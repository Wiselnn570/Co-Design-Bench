# Three tasks, three kinds of evidence

These are real **ME tasks in the prepared 96-case public subset**. The visual
comparison uses their starting applications and archived `qwen3.8-max-0902`
outputs. It illustrates concrete revisions, including an incomplete one; it is
not a collection of gold targets or a claim that every criterion passed.

![Real before/output comparisons, with archived browser footage for the title-animation task](assets/task-showcase.gif)

The GIF switches between real screenshots for the data-editing tasks. Its motion
section samples the archived output browser recording at its original playback
speed, visiting the three headings. It is not a recording of an agent executing
the task. A [static before/output comparison](assets/task-showcase.png) is also
available.

## Video reference → three existing headings

**Case `7d7953f8` · Video input · Actual output: `qwen3.8-max-0902`**

The user asks the agent to interpret three different effects in a short video
and map them to three marked headings on an existing page:

> “Reproduce video rows 1, 2 and 3 on headings ①, ② and ③ respectively. The three
> effects must be distinct, correctly matched to the video, and loop
> continuously. Keep the heading text unchanged; only add animation.”

The archived browser footage shows a moving highlight on the hero title, a
changing hue on “The Shoreline Routine,” and a staggered quotation effect. The
surrounding page remains recognizable in the before/output captures. A single
screenshot cannot establish timing, looping, or the exact match to the reference;
those require video and implementation evidence.

The still-image comparison crops the hero from the original full-page captures.
The GIF's output segment uses actual frames from the archived browser recording,
rather than animating a reconstructed page or inventing intermediate states.

## Image + spreadsheet → consistent click statistics

**Case `b0e36f34` · Image and spreadsheet input · Actual output: `qwen3.8-max-0902`**

An audit export and a photo of a printed bulletin supply evidence for correcting
several views of the same click counts:

> “Use this issue’s click audit in the attachments to correct the statistics
> inside the red circles. Don’t change the other links’ status or content.”

In the visible output, the weekly KPI changes from **847 to 939**, and the ranking
lists `/events` at **241**, followed by `/sermon` at 228, `/give` at 207, `/prayer`
at 174, and `/news` at 89. The page also retains the visible broken-link warning.

The revision is visibly incomplete: the main table still shows older click
numbers such as **1,687** and **1,286**, while the KPI and ranking use the revised
values. This is why a convincing dashboard screenshot alone cannot establish
cross-view consistency. The comparison shows the actual archived output,
including this discrepancy.

The displayed crops retain the KPI, main table, and ranking; they omit the
unrelated link-creation form near the bottom of the full-page capture.

## PDF receipt → dependent dashboard values

**Case `f725ea72` · PDF receipt input · Actual output: `qwen3.8-max-0902`**

The user requests a correction to one expense row and explicitly names the
dependent dashboard values that must follow it:

> “The attachment is the supplier’s actual receipt: correct row ① to the amount
> actually paid for the salt line. Afterwards the home page can’t keep the old
> numbers … Don’t touch any other expense row, and leave ‘average cost per coral’
> alone — we calculate that differently.”

The dashboard captures show spending changing from **$511.50 to $652.00** and
remaining budget from **$188.50 to $48.00**. The salt category changes from
**$68.00 / 13%** to **$208.50 / 32%**, and the other displayed chart shares change
with the total. The average cost per coral remains **$35.83** in both captures.

These images show the dashboard route. They do not show the corrected expense
row or the report's bottom totals, so those requirements need separate evidence.

## Where the visuals come from

[task-showcase-sources.json](assets/task-showcase-sources.json) records the public
case IDs, model, original requests, relative asset names, source hashes, and
crop boxes. All three IDs were checked against the repository's
[public whitelist](../data/case_ids_me96.txt).

[make_task_showcase.py](assets/make_task_showcase.py) composes the screenshot
cards and samples the existing MP4 with Pillow and ffmpeg. It executes no model
and launches no task application. The six original screenshot files, original
MP4, and minimal task metadata are included in
[showcase-sources/](assets/showcase-sources/). Rebuild from this repository's root:

```bash
python docs/assets/make_task_showcase.py
```

Use the [evaluation guide](evaluation.md) to evaluate fixed criteria. Visible
changes are useful evidence, but they do not replace the full judge and
verification record.
