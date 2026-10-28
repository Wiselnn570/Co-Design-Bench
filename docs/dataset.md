# Dataset

Co-Design Bench has two evaluation tracks: Multimodal Editing (ME) and Repository Editing (RE). The paper evaluates **273 tasks and 2,331 acceptance criteria**. The prepared public subset contains **96 ME tasks and 521 criteria**; RE tasks are not part of that subset.

| Scope | Tasks | Acceptance criteria |
| --- | ---: | ---: |
| Full ME evaluation track | 100 | 553 |
| Full RE evaluation track | 173 | 1,778 |
| Prepared public ME subset | 96 | 521 |

## Task inputs

Every ME task includes a normalized user request, a runnable pre-edit application, and an annotated screenshot identifying the region to edit. Some tasks also include audio, video, document, or image attachments. The request refers to these assets by their task-relative paths.

The primary attachment counts for the public subset are:

| Audio | Video | Document | Image | No extra attachment |
| ---: | ---: | ---: | ---: | ---: |
| 32 | 24 | 16 | 4 | 20 |

“No extra attachment” tasks still include the request, application, and annotated screenshot.

## Package layout

The prepared archives share this layout:

```text
cases/
└── <case_id>/
    ├── user_queries.json
    ├── project/
    │   ├── _attachments/   # when present
    │   ├── _annotations/   # task annotation assets
    │   └── ...             # application source
    └── rubric.json         # evaluation archive only
```

`user_queries.json` stores the request text. Preserve its asset references and the surrounding task files when preparing a solver workspace. The application source is under `project/`.

| Archive | Intended use |
| --- | --- |
| `solve_norubric.tar.gz` | Solver inputs: applications, requests, and assets, without acceptance criteria. |
| `eval_withrubric.tar.gz` | Evaluator inputs: the same tasks, with their original `rubric.json` files. |

These archives are **not included in this Git repository**, and a public download link is not yet documented here. Their filenames, sizes, and checksums are recorded in the [public release manifest](../data/public_release_manifest.json). The repository's [synthetic scoring example](../examples/README.md) can be run without them.

When you obtain the public archives, compare their SHA-256 checksums with the manifest:

```bash
sha256sum solve_norubric.tar.gz eval_withrubric.tar.gz
```

The full 273-task experiment uses archives with the same filenames but a different task population. Identify the public subset by its manifest and fixed case list.

Extract solver and evaluator inputs to separate directories:

```bash
mkdir -p work/solver-inputs work/evaluation-inputs
tar -xzf solve_norubric.tar.gz -C work/solver-inputs
tar -xzf eval_withrubric.tar.gz -C work/evaluation-inputs
```

Give the solver access to `work/solver-inputs/` only. Use `work/evaluation-inputs/` with `cdb prepare` after collecting the candidate applications.

## Fixed public scope

The [case list](../data/case_ids_me96.txt) records all 96 task IDs in their original order. The manifest records the 521 criteria and the attachment counts. Four tasks from the full 100-task ME track are outside this public subset.

Keep acceptance criteria hidden from the solver. Give the evaluator the task's fixed criteria and the candidate's final application. Do not generate new criteria when reporting scores on this subset.

## Interpreting results

The [README leaderboard](../README.md#leaderboard) reports the full **273-task** evaluation, including tasks outside the public subset. Scores obtained on the 96-task subset cover a different task population and should identify that scope explicitly.

See [evaluation](evaluation.md) for the judge-then-refute protocol and metric definitions.
