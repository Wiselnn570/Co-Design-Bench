"""Render the GitHub hero and compact workflow from public assets.

Requires Pillow. Run this file from any working directory.
The application image is a real archived qwen3.8-max-0902 output.
"""

from pathlib import Path
import json
import math

from PIL import Image, ImageDraw, ImageFont, ImageFilter


OUT = Path(__file__).resolve().parent


def font(size, bold=False):
    name = "Lato-Heavy.ttf" if bold else "Lato-Regular.ttf"
    candidates = [
        Path("/usr/share/fonts/truetype/lato") / name,
        Path("/usr/share/fonts/truetype/dejavu") /
        ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"),
        Path("/System/Library/Fonts/Supplemental") /
        ("Arial Bold.ttf" if bold else "Arial.ttf"),
    ]
    for path in candidates:
        if path.is_file():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default(size=size)


def text(image, position, value, size=26, color="#FFFFFF", bold=False):
    ImageDraw.Draw(image).text(position, value, font=font(size, bold), fill=color)


def rounded(image, box, radius, fill, outline=None, width=1):
    ImageDraw.Draw(image, "RGBA").rounded_rectangle(
        box, radius=radius, fill=fill, outline=outline, width=width)


def shadow(image, box):
    layer = Image.new("RGBA", image.size)
    shifted = tuple(value + (12 if index % 2 else 0)
                    for index, value in enumerate(box))
    ImageDraw.Draw(layer).rounded_rectangle(shifted, radius=26, fill=(0, 0, 0, 115))
    image.paste(Image.alpha_composite(image.convert("RGBA"),
                                     layer.filter(ImageFilter.GaussianBlur(28))).convert("RGB"))


def paste_round(image, asset, position, radius):
    mask = Image.new("L", asset.size)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, asset.width - 1, asset.height - 1), radius=radius, fill=255)
    image.paste(asset, position, mask)


def hero():
    width, height = 1400, 700
    image = Image.new("RGB", (width, height))
    pixels = image.load()
    for y in range(height):
        for x in range(width):
            t = x / (width - 1)
            glow = math.exp(-(((x - 1050) / 570) ** 2 + ((y - 110) / 370) ** 2))
            pixels[x, y] = (int(10 + 15*t + 12*glow),
                            int(20 + t + 7*glow), int(40 + 32*t + 28*glow))
    draw = ImageDraw.Draw(image, "RGBA")
    for x in range(0, width, 70):
        draw.line((x, 0, x, height), fill=(255, 255, 255, 9))
    for y in range(0, height, 70):
        draw.line((0, y, width, y), fill=(255, 255, 255, 9))
    rounded(image, (58, 45, 450, 86), 20, (45, 211, 190, 26), (53, 183, 175, 95))
    text(image, (80, 53), "MULTIMODAL CODING BENCHMARK", 18, "#6CE3D5", True)
    text(image, (58, 116), "Co-Design Bench", 72, bold=True)
    text(image, (61, 217), "Real requests.", 47, bold=True)
    text(image, (61, 275), "Working revisions.", 47, "#90EBDF", True)
    text(image, (62, 356), "Understand the request. Edit the app.", 27, "#C3CBDE")
    text(image, (62, 395), "Verify what actually works.", 27, "#C3CBDE")
    text(image, (62, 474), "THE PAPER EVALUATION", 17, "#899AB9", True)
    for x, value, label in [(62, "273", "real-user tasks"),
                            (282, "2,331", "fixed criteria"),
                            (534, "10", "model endpoints")]:
        text(image, (x, 509), value, 50, bold=True)
        text(image, (x, 568), label, 21, "#B3C0D7")
    shadow(image, (786, 117, 1340, 488))
    rounded(image, (810, 94, 1356, 442), 24, "#2A3759", "#455274", 2)
    rounded(image, (786, 117, 1340, 488), 24, "#F5F8FB", "#7685A8")
    draw = ImageDraw.Draw(image)
    for i, color in enumerate(["#FF858A", "#FFC86B", "#6DD9AC"]):
        draw.ellipse((808+i*18, 133, 818+i*18, 143), fill=color)
    text(image, (881, 131), "ARCHIVED AGENT OUTPUT", 15, "#556276", True)
    screenshot = Image.open(OUT / "receipt-output.webp").convert("RGB")
    screenshot = screenshot.resize((530, 331), Image.Resampling.LANCZOS)
    paste_round(image, screenshot, (798, 153), 14)
    mascot = Image.open(OUT / "logo.png").convert("RGBA").resize((81, 81), Image.Resampling.LANCZOS)
    image.paste(mascot, (1270, 9), mascot)
    rounded(image, (786, 513, 1340, 606), 18, (255, 255, 255, 10), (149, 162, 198, 58))
    text(image, (808, 531), "ONE RECEIPT. EVERY DEPENDENT VIEW.", 18, "#68DED0", True)
    text(image, (808, 563), "Correct the cost. Reconcile totals and charts.", 20, "#C7D2E7")
    ImageDraw.Draw(image).line((58, 622, 1340, 622), fill="#34415E")
    text(image, (60, 647), "PUBLIC SUBSET", 18, "#8394B4", True)
    text(image, (242, 643), "96 ME tasks  /  521 criteria", 27, "#EFF6FF", True)
    text(image, (1110, 650), "arXiv:2610.35138", 17, "#A7B7D0")
    image.save(OUT / "github-hero.png", optimize=True)


def pipeline():
    image = Image.new("RGB", (1400, 340), "#FFFFFF")
    text(image, (28, 18), "FROM A USER REQUEST TO A VERIFIED REVISION", 22, "#152744", True)
    steps = [
        (28, "01", "Ground the request", ["Initial app + request context", "Optional media / ME annotation"], "#EAF8F5", "#167F79"),
        (378, "02", "Revise the app", ["Inspect, edit, build, run", "Keep preserved behavior intact"], "#EEF2FD", "#4D63BD"),
        (728, "03", "Collect evidence", ["Source changes + rendered UI", "Check relevant interactions"], "#F4F0FC", "#785CB4"),
        (1078, "04", "Judge → Refute", ["Fixed evaluator-only criteria", "Challenge positive credit"], "#ECF6FB", "#247A9E"),
    ]
    for x, number, title, lines, fill, accent in steps:
        rounded(image, (x, 77, x+294, 249), 18, fill)
        text(image, (x+18, 91), number, 18, accent, True)
        text(image, (x+18, 125), title, 26, "#1B2942", True)
        for i, line in enumerate(lines):
            text(image, (x+18, 175+i*30), line, 17, "#57667E")
        if x < 1000:
            start = x + 305
            draw = ImageDraw.Draw(image)
            draw.line((start, 166, start+26, 166), fill="#91A0B7", width=3)
            draw.polygon([(start+26, 166), (start+17, 159), (start+17, 173)], fill="#91A0B7")
    rounded(image, (28, 277, 1372, 330), 14, "#F3F6FA")
    text(image, (48, 288), "PASS", 19, "#187E6A", True)
    text(image, (118, 288), " / PARTIAL / FAIL", 19, "#596A84", True)
    text(image, (381, 287), "Strict  ·  Graded  ·  Full pass", 21, "#1A2D4B", True)
    text(image, (951, 292), "Equal weight for every task", 18, "#5E708C")
    image.save(OUT / "github-pipeline.png", optimize=True)


if __name__ == "__main__":
    hero()
    pipeline()
    print("Rendered GitHub hero and pipeline.")
