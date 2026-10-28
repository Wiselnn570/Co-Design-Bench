#!/usr/bin/env python3
"""Audit judge output for visual-evidence claims when mandatory render failed."""
import argparse
import json
import re
import sys


CLAIM_RE = re.compile(
    r"render shows|render confirms|rendered screenshot|screenshot confirms|"
    r"截图(?:显示|确认)|渲染(?:显示|确认|正常|通过|可见)",
    re.I,
)


def load_journal(path):
    out = []
    for line in open(path, encoding="utf-8", errors="ignore"):
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if obj.get("type") == "result":
            val = obj.get("value") or obj.get("result") or obj.get("data")
            if isinstance(val, dict):
                out.append(val)
    return out


def result_text(result):
    chunks = [str(result.get("final_notes") or result.get("notes") or "")]
    for req in result.get("requirements") or []:
        chunks.append(str(req.get("evidence") or ""))
    return "\n".join(chunks)


def render_bad(render):
    if not render:
        return True
    return (
        render.get("status") == "RENDER_FAIL"
        or render.get("process_rc") not in (0, "0")
        or render.get("render_rc") not in (0, "0")
        or not render.get("dom_path")
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--journal", required=True)
    ap.add_argument("--render-json", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--fail-on-violation", action="store_true")
    args = ap.parse_args()

    renders = json.load(open(args.render_json, encoding="utf-8"))
    violations = []
    for result in load_journal(args.journal):
        uuid = result.get("uuid")
        render = renders.get(uuid, {})
        text = result_text(result)
        if render_bad(render):
            hits = sorted({m.group(0) for m in CLAIM_RE.finditer(text)})
            if hits:
                violations.append(
                    {
                        "uuid": uuid,
                        "render_status": render.get("status", "MISSING"),
                        "render_rc": render.get("render_rc"),
                        "body_words": render.get("body_words"),
                        "claims": hits,
                    }
                )
    json.dump({"violations": violations}, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"visual evidence guard violations={len(violations)} -> {args.out}")
    if violations and args.fail_on_violation:
        sys.exit(2)


if __name__ == "__main__":
    main()
