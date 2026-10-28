#!/usr/bin/env python3
"""Compose real public screenshots and archived browser footage for GitHub.

Requires Pillow and ffmpeg. Defaults to the public captures packaged in
showcase-sources/. No model or application is executed.

    python docs/assets/make_task_showcase.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps


W, H = 1280, 890
INK = "#15243f"
MUTED = "#65738a"
BLUE = "#4265dc"
CYAN = "#0d8d9c"
PURPLE = "#7b5bd2"
MODEL = "qwen3.8-max-0902"
ORDER = ["7d7953f8", "b0e36f34", "f725ea72"]
CASES = {
    "7d7953f8": {
        "nav": "01  Video → title motion",
        "title": "Read motion.\nRevise three titles.",
        "tag": "VIDEO REFERENCE",
        "color": PURPLE,
        "request": "Map three video effects to three marked headings. Keep the wording and layout.",
        "inspect": ["Hero highlight sweep", "Hue-cycling routine title", "Staggered quotation"],
        "app": "Tideline",
        "before": "assets/cases/7d7953f8-baseline.webp",
        "output": "assets/cases/outputs/7d7953f8-qwen3.8-max-0902.webp",
        "video": "assets/cases/outputs/7d7953f8-qwen3.8-max-0902.mp4",
        "crop": [0, 0, 1200, 750],
        "short": "Three effects, mapped to three existing headings.",
    },
    "b0e36f34": {
        "nav": "02  Image + sheet → counts",
        "title": "Reconcile evidence.\nUpdate the views.",
        "tag": "IMAGE + SPREADSHEET",
        "color": BLUE,
        "request": "Correct the marked click statistics from an audit export and a printed proof.",
        "inspect": ["Weekly KPI: 939", "Ranking: /events at 241", "Table still has old counts"],
        "app": "BulletinLink",
        "before": "assets/cases/outputs/b0e36f34-baseline.webp",
        "output": "assets/cases/outputs/b0e36f34-qwen3.8-max-0902.webp",
        "crop": [0, 0, 1200, 950],
        "short": "KPI and ranking change; the table shows an incomplete revision.",
    },
    "f725ea72": {
        "nav": "03  PDF receipt → dashboard",
        "title": "Correct one row.\nFollow every total.",
        "tag": "PDF RECEIPT",
        "color": CYAN,
        "request": "Use the receipt's salt-line amount, then recompute the dashboard. Preserve unrelated values.",
        "inspect": ["Spent: $511.50 → $652.00", "Remaining: $188.50 → $48", "Salt share: 13% → 32%"],
        "app": "ReefLedger",
        "before": "assets/cases/outputs/f725ea72-baseline.webp",
        "output": "assets/cases/outputs/f725ea72-qwen3.8-max-0902.webp",
        "crop": [0, 0, 1200, 750],
        "short": "Receipt evidence changes totals, remaining budget, and chart shares.",
    },
}


def font(size: int, bold: bool = False):
    names = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
    ]
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    raise RuntimeError("Install DejaVu Sans or make it available to Pillow.")


def wrapped(draw, text, x, y, width, size=23, color=INK, bold=False, gap=8):
    face = font(size, bold)
    for paragraph in text.split("\n"):
        words = paragraph.split()
        line = ""
        for word in words:
            candidate = f"{line} {word}".strip()
            if line and draw.textlength(candidate, font=face) > width:
                draw.text((x, y), line, font=face, fill=color)
                y += size + gap
                line = word
            else:
                line = candidate
        if line:
            draw.text((x, y), line, font=face, fill=color)
            y += size + gap
    return y


def pill(draw, box, text, fill, color, size=15, border=None):
    draw.rounded_rectangle(box, radius=14, fill=fill, outline=border, width=1)
    face = font(size, True)
    x = (box[0] + box[2] - draw.textlength(text, font=face)) / 2
    draw.text((x, box[1] + (box[3] - box[1] - size) / 2 - 2), text, font=face, fill=color)


def paste_contained(canvas, picture, box):
    image = ImageOps.contain(picture.convert("RGB"), (box[2] - box[0], box[3] - box[1]), Image.Resampling.LANCZOS)
    canvas.paste(image, (box[0] + (box[2] - box[0] - image.width) // 2,
                         box[1] + (box[3] - box[1] - image.height) // 2))


def crop_capture(root, case, key):
    picture = Image.open(source_path(root, case[key])).convert("RGB")
    # Align full-page captures to the same 1200-pixel coordinate system.
    if picture.width != 1200:
        picture = picture.resize((1200, round(picture.height * 1200 / picture.width)), Image.Resampling.LANCZOS)
    return picture.crop(tuple(case["crop"]))


def background(active):
    canvas = Image.new("RGB", (W, H), "#f8fafc")
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, W, 166), fill="white")
    draw.text((38, 24), "REAL TASKS  /  ACTUAL APPLICATION REVISIONS", font=font(15, True), fill=BLUE)
    draw.text((36, 54), "See what the agent changed.", font=font(42, True), fill=INK)
    for i, case_id in enumerate(ORDER):
        case = CASES[case_id]
        x = 38 + i * 405
        is_active = case_id == active
        pill(draw, (x, 118, x + 392, 157), case["nav"],
             "#edf1ff" if is_active else "#f7f8fb", case["color"] if is_active else MUTED, size=17)
    case = CASES[active]
    pill(draw, (38, 199, 344, 237), case["tag"], "#eaf1fa", case["color"], size=14)
    y = wrapped(draw, case["title"], 38, 267, 309, size=31, bold=True, gap=9)
    draw.text((38, y + 22), "THE REQUEST", font=font(14, True), fill=case["color"])
    y = wrapped(draw, case["request"], 38, y + 54, 301, size=22, gap=9)
    draw.text((38, y + 25), "WHAT TO INSPECT", font=font(14, True), fill=case["color"])
    y += 60
    for text in case["inspect"]:
        draw.rounded_rectangle((39, y + 8, 45, y + 14), radius=3, fill=case["color"])
        y = wrapped(draw, text, 56, y, 288, size=18, gap=6) + 12
    draw.text((38, 801), f"CASE {active}  ·  ME", font=font(15, True), fill=MUTED)

    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((378, 197, 1250, 790), radius=22, fill=(37, 58, 100, 27))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), shadow.filter(ImageFilter.GaussianBlur(15))).convert("RGB")
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((375, 185, 1244, 780), radius=18, fill="white", outline="#dce3ee", width=1)
    draw.rectangle((376, 222, 1243, 235), fill="#f3f5f9")
    draw.rounded_rectangle((375, 185, 1244, 234), radius=18, fill="#f3f5f9")
    for i, color in enumerate(["#d7deeb", "#c5d6ec", "#c9c9ef"]):
        draw.ellipse((393 + i * 16, 203, 400 + i * 16, 210), fill=color)
    draw.text((450, 194), f"{case['app']}  /  archived capture", font=font(16), fill=MUTED)
    draw.line((38, 846, 1242, 846), fill="#dfe5ee", width=1)
    draw.text((38, 858), f"Actual agent: {MODEL}", font=font(15, True), fill=INK)
    draw.text((525, 858), "Screenshot comparison + archived browser footage. No target render.", font=font(14), fill=MUTED)
    return canvas


def slide(root, case_id, phase, video_frame=None):
    canvas = background(case_id)
    case = CASES[case_id]
    draw = ImageDraw.Draw(canvas)
    color = case["color"] if phase == "output" else MUTED
    phase_label = "Actual agent output" if phase == "output" else "Before"
    pill(draw, (987, 193, 1226, 225), phase_label, "white", color, size=15)
    picture = video_frame if video_frame is not None else crop_capture(root, case, "output" if phase == "output" else "before")
    paste_contained(canvas, picture, (389, 248, 1230, 768))
    draw = ImageDraw.Draw(canvas)
    draw.text((382, 802), "Archived browser footage" if video_frame is not None else "Actual screenshot · matched crop", font=font(16, True), fill=color)
    draw.text((1000, 802), "Before  →  Output", font=font(16), fill=MUTED)
    return canvas


def static_comparison(root):
    canvas = Image.new("RGB", (W, 1520), "#f8fafc")
    draw = ImageDraw.Draw(canvas)
    draw.text((38, 26), "THREE REAL TASKS  /  BEFORE → ACTUAL AGENT OUTPUT", font=font(16, True), fill=BLUE)
    draw.text((36, 62), "Different evidence. Existing applications.", font=font(35, True), fill=INK)
    draw.text((38, 112), f"Archived outputs from {MODEL} · screenshots are crops, not target renders", font=font(17), fill=MUTED)
    for i, case_id in enumerate(ORDER):
        case = CASES[case_id]
        top = 168 + i * 432
        draw.rounded_rectangle((28, top, 1252, top + 414), radius=20, fill="white", outline="#dce3ee")
        draw.text((49, top + 19), f"{case['nav']}  ·  {case_id}", font=font(22, True), fill=case["color"])
        draw.text((49, top + 54), case["short"], font=font(18), fill=MUTED)
        for j, key in enumerate(["before", "output"]):
            left = 49 + j * 605
            draw.text((left, top + 92), "Before" if key == "before" else "Actual agent output", font=font(15, True), fill=MUTED if key == "before" else case["color"])
            draw.rounded_rectangle((left, top + 122, left + 576, top + 398), radius=10, fill="#f5f7fb")
            paste_contained(canvas, crop_capture(root, case, key), (left + 5, top + 125, left + 571, top + 395))
    draw.text((38, 1483), "The visual comparison illustrates revisions; it does not certify every acceptance criterion.", font=font(16), fill=MUTED)
    return canvas


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_path(root, public_path):
    nested = root / public_path
    return nested if nested.is_file() else root / Path(public_path).name


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=Path(__file__).resolve().parent / "showcase-sources")
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--fps", type=int, default=5, help="Sample real video frames without changing playback duration")
    args = parser.parse_args()
    root = args.source_root
    metadata_path = source_path(root, "data/site-data.json")
    site_data = json.loads(metadata_path.read_text())
    original = {case["id"]: case for case in site_data["cases"]}
    whitelist = set((Path(__file__).resolve().parents[2] / "data/case_ids_me96.txt").read_text().splitlines())
    for case_id in ORDER:
        assert case_id in whitelist, f"Not a public ME task: {case_id}"
        assert CASES[case_id]["output"] == original[case_id]["outputs"][MODEL]
        assert CASES[case_id]["before"] == original[case_id]["editsBaseline"]
    if not 1 <= args.fps <= 10:
        parser.error("Use a sampling rate from 1 to 10 fps.")
    args.out.mkdir(parents=True, exist_ok=True)
    frames, durations = [], []
    with tempfile.TemporaryDirectory(prefix="cdb-real-showcase-") as directory:
        video = source_path(root, CASES["7d7953f8"]["video"])
        subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-vf", f"fps={args.fps}",
                        str(Path(directory) / "frame-%04d.png")], check=True)
        frames.append(slide(root, "7d7953f8", "before"))
        durations.append(1600)
        for path in sorted(Path(directory).glob("frame-*.png")):
            with Image.open(path) as picture:
                frames.append(slide(root, "7d7953f8", "output", picture.copy()))
                durations.append(round(1000 / args.fps))
        for case_id in ORDER[1:]:
            for phase, duration in [("before", 1800), ("output", 2800)]:
                frames.append(slide(root, case_id, phase))
                durations.append(duration)
    # One global palette keeps static typography stable and allows GIF delta frames.
    sample = Image.new("RGB", (320 * 4, 223 * 4), "white")
    for i in range(16):
        frame = frames[round(i * (len(frames) - 1) / 15)].resize((320, 223))
        sample.paste(frame, ((i % 4) * 320, (i // 4) * 223))
    photographic_palette = sample.quantize(colors=192, method=Image.Quantize.MEDIANCUT).getpalette()[:192 * 3]
    fixed_colors = [INK, MUTED, BLUE, CYAN, PURPLE, "#ffffff", "#f8fafc", "#edf1ff", "#eaf1fa",
                    "#dce3ee", "#f3f5f9", "#dfe5ee", "#00ff00", "#ff00ff", "#ffaf00", "#0bb9d4"]
    fixed_palette = [int(color[i:i + 2], 16) for color in fixed_colors for i in (1, 3, 5)]
    dashboard_palette = crop_capture(root, CASES["f725ea72"], "output").quantize(
        colors=48, method=Image.Quantize.MEDIANCUT).getpalette()[:48 * 3]
    palette = Image.new("P", (1, 1))
    palette.putpalette(photographic_palette + fixed_palette + dashboard_palette)
    indexed = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    gif = args.out / "task-showcase.gif"
    indexed[0].save(gif, save_all=True, append_images=indexed[1:], duration=durations,
                    loop=0, optimize=True, disposal=1)
    if gif.stat().st_size > 5_000_000:
        raise RuntimeError("GIF exceeded 5 MB; re-run with --fps 3 to retain real playback at a smaller size.")
    png = args.out / "task-showcase.png"
    static_comparison(root).save(png, optimize=True)
    sources = []
    for case_id in ORDER:
        case = CASES[case_id]
        paths = [case["before"], case["output"]] + ([case["video"]] if "video" in case else [])
        sources.append({"case_id": case_id, "track": "ME", "public_whitelist_verified": True,
                        "model": MODEL, "request": original[case_id]["request"],
                        "screenshots": {key: case[key] for key in ["before", "output"]},
                        "normalized_screenshot_width": 1200, "crop_box": case["crop"],
                        "archived_video": case.get("video"),
                        "source_files": [{"path": path, "packaged_path": "showcase-sources/" + Path(path).name,
                                          "sha256": digest(source_path(root, path))} for path in paths]})
    provenance = {"schema_version": 1, "public_source_site": "https://codesignbench.github.io/",
                  "site_data": "data/site-data.json",
                  "site_data_sha256": site_data.get("meta", {}).get("source_site_data_sha256", digest(metadata_path)),
                  "packaged_metadata": "showcase-sources/site-data.json",
                  "packaged_metadata_sha256": digest(metadata_path),
                  "description": "Real baseline/output screenshots; motion stage samples an archived output browser recording. No gold target or new application run is generated.",
                  "generator": "docs/assets/make_task_showcase.py", "video_sampling_fps": args.fps,
                  "video_speed": "Original playback duration, sampled frames",
                  "cases": sources,
                  "artifacts": {"task-showcase.gif": {"width": W, "height": H, "bytes": gif.stat().st_size,
                                  "sha256": digest(gif), "frames": len(indexed)},
                                "task-showcase.png": {"width": W, "height": 1520, "bytes": png.stat().st_size,
                                  "sha256": digest(png)}}}
    (args.out / "task-showcase-sources.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(provenance["artifacts"], indent=2))


if __name__ == "__main__":
    main()
