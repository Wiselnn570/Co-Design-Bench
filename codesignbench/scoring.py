"""Score fixed benchmark criteria from final judge verdicts.

All reported completion scores are percentages. Each task receives equal weight
in the summary, regardless of its number of criteria.
"""

import json
from collections.abc import Mapping
from fractions import Fraction
from pathlib import Path


class ValidationError(ValueError):
    """A result cannot be scored against the fixed evaluation cases."""


def _final_record(record, context):
    if not isinstance(record, Mapping):
        raise ValidationError(f"{context}: expected a result object.")
    if record.get("type") == "result":
        field = "value" if "value" in record else "result"
        record = record.get(field)
        if not isinstance(record, Mapping):
            raise ValidationError(f"{context}: final result must contain an object in value or result.")
    return dict(record)


def _records(results):
    """Accept a result list, one result, or a UUID-keyed verify_results object."""
    if isinstance(results, list):
        return [_final_record(row, f"Result {index}") for index, row in enumerate(results, 1)]
    if not isinstance(results, Mapping):
        raise ValidationError("Results must be a list or a JSON object.")
    if "uuid" in results or results.get("type") == "result":
        return [_final_record(results, "Result")]
    records = []
    for uuid, value in results.items():
        row = _final_record(value, f"Result {uuid}")
        if "uuid" in row and row["uuid"] != uuid:
            raise ValidationError(f"Result {uuid}: UUID disagrees with its dictionary key.")
        row["uuid"] = uuid
        records.append(row)
    return records


def load_results(path):
    """Read final results from journal.jsonl or verify_results.json.

    Valid non-result journal events are ignored; malformed lines and malformed
    final result events are errors. Duplicate and missing task results are
    checked by :func:`score_results` against the fixed case list.
    """
    path = Path(path)
    try:
        if path.suffix.lower() == ".jsonl":
            records = []
            with path.open(encoding="utf-8") as stream:
                for number, line in enumerate(stream, 1):
                    if not line.strip():
                        continue
                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError as error:
                        raise ValidationError(f"{path.name}:{number}: invalid JSON.") from error
                    if not isinstance(event, Mapping):
                        raise ValidationError(f"{path.name}:{number}: journal event must be an object.")
                    if event.get("type") == "result":
                        records.append(_final_record(event, f"{path.name}:{number}"))
            return records
        with path.open(encoding="utf-8") as stream:
            return _records(json.load(stream))
    except json.JSONDecodeError as error:
        raise ValidationError(f"{path.name}: invalid JSON.") from error


def _case_criteria(cases):
    if not isinstance(cases, list) or not cases:
        raise ValidationError("Cases must be a nonempty fixed case list.")
    fixed = {}
    for index, case in enumerate(cases, 1):
        if not isinstance(case, Mapping):
            raise ValidationError(f"Case {index}: expected a case object.")
        uuid = case.get("uuid")
        if not isinstance(uuid, str) or not uuid.strip():
            raise ValidationError(f"Case {index}: UUID must be a nonempty string.")
        if uuid in fixed:
            raise ValidationError(f"Duplicate case UUID: {uuid}.")
        rubrics = case.get("rubrics")
        if not isinstance(rubrics, list) or not rubrics:
            raise ValidationError(f"Case {uuid}: rubrics must be a nonempty fixed criterion list.")
        criteria = []
        for number, rubric in enumerate(rubrics, 1):
            req = rubric.get("req") if isinstance(rubric, Mapping) else None
            if not isinstance(req, str) or not req.strip():
                raise ValidationError(f"Case {uuid}, criterion {number}: req must be a nonempty string.")
            criteria.append(req)
        fixed[uuid] = criteria
    return fixed


def score_results(cases, results):
    """Validate final criterion verdicts and compute task-averaged scores.

    ``cases`` is the fixed cases.json list with ``uuid`` and
    ``rubrics=[{"req": ...}]``. ``results`` may be a list of final results or
    a UUID-keyed verify_results object. Every task and every fixed criterion
    must appear exactly once, with criteria in their original order. Model
    totals, earned points, and completion percentages are never used.
    """
    fixed = _case_criteria(cases)
    by_uuid = {}
    for index, result in enumerate(_records(results), 1):
        uuid = result.get("uuid")
        if not isinstance(uuid, str) or not uuid.strip():
            raise ValidationError(f"Result {index}: UUID must be a nonempty string.")
        if uuid not in fixed:
            raise ValidationError(f"Result UUID is outside the fixed case list: {uuid}.")
        if uuid in by_uuid:
            raise ValidationError(f"Duplicate final result for case {uuid}.")
        by_uuid[uuid] = result
    missing = [uuid for uuid in fixed if uuid not in by_uuid]
    if missing:
        raise ValidationError("Missing final results for cases: " + ", ".join(missing) + ".")

    per_task = []
    strict_scores, graded_scores = [], []
    full_pass_count = 0
    for uuid, criteria in fixed.items():
        requirements = by_uuid[uuid].get("requirements")
        if not isinstance(requirements, list):
            raise ValidationError(f"Case {uuid}: requirements must be a list.")
        if len(requirements) != len(criteria):
            raise ValidationError(
                f"Case {uuid}: expected {len(criteria)} fixed criteria, got {len(requirements)}."
            )
        counts = {"PASS": 0, "PARTIAL": 0, "FAIL": 0}
        for number, (req, requirement) in enumerate(zip(criteria, requirements), 1):
            if not isinstance(requirement, Mapping):
                raise ValidationError(f"Case {uuid}, criterion {number}: expected a verdict object.")
            if requirement.get("req") != req:
                raise ValidationError(
                    f"Case {uuid}, criterion {number}: req differs from the fixed criterion or its order."
                )
            verdict = requirement.get("verdict")
            if not isinstance(verdict, str) or verdict not in counts:
                raise ValidationError(f"Case {uuid}, criterion {number}: unknown verdict {verdict!r}.")
            counts[verdict] += 1
        count = len(criteria)
        strict = Fraction(counts["PASS"], count)
        graded = Fraction(2 * counts["PASS"] + counts["PARTIAL"], 2 * count)
        full_pass = counts["PASS"] == count
        strict_scores.append(strict)
        graded_scores.append(graded)
        full_pass_count += full_pass
        per_task.append({
            "uuid": uuid,
            "criterion_count": count,
            "n_pass": counts["PASS"],
            "n_partial": counts["PARTIAL"],
            "n_fail": counts["FAIL"],
            "strict": float(strict * 100),
            "graded": float(graded * 100),
            "full_pass": full_pass,
        })
    task_count = len(fixed)
    return {
        "summary": {
            "task_count": task_count,
            "criterion_count": sum(len(criteria) for criteria in fixed.values()),
            "strict": float(sum(strict_scores) * 100 / task_count),
            "graded": float(sum(graded_scores) * 100 / task_count),
            "full_pass": float(Fraction(full_pass_count, task_count) * 100),
        },
        "per_task": per_task,
    }
