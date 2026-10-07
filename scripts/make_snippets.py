"""Collect the source text relevant to one matchup into a single short file for claim extraction.

  make_snippets.py <role> <Enemy>  ->  data/clean/snippets/<role>_<Enemy>.txt
  make_snippets.py --general       ->  data/clean/snippets/_general.txt  (macro / teamfight / post-6
                                         excerpts from OTP transcripts dated after Garen's kit baseline)

- YouTube transcript whose title names the enemy: whole transcript.
- Other transcripts: +-WINDOW words around each mention of the enemy (aliases from config.yaml).
- MOBAFire threat lines for the enemy.
Sources dated before the enemy's kit_baseline (release / full rework) are skipped: every stable claim
from them would be invalid. Each block starts with a header carrying the claim metadata.
"""
from __future__ import annotations

import json
import re
import sys

from polite_http import CONFIG, ROOT

CLEAN = ROOT / "data" / "clean"
WINDOW = 150
AUTHORS = CONFIG["sources"]["video_authors"]


def display_name(cid: str) -> str:
    champs = json.loads((ROOT / "data/meta/champions.json").read_text(encoding="utf-8"))
    return champs.get(cid, {}).get("name", cid)


def header(fields: dict) -> str:
    return "\n=== SOURCE " + " | ".join(f"{k}: {v}" for k, v in fields.items()) + "\n"


def read_transcript(path) -> tuple[dict, str]:
    head, _, body = path.read_text(encoding="utf-8").partition("\n\n")
    meta = dict(l.split(": ", 1) for l in head.splitlines() if ": " in l)
    return meta, body


def windows(words: list[str], pattern: re.Pattern) -> list[tuple[int, int]]:
    spans = []
    for i, w in enumerate(words):
        if pattern.search(w if " " not in pattern.pattern else " ".join(words[i:i + 2])):
            lo, hi = max(0, i - WINDOW), min(len(words), i + WINDOW)
            if spans and lo <= spans[-1][1]:
                spans[-1] = (spans[-1][0], hi)
            else:
                spans.append((lo, hi))
    return spans


MACRO = re.compile(r"\b(split ?push\w*|side ?lan\w*|team ?fight\w*|group\w*|peel\w*|baron|drag(?:on)?s?|"
                   r"objective\w*|rotat\w*|win condition|tower ?div\w*|carry|ult(?:imate)?|execute)\b", re.I)


def general():
    """Macro-play excerpts from Garen OTP videos (otp_video authors only), +-60 words around macro keywords."""
    garen = json.loads((ROOT / "data/meta/change_log/Garen.json").read_text(encoding="utf-8"))
    last_mech = (garen.get("last_mechanic_change") or {}).get("release") or "0000"
    out, report = [], []
    for path in sorted((CLEAN / "youtube").glob("*.txt")):
        meta, body = read_transcript(path)
        info = AUTHORS.get(meta.get("author", "?"), {"type": "other_guide", "elo": "unknown"})
        if info["type"] != "otp_video" or (meta.get("source_date") or "0") < last_mech:
            continue
        words = body.split()
        spans = []
        for i, w in enumerate(words):
            if MACRO.search(w):
                lo, hi = max(0, i - 60), min(len(words), i + 60)
                if spans and lo <= spans[-1][1]:
                    spans[-1] = (spans[-1][0], hi)
                else:
                    spans.append((lo, hi))
        if not spans:
            continue
        text = "\n[...]\n".join(" ".join(words[a:b]) for a, b in spans)
        out.append(header({"source_url": meta.get("url"), "author": meta.get("author"), "source_date": meta.get("source_date"),
                           "source_type": info["type"], "elo_context": info["elo"], "title": meta.get("title"),
                           "included": f"{len(spans)} macro excerpt(s)"}) + text)
        report.append(f"use {len(text.split()):>5} words  {meta.get('author')} {meta.get('source_date')} {meta.get('title', '')[:50]}")
    dest = CLEAN / "snippets" / "_general.txt"
    dest.parent.mkdir(parents=True, exist_ok=True)
    head = f"# General Garen macro snippets; sources after Garen's last mechanic change ({last_mech})\n"
    dest.write_text(head + "\n".join(out), encoding="utf-8")
    print("\n".join(report))
    print(f"-> {dest.relative_to(ROOT)}: {len(dest.read_text(encoding='utf-8').split())} words")


def main():
    if "--general" in sys.argv:
        return general()
    role, enemy = sys.argv[1], sys.argv[2]
    aliases = CONFIG["sources"]["champion_aliases"].get(enemy, [enemy.lower()])
    pattern = re.compile(r"\b(" + "|".join(re.escape(a) for a in aliases) + r")\b", re.I)
    log = json.loads((ROOT / "data/meta/change_log" / f"{enemy}.json").read_text(encoding="utf-8"))
    baseline = (log.get("kit_baseline") or {}).get("release") or "0000"

    out, report = [], []
    for path in sorted((CLEAN / "youtube").glob("*.txt")):
        meta, body = read_transcript(path)
        author = meta.get("author", "?")
        info = AUTHORS.get(author, {"elo": "unknown", "type": "other_guide"})
        fields = {"source_url": meta.get("url"), "author": author, "source_date": meta.get("source_date"),
                  "source_type": info["type"], "elo_context": info["elo"], "title": meta.get("title")}
        words = body.split()
        if pattern.search(meta.get("title", "")):
            text, how = body, "whole transcript"
        else:
            spans = windows(words, pattern)
            if not spans:
                continue
            text = "\n[...]\n".join(" ".join(words[a:b]) for a, b in spans)
            how = f"{len(spans)} excerpt(s)"
        if (meta.get("source_date") or "0") < baseline:
            report.append(f"SKIP (before {enemy} kit baseline {baseline}): {author} {meta.get('source_date')} {meta.get('title', '')[:50]}")
            continue
        out.append(header(fields | {"included": how}) + text)
        report.append(f"use  {how:<17} {len(text.split()):>5} words  {author} {meta.get('source_date')} {meta.get('title', '')[:50]}")

    for path in sorted((CLEAN / "mobafire").glob("*_threats.txt")):
        head, _, body = path.read_text(encoding="utf-8").partition("\n\n")
        name = display_name(enemy)  # threat lists use display names ("K'Sante"), not ids ("KSante")
        lines = [l for l in body.splitlines() if l.split(" = ")[0].strip() == name]
        lines += [f"{name}={m.group(1)}" for m in re.finditer(rf"(?<![\w']){re.escape(name)}=(\w+)", body)]
        if lines:
            out.append(f"\n=== SOURCE (MOBAFire threats; see header)\n{head}\n" + "\n".join(dict.fromkeys(lines)))
            report.append(f"use  threat line(s)          {path.name}")

    dest = CLEAN / "snippets" / f"{role}_{enemy}.txt"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(f"# Snippets for {role} vs {enemy}; enemy kit baseline {baseline}\n" + "\n".join(out), encoding="utf-8")
    print("\n".join(report))
    print(f"-> {dest.relative_to(ROOT)}: {len(dest.read_text(encoding='utf-8').split())} words")


if __name__ == "__main__":
    main()
