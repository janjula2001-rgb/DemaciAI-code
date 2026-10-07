"""Screenshots of the web app for review (Playwright, Chromium). The dev server must be running (npm run dev).

  screenshot_frontend.py [shot ...] [--base http://localhost:5173] [--all-matchups]

Shots go to data/screens/<name>-<width>.png at 1920x1080 and 1366x768, plus a reduced-motion run.
--all-matchups opens every matchup in data/index.json and reports console errors and failed requests
(including any request that leaves localhost: the app must never hotlink).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "screens"
BASE = sys.argv[sys.argv.index("--base") + 1] if "--base" in sys.argv else "http://localhost:5173"
SIZES = [(1920, 1080), (1366, 768)]

# name -> (path, actions after load)
SHOTS = {
    "home": ("/", [("wait", 2600)]),
    "home-hover": ("/", [("wait", 2600), ("hover", "a[href='/top/Darius']"), ("wait", 500)]),
    "home-search": ("/", [("wait", 2200), ("press", "/"), ("type", "dar"), ("wait", 700)]),
    "home-mid": ("/?role=mid", [("wait", 2600)]),
    "matchup": ("/top/Darius", [("wait", 2500)]),
    "matchup-scrolled": ("/top/Darius", [("wait", 2500), ("scroll", 520), ("wait", 600)]),
    # the VS intro, frame by frame (screenshots take ~100 ms, so times are approximate)
    # the VS intro, frame by frame at 0.2x speed (debug hook in VsIntro.tsx)
    "intro": ("/", [("wait", 2600), ("eval", "window.__introSlowmo = 0.2"), ("click", "a[href='/top/Darius']"),
                    ("wait", 500), ("shot", "a"), ("wait", 700), ("shot", "b"), ("wait", 400), ("shot", "c"),
                    ("wait", 900), ("shot", "d"), ("wait", 1200), ("shot", "e"), ("wait", 3000), ("shot", "f")]),
    "drawer": ("/top/Darius", [("wait", 2500), ("click", r"text=/\d+ sources?/"), ("wait", 700)]),
}


def act(page, actions, prefix=""):
    for kind, arg in actions:
        if kind == "wait":
            page.wait_for_timeout(arg)
        elif kind == "hover":
            page.hover(arg)
        elif kind == "press":
            page.keyboard.press(arg)
        elif kind == "type":
            page.keyboard.type(arg, delay=60)
        elif kind == "click":
            page.locator(arg).first.click()
        elif kind == "eval":
            page.evaluate(arg)
        elif kind == "scroll":
            page.mouse.wheel(0, arg)
        elif kind == "shot":
            page.screenshot(path=OUT / f"{prefix}-{arg}.png")
            print("shot", f"{prefix}-{arg}.png")


def shots(names):
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for motion in ("no-preference", "reduce"):
            for w, h in SIZES if motion == "no-preference" else SIZES[:1]:
                ctx = browser.new_context(viewport={"width": w, "height": h}, reduced_motion=motion)
                page = ctx.new_page()
                errors = []
                page.on("console", lambda m: m.type == "error" and errors.append(m.text))
                page.on("pageerror", lambda e: errors.append(str(e)))
                for name in names:
                    path, actions = SHOTS[name]
                    page.goto(BASE + path)
                    suffix = f"{w}" + ("-reduced" if motion == "reduce" else "")
                    act(page, actions, prefix=f"{name}-{suffix}")
                    page.screenshot(path=OUT / f"{name}-{suffix}.png")
                    print("shot", f"{name}-{suffix}.png")
                if errors:
                    print("console errors:", *errors[:10], sep="\n  ")
                ctx.close()
        browser.close()


def all_matchups():
    index = json.loads((ROOT / "frontend" / "public" / "data" / "index.json").read_text(encoding="utf-8"))
    problems = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        current = {"errors": []}
        page.on("console", lambda m: m.type == "error" and current["errors"].append(m.text))
        page.on("pageerror", lambda e: current["errors"].append(str(e)))
        page.on("requestfailed", lambda r: current["errors"].append(f"failed {r.url}"))
        page.on("request", lambda r: not r.url.startswith(BASE) and not r.url.startswith("data:")
                and current["errors"].append(f"external request {r.url}"))
        for role, rows in index["roles"].items():
            for r in rows:
                current["errors"] = []
                page.goto(f"{BASE}/{role}/{r['id']}")
                page.wait_for_timeout(1200)
                if current["errors"]:
                    problems.append((f"{role}/{r['id']}", current["errors"][:5]))
        browser.close()
    print(f"checked {sum(len(v) for v in index['roles'].values())} matchups; problems: {len(problems)}")
    for page_id, errs in problems:
        print(" ", page_id, errs)


if __name__ == "__main__":
    if "--all-matchups" in sys.argv:
        all_matchups()
    else:
        names = [a for a in sys.argv[1:] if a in SHOTS] or list(SHOTS)
        shots(names)
