# Original experiment protocol

[protocol.json](protocol.json) records the original `codesign-unified` configuration
and the evaluation tools reviewed for this release. It contains model identifiers,
budgets, evidence settings, source revisions, and source-file checksums. It is a
protocol reference; it is not an executable platform submission configuration.

The full experiment contains **100 ME + 173 RE = 273 cases**, with one case per job.
Each job first solves the task using the request, initial application, and assets,
then evaluates the final workspace against the separately supplied expert rubric.
The prepared public data contains **96 ME cases and 521 criteria**. The full-set
input archives and RE tasks are not part of this release.

## Budgets and configuration

The supplied launch configuration requests one submission combination, no skipped
models, and **two concurrent jobs**. The reference job was inspected read-only.
The launch concurrency is recorded as a requested setting, rather than asserted
as the current state of the remote group.

| Setting | Supplied launch value | Inspected reference job |
| --- | ---: | ---: |
| Solve allowance | 43,200 s | 43,200 s |
| Enclosing solve stage | — | 45,000 s |
| Evaluation budget | 43,200 s | 43,200 s |
| Whole-job runtime | 90,000 s | 90,000 s |
| Individual primary/verifier call timeout | — | 7,200 s |
| Maximum attempts per judge call | — | 2 |
| Extra render retries after timeout | — | 2 |

These timeouts apply at different levels. The enclosing solve stage includes time
around the solver; an individual judge call remains bounded by the overall
evaluation and job budgets. A render attempt starts at 420 seconds, with a 1.5
timeout multiplier on retries. Build failures are not retried as render timeouts.

The inspected evaluator model is `mr.claude-opus-4-8`, with reasoning effort `low`.
This identifier belongs to the original routing configuration. For `cdb judge`,
choose a model identifier accepted by your own authenticated Claude CLI.

## Evidence and adjudication

The matching tools identify themselves with tools revision
`063fc71ef0f5033d22f09fc913a2bae819a28a11`. The reference job uses template revision
`6207e81d03194ca669662dc4e403c7abc4bacb00`. The following flow was checked against
the matching tool source, rather than inferred from the portable runner:

1. Normalize the task and solver workspace, and load the fixed human rubric.
2. Copy the candidate into an evaluator scratch workspace and render it **before
   judging**. Save a screenshot, DOM, body text, render status, and command log.
   The original runtime adapter applies evaluation-only build repairs on scratch
   copies, including entry-point wiring and dependency stubs for certain projects.
3. Inject the render record into the primary evaluator's prompt. Rendering
   failures and missing DOM prohibit `PASS` on render-dependent requirements.
   Fewer than five body words flag a suspected empty page. Visual claims must
   cite real render evidence.
4. Judge each fixed criterion as `PASS`, `PARTIAL`, or `FAIL`. Preserve the
   criterion text, order, and denominator. Inspect implementation reachability
   and compare requested behavior against the initial application.
5. Ask an adversarial verifier to challenge positive verdicts. Its prompt repeats
   the fixed rubric and checks disconnected code, stubs, hardcoded data, and
   whether changing the input data would change the claimed behavior.
6. Audit visual claims and aggregate the results. The original pipeline can also
   investigate low-score cases using baseline rendering and solvability
   attribution, then retain source and screenshot records for review.

**`judge_browser_enabled=false` does not disable browser rendering.** It disables
the optional live Playwright MCP interaction session during judging. In this
reference configuration, judges inspect mandatory pre-rendered screenshot/DOM
evidence plus source reachability; they must not claim interactions they did not
perform. The optional browser viewport is configured as 1440 × 900. The inspected
headless Chrome renderer separately defaults to 1440 × 1600 screenshots.

The original tool's handling of incomplete evaluations also differs from the
public runner: a failed verifier can fall back to the primary result, and an
outer timeout can recover a saved primary result. These records must not be
described as successfully verified second-stage results. Synthetic failure
records exist for diagnostics, and the original configuration rejects runs with
no valid judge journal.

The platform's `pass_score_threshold=0.75` controls a job-level status flag. It is
separate from the benchmark's **full task pass**, which requires every fixed
criterion to receive `PASS`.

## Source locations

The filenames below locate the reviewed logic inside the original evaluation
tools. Their exact source-file SHA-256 checksums are in [protocol.json](protocol.json).

| Original filename | Reviewed responsibility |
| --- | --- |
| `reflow_modeb_eval_after_solve.sh` | Evaluation orchestration and budget/recovery handling |
| `reflow_render_judge_cases.py` | Mandatory candidate render and evidence record |
| `reflow_render_case_eval.sh` | Runtime adapter operating on scratch copies |
| `judge_cli.py` | Primary and adversarial verifier templates |
| `reflow_patch_judge_cli_render_guard.py` | Runtime injection of render and browser rules |
| `reflow_guard_visual_evidence.py` | Audit unsupported visual-evidence claims |

These source identities provide traceability. The original visual-claim audit
script is included as [guard_visual_evidence.py](guard_visual_evidence.py), with
byte-identical contents and its source checksum recorded in the protocol. The
full original tools bundle is not included in this repository. Credentials, private storage locations,
platform scheduling identifiers, and model-routing infrastructure are not
required by the public runner.

## Run the original visual-claim audit

From the repository root, this command checks two synthetic records:

```bash
python evaluation/guard_visual_evidence.py \
  --journal evaluation/examples/journal.jsonl \
  --render-json evaluation/examples/render_status.json \
  --out visual_claim_audit.json \
  --fail-on-violation
```

The example exits successfully and writes `{"violations": []}`. Its task IDs,
render statuses, and paths are synthetic; the example does not render an
application or create the named DOM file.

The script consumes the original pipeline's result journal and a JSON object
keyed by task UUID, whose records include `status`, `process_rc`, `render_rc`,
`body_words`, and `dom_path`. When rendering failed or required render metadata
is missing, it flags phrases such as “screenshot confirms” in the evaluator's
evidence or notes. `--fail-on-violation` makes detected violations exit with
status 2. For real runs, supply render metadata produced by your runtime adapter.

This is a phrase-matching audit, not a semantic judge. It does not create render
records, check that cited files exist, validate successful screenshots, or
establish that a criterion was satisfied. The public `cdb judge` command has its
own artifact validation and does not automatically produce the original
render-record format.

## Public reference implementation

[`codesignbench/judge.py`](../codesignbench/judge.py) implements the portable
`cdb judge` command. See the [evaluation guide](../docs/evaluation.md) for setup
and output format.

| Area | Inspected original configuration | Public `cdb judge` |
| --- | --- | --- |
| Application runtime | Dedicated render adapters and evaluator scratch repairs | Static HTML and supported npm build outputs |
| Evidence | Mandatory pre-rendered Chrome screenshot/DOM; optional interaction browser disabled | Live Playwright checks with saved evidence in each stage |
| Rubric | Fixed expert-authored criteria, repeated in both prompts | Fixed criteria, with exact task/text/order validation |
| Incomplete verification | May recover or retain a primary result | Requires both stages to succeed |
| Verifier credit | Prompt instructs verifier to challenge and downgrade | Also rejects increases programmatically |
| Additional attribution | Baseline and low-score solvability analysis | Final fixed-criterion scoring |

The public command provides a runnable starting point for released tasks. It
does not reproduce the original runtime adapters, routing, recovery behavior,
or full 273-case experiment, and its results do not automatically reproduce the
published leaderboard. Keep the evaluated task population and configuration
with every reported result.
