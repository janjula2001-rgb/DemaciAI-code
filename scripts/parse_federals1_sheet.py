"""Federals1's public Garen matchup spreadsheet -> data/clean/federals1/sheet.json (deterministic).

Columns: champion | level-up order | runes + summoner spells | build path to 2-3 items | difficulty | tips
(the tips column is empty: Federals1 moved tips to a paid site, which we don't use).
Linked from his MOBAFire guide (updated 2026-08-31), where he says the sheet is kept ~98% up to date;
the sheet itself carries no per-row dates, so claims from it are marked date_uncertain.
Usage: parse_federals1_sheet.py [--refresh]
"""
from __future__ import annotations

import csv
import io
import json
import re
import sys

from polite_http import ROOT, fetch

SHEET_ID = "1hoDv6XMqwK_ABrUaeqM0D8UP6jDbiw33G9m7USmCrLg"
VIEW_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}"
CSV_URL = f"{VIEW_URL}/export?format=csv&gid=0"
NAME_FIXES = {"jarvan": "JarvanIV", "llillia": "Lillia", "nunu": "Nunu"}  # sheet spellings
DIFFICULTY = {"easy matchup": 2, "skill matchup": 3, "hard matchup": 4, "extremely hard matchup": 5}


def main():
    text = fetch(CSV_URL, "federals1", "sheet_gid0.csv", refresh="--refresh" in sys.argv).text
    rows = list(csv.reader(io.StringIO(text)))
    champs = json.loads((ROOT / "data/meta/champions.json").read_text(encoding="utf-8"))
    by_name = {re.sub(r"[^a-z]", "", c["name"].lower()): cid for cid, c in champs.items()}
    out, unmatched = {}, []
    for r in rows:
        if len(r) < 5 or not r[0].strip() or r[0].strip() == "Champion" or not r[1].strip():
            continue
        key = re.sub(r"[^a-z]", "", r[0].lower())
        cid = by_name.get(key) or NAME_FIXES.get(key)
        if not cid:
            unmatched.append(r[0])
            continue
        lines = [l.strip() for l in r[2].splitlines() if l.strip()]
        summ = next((l.split(":", 1)[1].strip() for l in lines if l.lower().startswith("summoner")), None)
        runes = [l for l in lines if not l.lower().startswith("summoner")]
        diff = r[4].strip()
        out[cid] = {"name": r[0].strip(), "skill_order": r[1].strip(), "runes": runes, "summoners": summ,
                    "build_path": [s.strip() for s in r[3].split(">") if s.strip()],
                    "difficulty_label": diff, "difficulty": DIFFICULTY.get(diff.lower()),
                    "tips": r[5].strip() if len(r) > 5 else ""}
    dest = ROOT / "data/clean/federals1/sheet.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps({"source_url": VIEW_URL, "author": "Federals1", "elo_context": "challenger",
                                "source_date": "2026-08-31", "date_note": "MOBAFire guide last update; rows undated",
                                "champions": out}, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{len(out)} champions parsed; unmatched names: {unmatched}")


if __name__ == "__main__":
    main()
