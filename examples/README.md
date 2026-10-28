# Scoring example

These two synthetic tasks demonstrate the result format and task-weighted scoring. They are not Co-Design Bench tasks and do not contain runnable applications.

From the repository root:

```bash
python -m codesignbench score \
  --cases examples/cases.json \
  --results examples/final_verdicts.json
```

Expected scores: Strict **66.67%**, Graded **75.0%**, Full pass **50.0%**. The first task has one criterion, the second has three. Each task receives equal weight.

For actual evaluation, generate a separate `cases.json` from the fixed public task inputs and your candidate workspaces using `cdb prepare`. See the [submission guide](../docs/submissions.md).
