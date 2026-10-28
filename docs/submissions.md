# Prepare candidate applications

Use the solver archive without acceptance criteria to run your coding agent. Copy each task's initial application into a separate solver workspace, provide the full user request and its assets, and retain the final application source.

The public tools accept any agent harness. They do not call the internal platform used to run the paper experiments.

## Candidate layout

Place each candidate's final application under its original task ID:

```text
submissions/
├── <case_id_1>/
│   ├── index.html
│   └── ...
└── <case_id_2>/
    ├── package.json
    └── ...
```

Each `<case_id>/` is the final application root, rather than a parent containing another `project/` directory. Include its source, task assets, and dependency manifests.
Preserve paths used by the request and application, including `_attachments/`
and `_annotations/` when present. Keep rubrics and evaluator outputs outside the
solver workspace and final application.

## Bind inputs and criteria

Extract the evaluation archive to a directory separate from solver workspaces. Then run:

```bash
cdb prepare \
  --dataset /path/to/evaluation-inputs \
  --submissions /path/to/submissions \
  --out work/evaluation
```

The dataset root must contain `cases/<case_id>/project/`, `user_queries.json`, and `rubric.json`. The command checks all 96 public task IDs by default, requires a corresponding candidate for each, and writes `work/evaluation/cases.json`.
This command prepares the fixed 96-task public subset. It does not select the
full 273-task experiment from a larger archive.

For a smaller run, repeat `--case` with public IDs:

```bash
cdb prepare \
  --dataset /path/to/evaluation-inputs \
  --submissions /path/to/submissions \
  --out work/one-task \
  --case 7d7953f8
```

The command preserves the public case-list order. It checks rubric identity and criterion counts, keeps criterion text unchanged, and references the original request JSON and project paths. It does not copy large applications or run them. Keep its output outside both input directories.

The resulting `cases.json` uses absolute local paths:

```json
[
  {
    "uuid": "<case_id>",
    "base": "/absolute/path/to/cases/<case_id>/project",
    "ws": "/absolute/path/to/submissions/<case_id>",
    "query": "/absolute/path/to/cases/<case_id>/user_queries.json",
    "rubrics": [{"req": "<original acceptance criterion>"}]
  }
]
```

Keep the evaluation inputs and submissions at those paths while judging and
scoring. If you move them or transfer a run to another machine, run `cdb prepare`
again to create paths for that environment. The candidate applications are
ordinary source directories; `cases.json` is the local evaluator's input manifest.

See [evaluation](evaluation.md) to run the reference judge or score final verdicts from another evaluator.
