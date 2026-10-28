# Evaluation

Co-Design Bench evaluates the final application against fixed, expert-authored acceptance criteria. The solver receives the user request and initial application; the criteria are reserved for evaluation. The protocol uses source and browser evidence without requiring gold code or a target screenshot.

![Evaluation pipeline](assets/evaluation-pipeline.png)

## Judge, then refute

1. **Build and launch.** Run the candidate's final application in an isolated evaluation environment. Retain the initial application for comparison.
2. **Gather evidence.** Inspect source changes, screenshots, and browser interactions for each criterion. Visual or interaction claims require evidence from the running application.
3. **Judge.** A primary evaluator assigns each fixed criterion `PASS`, `PARTIAL`, or `FAIL`, with evidence supporting the verdict.
4. **Refute.** A separate verifier challenges positive verdicts, including stubs, hardcoded outputs, unreachable functionality, and requirement mismatches. Audit required evidence before aggregating the final verdicts.

Build failures, unavailable functionality, or missing evidence must remain visible in the evaluation record. The initial application helps distinguish requested changes from behavior that already existed.

## Metrics

For a task with `n` criteria and final verified verdicts:

```text
Strict completion   R = #PASS / n
Graded completion   G = (#PASS + 0.5 × #PARTIAL) / n
Full task pass      I = 1 if every criterion is PASS, otherwise 0
```

For a set of tasks, average `R`, `G`, and `I` with **equal weight per task**. Report the averages as percentages. A task with more criteria receives the same weight as a task with fewer criteria; pooling all criteria across tasks gives a different statistic.

For example, a task with `PASS`, `PARTIAL`, and `FAIL` has strict completion `33.3%`, graded completion `50.0%`, and does not fully pass. A task whose criteria are all `PASS` has `100%` strict and graded completion and fully passes.

## Result scope

The paper compares ten model endpoints using one shared agentic harness over **100 ME and 173 RE tasks**. Overall scores average all 273 tasks; per-track scores average tasks within that track.

The prepared public subset contains **96 ME tasks and 521 criteria**. Report evaluations on that subset separately from the paper's full-set results. Keep the original task IDs, criterion text, criterion order, and criterion counts fixed.

## Original experiment configuration

The [original protocol reference](../evaluation/README.md) and [machine-readable configuration](../evaluation/protocol.json) document the reviewed `codesign-unified` solve → evaluate flow, source revisions, and budgets. The supplied launch configuration uses two concurrent jobs, one case per job, with 43,200-second solve and evaluation budgets and a 90,000-second job runtime. The inspected job also has a 45,000-second enclosing solve stage and 7,200-second individual judge call timeouts.

That reference configuration uses mandatory headless Chrome rendering before judging. Its `judge_browser_enabled=false` setting disables the optional live interaction browser during judging; screenshot and DOM collection still run. The public runner below uses live Playwright evidence in both stages and requires both stages to succeed. See the protocol reference for the original runtime adapters, recovery behavior, and other differences.

## Public reference runner

The `cdb judge` command is adapted from the project's existing Claude/Playwright judge. It uses an authenticated Claude CLI for a primary evaluation and a separate refutation call. It does not depend on the internal job platform or model-routing infrastructure.

Install Playwright in the directory from which you invoke the command:

```bash
npm install --no-save playwright
npx playwright install chromium
```

Then evaluate prepared cases and score their final verdicts:

```bash
cdb judge --cases work/evaluation/cases.json --out results/run-1 --model opus
cdb score --cases work/evaluation/cases.json --results results/run-1/journal.jsonl --out results/run-1/scores.json
```

Set `--model` to a model name accepted by your configured Claude CLI. Use `--claude-bin` for a non-default executable, `--concurrency` to evaluate multiple tasks, and `--timeout` for the stage and build timeout in seconds. The output directory must be outside the input applications. Use a new output directory for each run.

The runner copies the baseline and candidate sources before installing dependencies or building. Static applications with a root `index.html` are served directly. Applications with an npm `build` script are installed and built, then served from `dist/`, `build/`, or `out/` containing `index.html`. Server-rendered applications, backend services, and custom build tools need a separate runtime adapter.

Application builds and Claude's permitted tools execute local commands. Run them inside a disposable container or VM configured for evaluation. Source copies protect the original files; they do not provide a security sandbox.

Each stage saves its response and artifacts separately. Positive verdicts require nonempty evidence. Browser credit also requires a running candidate application and evidence files in that stage's artifact directory. The verifier can retain or downgrade a verdict; it cannot increase credit. A failed stage is recorded as an error, and the command exits unsuccessfully if any task lacks a final verified result.

```text
results/run-1/
├── journal.jsonl
├── applications/<case_id>/
│   ├── base/
│   └── ws/
└── artifacts/<case_id>/
    ├── judge/
    └── refute/
```

This runner supplies a portable starting point for evaluation. File-existence checks do not establish that a screenshot or browser assertion is semantically sufficient. The paper's complete experiment infrastructure, dedicated rendering adapters, and additional evidence audits are not reproduced by this command; running it does not reproduce the published leaderboard automatically.

## Score an existing evaluator's results

`cdb score` can also consume final verdicts from another evaluator. Pass the same fixed `cases.json` and either a result JSON or final-result journal. A result must use each task's original `uuid` and exactly one entry per criterion, preserving its text and order:

```json
{
  "uuid": "<case_id>",
  "requirements": [
    {"req": "<original acceptance criterion>", "verdict": "PASS", "evidence": "<observed evidence>"}
  ]
}
```

JSON inputs can be a list of these objects or an object keyed by task ID. A journal's final records use `{"type": "result", "value": <result object>}`. The scorer rejects missing or duplicate tasks, changed criteria, and unknown verdict labels. It recomputes all scores from the final verdicts and ignores model-provided totals or percentages. The JSON report includes aggregate percentages and per-task scores.

See the [paper](Co-Design-Bench.pdf) for the full methodology and the [dataset documentation](dataset.md) for the task package format.
