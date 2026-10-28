"""Prepare judge inputs from local dataset and submission directories."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import tempfile
from typing import Sequence


def _read_json(path: Path):
    """Read a required JSON file without including its contents in errors."""
    try:
        with path.open(encoding="utf-8") as stream:
            return json.load(stream)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Cannot read valid JSON from {path}") from error


def _require_directory(path: Path, label: str) -> None:
    if not path.is_dir():
        raise ValueError(f"Missing {label} directory: {path}")


def prepare_cases(
    dataset_root: str | Path,
    submissions_root: str | Path,
    out_dir: str | Path,
    case_ids: Sequence[str],
    expected_criterion_count: int | None = None,
) -> dict:
    """Write ``cases.json`` for selected tasks, preserving their supplied order.

    ``dataset_root`` contains ``cases/<id>/project/``, ``user_queries.json``
    and ``rubric.json``. Candidate applications are at
    ``submissions_root/<id>/``. The caller supplies the public case-ID whitelist
    or a validated subset. This function reads task JSON only; it does not
    execute applications, inspect environment files, or copy assets.

    Every output record uses the judge schema ``uuid/base/ws/query/rubrics``.
    ``query`` points to the original JSON file so its attachment context stays
    available to the judge. Input files remain unchanged. Validation finishes
    before the output directory is created.

    Raises ``ValueError`` for invalid tasks, missing submissions, duplicate IDs,
    or an output directory inside either input root.
    """
    if isinstance(case_ids, (str, bytes)):
        raise ValueError("case_ids must be a sequence of task IDs")
    try:
        selected = list(case_ids)
    except TypeError as error:
        raise ValueError("case_ids must be a sequence of task IDs") from error
    if not selected:
        raise ValueError("At least one case ID is required")
    if any(not isinstance(cid, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", cid)
           for cid in selected):
        raise ValueError("Case IDs must be nonempty directory names without path separators")
    if len(set(selected)) != len(selected):
        raise ValueError("Duplicate case IDs are not allowed")

    dataset_root = Path(dataset_root).resolve()
    submissions_root = Path(submissions_root).resolve()
    out_dir = Path(out_dir).resolve()
    _require_directory(dataset_root, "dataset")
    _require_directory(submissions_root, "submissions")
    if out_dir.is_relative_to(dataset_root) or out_dir.is_relative_to(submissions_root):
        raise ValueError("Output directory must be outside dataset and submissions roots")
    output_path = (out_dir / "cases.json").resolve()
    if output_path.parent != out_dir:
        raise ValueError("Output cases.json must not resolve outside the output directory")

    records = []
    criterion_count = 0
    for cid in selected:
        case_dir = (dataset_root / "cases" / cid).resolve()
        project = (case_dir / "project").resolve()
        submission = (submissions_root / cid).resolve()
        query_path = (case_dir / "user_queries.json").resolve()
        rubric_path = (case_dir / "rubric.json").resolve()
        _require_directory(case_dir, f"case {cid}")
        _require_directory(project, f"case {cid} starting project")
        _require_directory(submission, f"case {cid} submission")

        queries = _read_json(query_path)
        if not isinstance(queries, list) or not queries or any(
            not isinstance(row, dict)
            or not isinstance(row.get("text"), str)
            or not row["text"].strip()
            for row in queries
        ):
            raise ValueError(f"Case {cid}: user_queries must be a nonempty list of text records")

        rubric = _read_json(rubric_path)
        if not isinstance(rubric, dict) or rubric.get("uuid") != cid:
            raise ValueError(f"Case {cid}: rubric uuid must match the case ID")
        if "case_id" in rubric and rubric["case_id"] != cid:
            raise ValueError(f"Case {cid}: rubric case_id must match the case ID")
        if not isinstance(rubric.get("task_id"), str) or not rubric["task_id"].strip():
            raise ValueError(f"Case {cid}: rubric task_id must be a nonempty string")
        criteria = rubric.get("criteria")
        if not isinstance(criteria, list) or not criteria or any(
            not isinstance(item, str) or not item.strip() for item in criteria
        ):
            raise ValueError(f"Case {cid}: rubric criteria must be nonempty strings")
        total = rubric.get("total_points")
        if isinstance(total, bool) or not isinstance(total, int) or total != len(criteria):
            raise ValueError(f"Case {cid}: total_points must equal the number of criteria")

        records.append({
            "uuid": cid,
            "base": str(project),
            "ws": str(submission),
            "query": str(query_path),
            "rubrics": [{"req": criterion} for criterion in criteria],
        })
        criterion_count += len(criteria)

    if expected_criterion_count is not None and criterion_count != expected_criterion_count:
        raise ValueError(f"Expected {expected_criterion_count} criteria, found {criterion_count}")

    out_dir.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=out_dir, prefix=".cases-", suffix=".json", delete=False
        ) as stream:
            temporary_path = Path(stream.name).resolve()
            json.dump(records, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(temporary_path, output_path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

    return {
        "task_count": len(records),
        "criterion_count": criterion_count,
        "case_ids": selected,
        "cases_json": str(output_path),
    }
