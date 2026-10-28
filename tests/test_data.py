"""Tests for preparing local judge inputs without running applications."""

import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from codesignbench.data import prepare_cases


class PrepareCasesTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.dataset = self.root / "dataset"
        self.submissions = self.root / "submissions"
        self.output = self.root / "prepared"
        self.ids = ["00000001", "00000002"]
        for index, cid in enumerate(self.ids):
            case = self.dataset / "cases" / cid
            (case / "project").mkdir(parents=True)
            (case / "project" / "index.html").write_text("<h1>Example</h1>")
            (case / "user_queries.json").write_text(json.dumps([
                {"text": "Update this synthetic example.", "attachments": ["project/reference.png"]}
            ]))
            (case / "rubric.json").write_text(json.dumps({
                "uuid": cid,
                "task_id": f"example-{cid}",
                "total_points": index + 1,
                "criteria": ["Keep the heading."] + (["Show a button."] if index else []),
            }))
            (self.submissions / cid).mkdir(parents=True)
            (self.submissions / cid / "index.html").write_text("<h1>Candidate</h1>")
            # This file must never be read, parsed, or copied by preparation.
            (self.submissions / cid / ".env").write_bytes(b"\xff\xfe\x00")

    def prepare(self, ids=None):
        return prepare_cases(self.dataset, self.submissions, self.output, self.ids if ids is None else ids)

    def change_rubric(self, **changes):
        path = self.dataset / "cases" / self.ids[0] / "rubric.json"
        data = json.loads(path.read_text())
        data.update(changes)
        path.write_text(json.dumps(data))

    def test_valid_preparation_preserves_inputs_and_original_query_paths(self):
        before = {p: p.read_bytes() for folder in (self.dataset, self.submissions)
                  for p in folder.rglob("*") if p.is_file()}
        result = self.prepare()
        records = json.loads(Path(result["cases_json"]).read_text())
        self.assertEqual(result["task_count"], 2)
        self.assertEqual(result["criterion_count"], 3)
        self.assertEqual(result["case_ids"], self.ids)
        self.assertEqual(set(records[0]), {"uuid", "base", "ws", "query", "rubrics"})
        for cid, record in zip(self.ids, records):
            case = self.dataset / "cases" / cid
            self.assertEqual(record["uuid"], cid)
            self.assertEqual(record["base"], str((case / "project").resolve()))
            self.assertEqual(record["ws"], str((self.submissions / cid).resolve()))
            self.assertEqual(record["query"], str((case / "user_queries.json").resolve()))
            rubric = json.loads((case / "rubric.json").read_text())
            self.assertEqual(record["rubrics"], [{"req": value} for value in rubric["criteria"]])
        self.assertEqual(before, {p: p.read_bytes() for p in before})
        self.assertEqual([p.name for p in self.output.iterdir()], ["cases.json"])

    def test_supplied_order_and_subset_are_preserved(self):
        self.prepare(list(reversed(self.ids)))
        records = json.loads((self.output / "cases.json").read_text())
        self.assertEqual([row["uuid"] for row in records], list(reversed(self.ids)))
        result = self.prepare([self.ids[1]])
        self.assertEqual(result["task_count"], 1)
        self.assertEqual(result["criterion_count"], 2)

    def test_expected_public_criterion_count_is_checked_before_writing(self):
        with self.assertRaisesRegex(ValueError, "Expected 521 criteria, found 3"):
            prepare_cases(self.dataset, self.submissions, self.output, self.ids,
                          expected_criterion_count=521)
        self.assertFalse(self.output.exists())

    def test_missing_rubric_is_rejected_before_writing(self):
        (self.dataset / "cases" / self.ids[1] / "rubric.json").unlink()
        with self.assertRaisesRegex(ValueError, "Cannot read valid JSON"):
            self.prepare()
        self.assertFalse(self.output.exists())

    def test_missing_submission_is_rejected(self):
        with tempfile.TemporaryDirectory() as empty:
            with self.assertRaisesRegex(ValueError, "submission directory"):
                prepare_cases(self.dataset, empty, self.output, self.ids)
        self.assertFalse(self.output.exists())

    def test_missing_starting_project_is_rejected(self):
        case = self.dataset / "cases" / self.ids[0]
        (case / "project" / "index.html").unlink()
        (case / "project").rmdir()
        with self.assertRaisesRegex(ValueError, "starting project"):
            self.prepare()

    def test_invalid_criteria_are_rejected(self):
        for criteria in ([], [""], ["  "], [123], [{"req": "Keep the heading."}], "criterion"):
            with self.subTest(criteria=criteria):
                self.change_rubric(criteria=criteria)
                with self.assertRaisesRegex(ValueError, "criteria"):
                    self.prepare()
        self.assertFalse(self.output.exists())

    def test_rubric_identity_and_count_are_validated(self):
        self.change_rubric(uuid="00000099")
        with self.assertRaisesRegex(ValueError, "uuid"):
            self.prepare()
        self.change_rubric(uuid=self.ids[0], total_points=2)
        with self.assertRaisesRegex(ValueError, "total_points"):
            self.prepare()
        self.change_rubric(total_points=True)
        with self.assertRaisesRegex(ValueError, "total_points"):
            self.prepare()

    def test_invalid_queries_are_rejected(self):
        path = self.dataset / "cases" / self.ids[0] / "user_queries.json"
        for queries in ([], {}, [{}], [{"text": ""}], [{"text": 1}]):
            with self.subTest(queries=queries):
                path.write_text(json.dumps(queries))
                with self.assertRaisesRegex(ValueError, "text records"):
                    self.prepare()

    def test_duplicate_empty_and_path_ids_are_rejected(self):
        for ids in ([self.ids[0], self.ids[0]], [], ["../other"], "00000001"):
            with self.subTest(ids=ids):
                with self.assertRaises(ValueError):
                    self.prepare(ids)

    def test_output_cannot_modify_input_directories(self):
        for output in (self.dataset / "prepared", self.submissions / self.ids[0]):
            with self.subTest(output=output):
                with self.assertRaisesRegex(ValueError, "outside dataset and submissions"):
                    prepare_cases(self.dataset, self.submissions, output, self.ids)

    def test_output_symlink_cannot_overwrite_input(self):
        self.output.mkdir()
        query = self.dataset / "cases" / self.ids[0] / "user_queries.json"
        original = query.read_bytes()
        (self.output / "cases.json").symlink_to(query)
        with self.assertRaisesRegex(ValueError, "outside the output directory"):
            self.prepare()
        self.assertEqual(query.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
