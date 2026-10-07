"""Patch refresh (Phase 5): redo everything deterministic, then write a short to-do for the parts that need Claude.

  refresh_patch.py [--since <patch>] [--offline] [--no-stats]

1. Meta: fetch_ddragon, build_change_log --refresh, detect_item_overhauls, parse_federals1_sheet --refresh
   (skipped with --offline).
2. check_freshness against the patch the data was built on (or --since), so kit/item/rune changes since then are found.
3. Re-assess + re-finalize every matchup and both general plans. This is local and cheap; claims whose ability got a
   mechanic change become possibly_outdated on their own, and sources that aged are re-labelled.
4. Platinum+ stats are re-fetched for every matchup when the patch changed (skip with --no-stats).
5. Before/after diff of every advice item's freshness.
7. export_frontend.py, so the web app shows the refreshed data.
6. data/meta/refresh_todo.md (+ refresh_report.json): only what needs Claude, ready to paste into a session:
   onetricks re-captures (capture patch older than current), advice that turned possibly_outdated/invalid,
   kit changes that touch stored advice, changed items/runes we reference, new OTP videos, sheet edits, overhauls.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import date

from polite_http import ROOT

META = ROOT / "data" / "meta"
MATCHUPS = ROOT / "data" / "matchups"
OFFLINE = "--offline" in sys.argv
PY = sys.executable
TIP_SECTIONS = ("laning_1_3", "laning_3_6", "post_6", "wave_management", "enemy_key_abilities", "midgame", "teamfight", "jungle")


def pkey(p: str) -> tuple:
    return tuple(int(x) for x in p.split(".")[:2])


def run(*args: str) -> str:
    r = subprocess.run([PY, *args], cwd=ROOT / "scripts", capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        raise SystemExit(f"FAILED: {' '.join(args)}\n{r.stdout[-1500:]}\n{r.stderr[-1500:]}")
    return r.stdout


def targets() -> list[tuple[str, str]]:
    out = []
    for role in ("top", "mid"):
        for p in sorted((MATCHUPS / role).glob("*.synth.json")):
            out.append((role, p.name[:-len(".synth.json")]))
    out.append(("-", "_general"))
    return out


def final_path(role: str, enemy: str):
    return MATCHUPS / ("" if role == "-" else role) / f"{enemy}.json"


def snapshot() -> dict:
    """{(role, enemy, section, text): freshness} for every advice item."""
    snap = {}
    for role, enemy in targets():
        p = final_path(role, enemy)
        if not p.exists():
            continue
        m = json.loads(p.read_text(encoding="utf-8"))
        for sec, items in m.items():
            if isinstance(items, list) and items and isinstance(items[0], dict) and "text" in items[0] and "freshness" in items[0]:
                for it in items:
                    snap[(role, enemy, sec, it["text"])] = it["freshness"]
    return snap


def built_patch() -> str:
    pats = [json.loads(final_path(r, e).read_text(encoding="utf-8"))["generated_at_patch"]
            for r, e in targets() if r != "-" and final_path(r, e).exists()]
    return min(pats, key=pkey)


def stale_captures(current: str) -> list[str]:
    """Matchups whose onetricks capture was taken before the current patch was released.
    (A fresh capture can still end at an older patch when nobody played the matchup yet, so the range isn't used.)"""
    patches = json.loads((META / "patches.json").read_text(encoding="utf-8"))
    released = (patches.get(current) or {}).get("release") or "9999"
    out = []
    for role, enemy in targets():
        if role == "-" or enemy.startswith("_"):
            continue
        p = ROOT / "data" / "clean" / "onetricks" / f"{role}_{enemy}.json"
        if not p.exists():
            out.append(f"{role}/{enemy} (no capture)")
            continue
        if json.loads(p.read_text(encoding="utf-8"))["captured"] < released:
            out.append(f"{role}/{enemy}")
    return out


def main():
    since = sys.argv[sys.argv.index("--since") + 1] if "--since" in sys.argv else None
    built = since or built_patch()
    before = snapshot()
    log = []

    if not OFFLINE:
        for step in (["fetch_ddragon.py"], ["build_change_log.py", "--refresh"], ["detect_item_overhauls.py"],
                     ["parse_federals1_sheet.py", "--refresh"]):
            run(*step)
            log.append(" ".join(step))
    current = json.loads((META / "current_patch.json").read_text(encoding="utf-8"))["patch"]
    new_patch = pkey(current) > pkey(built)

    run("check_freshness.py", "--since", built, *(["--offline"] if OFFLINE else []))
    log.append(f"check_freshness.py --since {built}")
    report = json.loads((META / "freshness_report.json").read_text(encoding="utf-8"))

    if new_patch and not OFFLINE and "--no-stats" not in sys.argv:
        for role in ("top", "mid"):
            enemies = [e for r, e in targets() if r == role]
            run("fetch_stats.py", role, *enemies, "--refresh")
            log.append(f"fetch_stats.py {role} ({len(enemies)} matchups) --refresh")

    for role, enemy in targets():
        run("prepare_claims.py", role, enemy)
        run("finalize_matchup.py", role, enemy)
    log.append(f"re-assessed + finalized {len(targets())} pages")
    after = snapshot()

    changed = [(k, before.get(k), v) for k, v in after.items() if before.get(k) not in (None, v)]
    dropped = [k for k in before if k not in after]
    worse = [c for c in changed if c[2] in ("possibly_outdated", "invalid")]

    todo = []
    stale = stale_captures(current)
    if stale:
        todo.append(("Re-capture onetricks builds (built-in browser, `scripts/onetricks_batch_capture.js`, 5 per call), then "
                     "`split_onetricks_batch.py <role>`, `parse_onetricks.py`, `prepare_claims` + `finalize_matchup`; "
                     "update the build/rune/skill-order item texts in each synth if the percentages moved",
                     stale))
    by_page = {}
    for (role, enemy, sec, text), old, new in worse:
        by_page.setdefault(f"{role}/{enemy}", []).append(f"[{sec}] {old} -> {new}: {text[:90]}")
    for role, enemy, sec, text in dropped:
        by_page.setdefault(f"{role}/{enemy}", []).append(f"[{sec}] dropped (no valid claims left): {text[:90]}")
    if by_page:
        todo.append(("Advice that turned outdated: find newer sources (YouTube batch, 45 s pacing) or reword the synth items",
                     [f"{page}: " + " | ".join(v) for page, v in sorted(by_page.items())]))
    out_of_sync = []
    for role, enemy in targets():
        p = final_path(role, enemy)
        if p.exists():
            m = json.loads(p.read_text(encoding="utf-8"))
            out_of_sync += [f"{role}/{enemy} [{f}] {', '.join(v)} not in the page's claims or stats"
                            for f, v in (m.get("summary_stale_numbers") or {}).items()]
            for sec, items in m.items():
                if isinstance(items, list):
                    out_of_sync += [f"{role}/{enemy} [{sec}] {', '.join(it['stale_numbers'])} not in cited data: {it['text'][:90]}"
                                    for it in items if isinstance(it, dict) and it.get("stale_numbers")]
    if out_of_sync:
        todo.append(("Item/summary texts whose percentages don't match the claims they cite (re-captured data moved, or the number "
                     "comes from an uncited slot): update the text or add the claim id in the synth", out_of_sync))
    kinds = {"kit_mechanic": "Kit changes touching stored advice", "kit_rework": "Reworks (whole matchup needs new sources)",
             "item": "Changed items we reference", "rune": "Changed runes we reference", "item_overhaul": "Item overhaul",
             "new_video": "New OTP videos to consider", "source_changed": "Source edits"}
    for kind, label in kinds.items():
        fs = [f for f in report["findings"] if f["kind"] == kind and (kind not in ("kit_mechanic",) or any(a.get("sections") for a in f["affects"]))]
        if fs:
            todo.append((label, [f"{f['what']} → {f['todo']}" for f in fs]))

    out = {"refreshed_at": date.today().isoformat(), "built_on": built, "current_patch": current, "new_patch": new_patch,
           "steps": log, "freshness_changes": len(changed), "dropped_items": len(dropped),
           "todo": [{"task": t, "items": items} for t, items in todo]}
    (META / "refresh_report.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    md = [f"# Patch refresh to-do ({out['refreshed_at']})", "",
          f"Data built on {built}, current patch {current}" + (" (**new patch**)" if new_patch else " (no new patch)") + ".",
          "Done automatically: " + "; ".join(log) + ".",
          f"Advice items whose freshness changed: {len(changed)} ({len(worse)} got worse), dropped: {len(dropped)}.", ""]
    if not todo:
        md.append("Nothing needs Claude right now.")
    for i, (task, items) in enumerate(todo, 1):
        md.append(f"## {i}. {task}")
        md += [f"- {x}" for x in items[:60]]
        if len(items) > 60:
            md.append(f"- ... and {len(items) - 60} more (see refresh_report.json)")
        md.append("")
    md.append("Paste this file into a Claude Code session and work through it top to bottom, one section per session.")
    (META / "refresh_todo.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    run("export_frontend.py")  # the web app reads frontend/public/data/
    print(f"built on {built}, current {current}, new patch: {new_patch}; {len(changed)} freshness changes, {len(dropped)} dropped; "
          f"{len(todo)} to-do sections -> data/meta/refresh_todo.md")


if __name__ == "__main__":
    main()
