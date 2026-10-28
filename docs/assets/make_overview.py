"""Render the README overview as a standalone SVG and a 2x PNG.

Run: python3 CoDesignBench/docs/assets/make_overview.py
Counts describe the paper's full evaluation set (tables/dataset_stats.tex).
The public release contains 96 of the 100 Multimodal Editing tasks.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, PathPatch
from matplotlib.path import Path as MplPath


OUT = Path(__file__).resolve().parent
INK = "#232326"
MUTED = "#5F6571"
BLUE = "#244BB2"
BLUE_PALE = "#F0F4FC"
GOLD = "#89602A"
GOLD_PALE = "#FAF5EB"
LINE = "#DCE1EA"
GREEN = "#426C4B"
ROSE = "#9B5760"

plt.rcParams.update({"font.family": "DejaVu Sans", "svg.fonttype": "path"})
fig, ax = plt.subplots(figsize=(16, 8.6), dpi=100)
fig.subplots_adjust(0, 0, 1, 1)
ax.set(xlim=(0, 1600), ylim=(860, 0))
ax.axis("off")


def text(x, y, value, size=26, color=INK, weight="normal", align="left"):
    return ax.text(
        x, y, value, fontsize=size * 0.72, color=color, weight=weight,
        ha=align, va="top", linespacing=1.4,
    )


def box(x, y, w, h, fill="white", stroke=LINE, radius=14, lw=1.2):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        facecolor=fill, edgecolor=stroke, linewidth=lw,
    ))


def line(x1, y1, x2, y2, color=LINE, lw=1.6):
    ax.plot([x1, x2], [y1, y2], color=color, lw=lw, solid_capstyle="round")


def arrow(x1, y1, x2, y2, color=BLUE, lw=1.8, size=15):
    ax.add_patch(FancyArrowPatch(
        (x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=size,
        color=color, linewidth=lw, shrinkA=0, shrinkB=0,
    ))


def browser_icon(x, y, color=BLUE):
    box(x, y, 31, 27, fill="none", stroke=color, radius=4, lw=1.5)
    line(x, y + 8, x + 31, y + 8, color, 1.2)
    for dx in [5, 10, 15]:
        ax.add_patch(Circle((x + dx, y + 4), 1.1, color=color))


def document_icon(x, y, color=BLUE):
    box(x + 3, y, 24, 29, fill="none", stroke=color, radius=3, lw=1.5)
    for dy, length in [(8, 14), (14, 14), (20, 9)]:
        line(x + 8, y + dy, x + 8 + length, y + dy, color, 1.1)


def cursor_icon(x, y, color=BLUE):
    vertices = [
        (x + 5, y), (x + 5, y + 27), (x + 12, y + 20),
        (x + 18, y + 30), (x + 23, y + 27), (x + 17, y + 18),
        (x + 27, y + 16), (x + 5, y),
    ]
    ax.add_patch(PathPatch(MplPath(vertices, [MplPath.MOVETO] + [MplPath.LINETO] * 7),
                           fill=False, edgecolor=color, linewidth=1.5, joinstyle="round"))


def step(x, number, title, width=328):
    box(x, 430, width, 294, radius=16)
    ax.add_patch(Circle((x + 34, 461), 18, color=BLUE))
    text(x + 34, 447, str(number), 24, "white", "bold", "center")
    text(x + 64, 444, title, 26, weight="bold")
    line(x + 22, 490, x + width - 22, 490)


# Context and evaluation-set scope.
text(64, 34, "CO-DESIGN BENCH", 21, BLUE, "bold")
text(64, 72, "From user intent to working software", 47, weight="bold")
text(64, 137, "Real application revisions, evaluated from source and browser evidence.", 26, MUTED)
text(64, 187, "FULL EVALUATION SET  /  273 TASKS  /  2,331 ACCEPTANCE CRITERIA", 21, MUTED, "bold")

# Release status is separate from the full task and criterion counts.
box(64, 226, 724, 174, BLUE_PALE, "#D6E0F3", 16)
text(88, 247, "TRACK 1", 20, BLUE, "bold")
box(526, 241, 238, 38, "#E0E9FA", "none", 19)
text(645, 248, "96 tasks released", 21, BLUE, "bold", "center")
text(88, 281, "Multimodal Editing", 33, weight="bold")
text(88, 326, "Localized edits grounded in multimodal inputs", 24, MUTED)
text(88, 364, "100 tasks  ·  553 criteria", 24, BLUE, "bold")

box(812, 226, 724, 174, GOLD_PALE, "#EBDDC5", 16)
text(836, 247, "TRACK 2", 20, GOLD, "bold")
box(1342, 241, 170, 38, "#EFE5D3", "none", 19)
text(1427, 248, "Not released", 21, GOLD, "bold", "center")
text(836, 281, "Repository Editing", 33, weight="bold")
text(836, 326, "Coordinated changes across a frontend repository", 24, MUTED)
text(836, 364, "173 tasks  ·  1,778 criteria", 24, GOLD, "bold")

# A single workflow applies to both tracks. Only evaluators receive the rubric.
step(64, 1, "Task inputs")
step(446, 2, "Agent revision")
step(828, 3, "Collect evidence")
step(1210, 4, "Judge → Refute", width=326)
for left, right in [(392, 446), (774, 828), (1156, 1210)]:
    arrow(left + 8, 580, right - 8, 580, color="#8998B5", size=17)

browser_icon(88, 516)
text(132, 516, "Runnable app", 26)
document_icon(88, 563)
text(132, 563, "Request + context", 25)
text(88, 618, "Optional attachments", 23, MUTED)
for x, w, label in [(88, 70, "Image"), (164, 70, "Audio"), (240, 70, "Video"), (316, 52, "Doc")]:
    box(x, 657, w, 35, BLUE_PALE, "none", 6)
    text(x + w / 2, 664, label, 20, BLUE, align="center")

for y, label in [(515, "Inspect"), (574, "Edit source"), (633, "Build + run")]:
    box(472, y, 206, 42, BLUE_PALE, "none", 8)
    text(575, y + 6, label, 25, BLUE, align="center")
arrow(575, 559, 575, 571, size=10)
arrow(575, 618, 575, 630, size=10)
line(682, 654, 732, 654, BLUE, 1.6)
line(732, 654, 732, 536, BLUE, 1.6)
arrow(732, 536, 682, 536, size=12)
text(575, 689, "Iterative tool use", 21, MUTED, align="center")

document_icon(852, 516)
text(896, 516, "Source diffs", 25)
browser_icon(852, 569)
text(896, 569, "Rendered pages", 25)
cursor_icon(852, 622)
text(896, 622, "Browser actions", 25)
text(852, 679, "Check the final application", 21, MUTED)

box(1232, 511, 282, 54, GOLD_PALE, "none", 8)
text(1373, 515, "Hidden criteria", 22, GOLD, "bold", "center")
text(1373, 541, "Evaluator only", 20, GOLD, align="center")
text(1373, 586, "Grade each criterion", 25, align="center")
arrow(1373, 618, 1373, 635, color="#8998B5", size=10)
text(1373, 646, "Challenge positive verdicts", 21, align="center")
text(1373, 684, "Audit supporting evidence", 20, MUTED, align="center")

# Verdicts become three complementary completion metrics.
box(64, 757, 1472, 68, "#F5F7FB", "none", 12)
text(88, 780, "PASS", 24, GREEN, "bold")
text(179, 780, "/", 24, MUTED)
text(205, 780, "PARTIAL", 24, GOLD, "bold")
text(335, 780, "/", 24, MUTED)
text(361, 780, "FAIL", 24, ROSE, "bold")
arrow(452, 793, 509, 793, color="#8998B5", size=13)
text(536, 780, "Strict  ·  Graded  ·  Full pass", 26, weight="bold")
text(1509, 785, "No gold code or target screenshots", 21, MUTED, align="right")

description = (
    "Co-Design Bench contains 273 evaluation tasks and 2,331 criteria: "
    "100 Multimodal Editing tasks (96 publicly released) and 173 Repository "
    "Editing tasks (not released). Runnable task inputs lead to iterative agent "
    "revisions, source and browser evidence, and judge-then-refute evaluation "
    "against hidden acceptance criteria. PASS, PARTIAL and FAIL verdicts are "
    "aggregated into Strict, Graded and Full-pass metrics."
)
metadata = {"Title": "Co-Design Bench overview", "Description": description}
fig.savefig(OUT / "overview.svg", facecolor="white", metadata=metadata)
fig.savefig(OUT / "overview.png", dpi=200, facecolor="white", metadata=metadata)
plt.close(fig)
for name in ["overview.svg", "overview.png"]:
    print(OUT / name)
