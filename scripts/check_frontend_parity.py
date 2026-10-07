"""Parity check: does the web app show every piece of advice the data has (what the Streamlit app showed)?

  check_frontend_parity.py [--base http://localhost:5173]

For every matchup in frontend/public/data/index.json it computes, from the JSON, how many advice cards and
conflict cards the page must render, then counts [data-advice] / [data-conflict] in the live page.
Build advice that only restates the one-trick data or Federals1's sheet sits in a collapsed section (the same
data is drawn as icons), so the check opens that section before counting. Also checks the outdated-claims
count and that the cheat sheet's keystone matches the capture. The dev server must be running.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "frontend" / "public" / "data"
BASE = sys.argv[sys.argv.index("--base") + 1] if "--base" in sys.argv else "http://localhost:5173"
BUILD = ["runes", "summoners", "starting_items", "skill_order", "first_back", "core_build", "situational_items"]
OTHER = ["overview", "enemy_key_abilities", "laning_1_3", "laning_3_6", "wave_management", "post_6", "midgame", "jungle", "teamfight"]


def load(p: Path):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def expected(role: str, enemy: str) -> dict:
    m = load(DATA / role / f"{enemy}.json")
    rp = load(DATA / role / "_general.json") or {}
    sp = load(DATA / "_general.json") or {}
    n = len(m.get("key_tips") or [])
    for c in BUILD + OTHER:
        n += len(m.get(c, [])) + len(rp.get(c, [])) + len(sp.get(c, []))
    cap = load(DATA / "onetricks" / f"{role}_{enemy}.json")
    return {"advice": n, "conflicts": len(m["conflicts"]) + len(rp.get("conflicts", [])), "outdated": len(m["outdated"]),
            "keystone": cap["keystones"][0]["name"] if cap else None}


def main():
    index = load(DATA / "index.json")
    bad = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1920, "height": 1080}, reduced_motion="reduce")
        for role, rows in index["roles"].items():
            for r in rows:
                exp = expected(role, r["id"])
                page.goto(f"{BASE}/{role}/{r['id']}")
                page.wait_for_selector("#about", timeout=15000)
                toggle = page.get_by_text("The build data above as text, with its sources")
                if toggle.count():
                    toggle.first.click()
                    page.wait_for_timeout(150)
                got = {
                    "advice": page.locator("[data-advice]").count(),
                    "conflicts": page.locator("[data-conflict]").count(),
                    "outdated": int(page.get_by_text("Left out as outdated").count() and
                                    page.locator("#about").inner_text().split("Left out as outdated")[1].split()[0]) if exp["outdated"] else 0,
                    "keystone": exp["keystone"] and (exp["keystone"] if page.get_by_text(exp["keystone"]).count() else "missing"),
                }
                diffs = {k: (exp[k], got[k]) for k in exp if exp[k] != got[k]}
                if diffs:
                    bad.append((f"{role}/{r['id']}", diffs))
        browser.close()
    total = sum(len(v) for v in index["roles"].values())
    print(f"checked {total} pages; mismatches: {len(bad)}")
    for page_id, d in bad:
        print(f"  {page_id}: " + ", ".join(f"{k} expected {e} got {g}" for k, (e, g) in d.items()))


if __name__ == "__main__":
    main()
