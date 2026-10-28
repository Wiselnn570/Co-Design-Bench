import io
import json
import subprocess
import tempfile
import unittest
from contextlib import contextmanager, redirect_stderr
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from codesignbench.judge import (
    _extract_result, _judge_case, _serve, _validate_stage, run_judge,
)


def make_case(root):
    for directory in ("baseline", "candidate"):
        project = root / directory
        project.mkdir()
        (project / "index.html").write_text("<html><body>Application</body></html>", encoding="utf-8")
    query = root / "user_queries.json"
    query.write_text('[{"text": "Implement the criterion."}]', encoding="utf-8")
    return {
        "uuid": "task", "base": str(root / "baseline"), "ws": str(root / "candidate"),
        "query": str(query), "rubrics": [{"req": "Implement the criterion."}],
    }


def verdict(value, method="static", evidence_files=None):
    requirement = {
        "req": "Implement the criterion.", "verdict": value,
        "verification_method": method, "evidence": "Observed the relevant behavior.",
    }
    if evidence_files is not None:
        requirement["evidence_files"] = evidence_files
    return {"uuid": "task", "requirements": [requirement]}


@contextmanager
def served_app(*_):
    yield {"url": "http://127.0.0.1:12345", "error": None}


class JudgeTests(unittest.TestCase):
    def test_refute_failure_produces_error_and_never_a_final_result(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            case = make_case(root)
            output = root / "evaluation"
            node = subprocess.CompletedProcess(["node"], 0, stdout="/test/playwright/index.js\n", stderr="")
            with patch("codesignbench.judge.shutil.which", return_value="/test/claude"), \
                    patch("codesignbench.judge.subprocess.run", return_value=node), \
                    patch("codesignbench.judge._serve", side_effect=served_app), \
                    patch("codesignbench.judge._invoke", side_effect=[verdict("PASS"), RuntimeError("refute failed")]) as invoke, \
                    redirect_stderr(io.StringIO()):
                completed = run_judge([case], output, "test-model")
            self.assertFalse(completed)
            self.assertEqual(invoke.call_count, 2)
            events = [json.loads(line) for line in (output / "journal.jsonl").read_text().splitlines()]
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0]["type"], "error")
            self.assertEqual(events[0]["uuid"], "task")
            self.assertIn("refute failed", events[0]["error"])
            self.assertTrue((output / "artifacts/task/judge/judge.json").is_file())
            self.assertFalse((output / "artifacts/task/refute/verified.json").exists())

    def test_refuter_cannot_upgrade_any_initial_verdict(self):
        for initial, increased in (("FAIL", "PARTIAL"), ("PARTIAL", "PASS")):
            with self.subTest(initial=initial, increased=increased), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                case = make_case(root)
                with patch("codesignbench.judge._serve", side_effect=served_app), \
                        patch("codesignbench.judge._invoke", side_effect=[verdict(initial), verdict(increased)]), \
                        self.assertRaisesRegex(ValueError, "increase"):
                    _judge_case(case, root / "evaluation", "test-model", "claude", 10, "/test/playwright")
                self.assertFalse((root / "evaluation/artifacts/task/refute/verified.json").exists())

    def test_refuter_can_remove_credit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            case = make_case(root)
            with patch("codesignbench.judge._serve", side_effect=served_app), \
                    patch("codesignbench.judge._invoke", side_effect=[verdict("PASS"), verdict("FAIL")]):
                final = _judge_case(case, root / "evaluation", "test-model", "claude", 10, "/test/playwright")
            self.assertEqual(final["requirements"][0]["verdict"], "FAIL")
            self.assertTrue((root / "evaluation/artifacts/task/refute/verified.json").is_file())

    def test_application_preparation_uses_copies_and_preserves_original_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            case = make_case(root)
            original = {key: (Path(case[key]) / "index.html").read_bytes() for key in ("base", "ws")}
            served_paths = []

            @contextmanager
            def simulate_build(project, _timeout):
                project = Path(project)
                served_paths.append(project)
                (project / "index.html").write_text("Generated application output", encoding="utf-8")
                (project / "generated.log").write_text("Build completed", encoding="utf-8")
                yield {"url": "http://127.0.0.1:12345", "error": None}

            with patch("codesignbench.judge._serve", side_effect=simulate_build), \
                    patch("codesignbench.judge._invoke", side_effect=[verdict("FAIL"), verdict("FAIL")]):
                _judge_case(case, root / "evaluation", "test-model", "claude", 10, "/test/playwright")
            expected = root / "evaluation/applications/task"
            self.assertEqual(set(served_paths), {expected / "base", expected / "ws"})
            for key in ("base", "ws"):
                self.assertEqual((Path(case[key]) / "index.html").read_bytes(), original[key])
                self.assertFalse((Path(case[key]) / "generated.log").exists())

    def test_successful_build_cannot_reuse_old_export_as_candidate_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            case = make_case(root)
            for key in ("base", "ws"):
                project = Path(case[key])
                (project / "index.html").unlink()
                (project / "package.json").write_text(
                    '{"scripts":{"build":"true"}}', encoding="utf-8")
                (project / "out").mkdir()
                (project / "out/index.html").write_text("Old export", encoding="utf-8")

            def invoke(_prompt, artifacts, _stage, *_):
                (Path(artifacts) / "check.json").write_text('{"passed":true}', encoding="utf-8")
                return verdict("PASS", "playwright", ["check.json"])

            build = subprocess.CompletedProcess(["npm"], 0, stdout=b"", stderr=b"")
            output = root / "evaluation"
            with patch("codesignbench.judge.subprocess.run", return_value=build), \
                    patch("codesignbench.judge._invoke", side_effect=invoke), \
                    self.assertRaisesRegex(ValueError, "could not run"):
                _judge_case(case, output, "test-model", "claude", 10, "/test/playwright")
            for key in ("base", "ws"):
                self.assertFalse((output / "applications/task" / key / "out").exists())
                self.assertEqual((Path(case[key]) / "out/index.html").read_text(), "Old export")

    def test_refuter_cannot_reuse_primary_artifact_as_its_own_evidence(self):
        for refute_file in ("browser-check.json", "../judge/browser-check.json"):
            with self.subTest(path=refute_file), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                case = make_case(root)

                def invoke(_prompt, artifacts, stage, *_):
                    if stage == "judge":
                        (Path(artifacts) / "browser-check.json").write_text('{"passed":true}', encoding="utf-8")
                    filename = "browser-check.json" if stage == "judge" else refute_file
                    return verdict("PASS", "playwright", [filename])

                with patch("codesignbench.judge._serve", side_effect=served_app), \
                        patch("codesignbench.judge._invoke", side_effect=invoke), \
                        self.assertRaisesRegex(ValueError, "invalid browser evidence"):
                    _judge_case(case, root / "evaluation", "test-model", "claude", 10, "/test/playwright")
                self.assertFalse((root / "evaluation/artifacts/task/refute/verified.json").exists())

    def test_json_parser_handles_braces_and_escaped_quotes_in_strings(self):
        expected = verdict("PASS")
        expected["requirements"][0]["evidence"] = 'A string with } then {, an escaped "quote", and </RESULT> text.'
        response = "Preamble {not JSON}.\n<RESULT>\n" + json.dumps(expected) + "\n</RESULT>\n"
        self.assertEqual(_extract_result(response), expected)
        self.assertEqual(_extract_result("```json\n" + json.dumps(expected) + "\n```"), expected)

    def test_browser_credit_requires_real_nonempty_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            case = make_case(root)
            artifacts = root / "artifacts"
            artifacts.mkdir()
            (artifacts / "check.json").write_text('{"assertion": true}', encoding="utf-8")
            (artifacts / "empty.json").touch()
            (artifacts / "folder").mkdir()
            for value in ("PASS", "PARTIAL"):
                with self.subTest(verdict=value):
                    _validate_stage(case, verdict(value, "playwright", ["check.json"]), artifacts)
                for paths in (None, [], ["missing.png"], ["empty.json"], ["folder"], [123]):
                    with self.subTest(verdict=value, paths=paths), self.assertRaises(ValueError):
                        _validate_stage(case, verdict(value, "playwright", paths), artifacts)

    def test_browser_artifact_paths_cannot_escape_evidence_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            case = make_case(root)
            artifacts = root / "artifacts"
            artifacts.mkdir()
            outside = root / "outside.json"
            outside.write_text('{"assertion": true}', encoding="utf-8")
            (artifacts / "external.json").symlink_to(outside)
            for name in ("../outside.json", str(outside), "external.json"):
                with self.subTest(path=name), self.assertRaisesRegex(ValueError, "invalid browser evidence"):
                    _validate_stage(case, verdict("PASS", "playwright", [name]), artifacts)

    def test_browser_credit_is_rejected_when_candidate_could_not_run(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            case = make_case(root)
            (root / "check.json").write_text('{"passed":true}', encoding="utf-8")
            for value in ("PASS", "PARTIAL"):
                with self.subTest(verdict=value), self.assertRaisesRegex(ValueError, "could not run"):
                    _validate_stage(case, verdict(value, "playwright", ["check.json"]), root,
                                    runtime_available=False)

    def test_local_server_supports_spa_routes_and_returns_404_for_missing_assets(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            markup = "<html><body>SPA route rendered</body></html>"
            (project / "index.html").write_text(markup, encoding="utf-8")
            with _serve(project, 10) as runtime:
                self.assertIsNone(runtime["error"])
                with urlopen(runtime["url"] + "/settings/profile?tab=details", timeout=5) as response:
                    self.assertEqual(response.status, 200)
                    self.assertEqual(response.read().decode(), markup)
                with urlopen(runtime["url"] + "/users/alice.smith", timeout=5) as response:
                    self.assertEqual(response.status, 200)
                    self.assertEqual(response.read().decode(), markup)
                with self.assertRaises(HTTPError) as error:
                    urlopen(runtime["url"] + "/assets/missing.js", timeout=5)
                self.assertEqual(error.exception.code, 404)
                image_request = Request(runtime["url"] + "/assets/missing", headers={"Sec-Fetch-Dest": "image"})
                with self.assertRaises(HTTPError) as error:
                    urlopen(image_request, timeout=5)
                self.assertEqual(error.exception.code, 404)


if __name__ == "__main__":
    unittest.main()
