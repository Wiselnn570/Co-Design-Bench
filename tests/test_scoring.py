import json
import tempfile
import unittest
from pathlib import Path

from codesignbench.scoring import ValidationError, load_results, score_results


def case(uuid, criteria):
    return {
        "uuid": uuid, "base": "base", "ws": "workspace", "query": "query.txt",
        "rubrics": [{"req": criterion} for criterion in criteria],
    }


def result(uuid, verdicts):
    return {
        "uuid": uuid,
        "requirements": [
            {"req": req, "verdict": verdict, "evidence": "Observed in the application."}
            for req, verdict in verdicts
        ],
    }


class ScoringTests(unittest.TestCase):
    def test_macro_average_gives_each_task_equal_weight(self):
        criteria = [f"criterion {number}" for number in range(9)]
        cases = [case("short", ["one"]), case("long", criteria)]
        results = [result("long", [(req, "FAIL") for req in criteria]),
                   result("short", [("one", "PASS")])]
        report = score_results(cases, results)
        self.assertEqual(report["summary"], {
            "task_count": 2, "criterion_count": 10,
            "strict": 50.0, "graded": 50.0, "full_pass": 50.0,
        })
        self.assertEqual([row["uuid"] for row in report["per_task"]], ["short", "long"])

    def test_partial_credit_does_not_count_as_strict_or_full_pass(self):
        cases = [case("mixed", ["a", "b", "c"]), case("complete", ["d"])]
        results = [result("mixed", [("a", "PASS"), ("b", "PARTIAL"), ("c", "FAIL")]),
                   result("complete", [("d", "PASS")])]
        report = score_results(cases, results)
        self.assertAlmostEqual(report["summary"]["strict"], 200 / 3)
        self.assertEqual(report["summary"]["graded"], 75.0)
        self.assertEqual(report["summary"]["full_pass"], 50.0)
        self.assertFalse(report["per_task"][0]["full_pass"])
        self.assertEqual(report["per_task"][0]["n_partial"], 1)

    def test_model_reported_totals_cannot_inflate_scores(self):
        final = result("task", [("criterion", "FAIL")])
        final.update(total_points=1, earned_points=1000000, completion_pct=100)
        report = score_results([case("task", ["criterion"])], [final])
        self.assertEqual(report["summary"]["strict"], 0.0)
        self.assertEqual(report["summary"]["graded"], 0.0)
        self.assertEqual(report["summary"]["full_pass"], 0.0)

    def test_missing_duplicate_and_foreign_tasks_fail(self):
        cases = [case("a", ["one"]), case("b", ["two"])]
        first = result("a", [("one", "PASS")])
        second = result("b", [("two", "PASS")])
        invalid = [([first], "Missing final"), ([first, first, second], "Duplicate final"),
                   ([first, second, result("other", [("x", "PASS")])], "outside")]
        for results, message in invalid:
            with self.subTest(message=message), self.assertRaisesRegex(ValidationError, message):
                score_results(cases, results)

    def test_changed_reordered_missing_extra_and_unknown_criteria_fail(self):
        cases = [case("task", ["first", "second"])]
        variants = [
            [("changed", "PASS"), ("second", "PASS")],
            [("second", "PASS"), ("first", "PASS")],
            [("first", "PASS")],
            [("first", "PASS"), ("second", "PASS"), ("extra", "PASS")],
            [("first", "PASS"), ("second", "UNKNOWN")],
        ]
        for verdicts in variants:
            with self.subTest(verdicts=verdicts), self.assertRaises(ValidationError):
                score_results(cases, [result("task", verdicts)])

    def test_invalid_fixed_cases_fail(self):
        for cases in ([], [case("task", [])],
                      [case("task", ["one"]), case("task", ["one"])],
                      [case("task", [""])]):
            with self.subTest(cases=cases), self.assertRaises(ValidationError):
                score_results(cases, [])

    def test_loads_final_journal_events_and_uuid_keyed_json(self):
        final = result("task", [("one", "PASS")])
        cases = [case("task", ["one"])]
        with tempfile.TemporaryDirectory() as directory:
            journal = Path(directory) / "journal.jsonl"
            journal.write_text("\n".join(json.dumps(event) for event in [
                {"type": "message", "value": "intermediate event"},
                {"type": "result", "value": final},
            ]) + "\n", encoding="utf-8")
            self.assertEqual(score_results(cases, load_results(journal))["summary"]["strict"], 100.0)
            keyed = Path(directory) / "verify_results.json"
            keyed.write_text(json.dumps({"task": {"requirements": final["requirements"]}}), encoding="utf-8")
            self.assertEqual(score_results(cases, load_results(keyed))["summary"]["full_pass"], 100.0)
            with self.assertRaisesRegex(ValidationError, "dictionary key"):
                score_results(cases, {"other": final})

    def test_malformed_final_event_and_json_are_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = Path(directory) / "journal.jsonl"
            for content in ('{"type":"result","value":null}\n', 'not json\n'):
                journal.write_text(content, encoding="utf-8")
                with self.subTest(content=content), self.assertRaises(ValidationError):
                    load_results(journal)


if __name__ == "__main__":
    unittest.main()
