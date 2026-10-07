"""Copy the data the frontend reads into frontend/public/data/ (schema unchanged) and build its index.

  export_frontend.py

Copies data/matchups/<role>/*.json, both _general.json plans, data/clean/onetricks/*.json,
data/clean/federals1/sheet.json and the freshness report + refresh to-do. Writes index.json:
main champion + theme, current patch, and per role a list of matchups for the home grid
(name, difficulty, Platinum+ win rates, whether it has cheat-sheet tips, and a freshness dot).
refresh_patch.py runs this as its last step.
"""
from __future__ import annotations

import json
import shutil
from datetime import date

from polite_http import CONFIG, ROOT

DATA = ROOT / "data"
OUT = ROOT / "frontend" / "public" / "data"
ROLES = CONFIG["roles"]
TIP_CATS = ["laning_1_3", "laning_3_6", "post_6", "wave_management", "jungle", "midgame", "teamfight", "enemy_key_abilities"]


def load(p):
    return json.loads(p.read_text(encoding="utf-8"))


def freshness_dot(m: dict, capture: dict | None, patch_release: str) -> dict:
    """green: current build data and little outdated advice; amber: some; orange: a lot, or the build capture
    predates the current patch."""
    items = [it for c in TIP_CATS for it in m.get(c, [])]
    outdated = sum(it["freshness"] == "possibly_outdated" for it in items)
    share = outdated / len(items) if items else 0.0
    stale = capture is None or capture["captured"] < patch_release
    level = "orange" if stale or share >= 0.35 else "amber" if share >= 0.15 else "green"
    why = []
    if stale:
        why.append("build data is from before the current patch" if capture else "no build data captured")
    if outdated:
        why.append(f"{outdated} of {len(items)} tips possibly outdated")
    return {"level": level, "why": "; ".join(why) or "current"}


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "onetricks").mkdir(parents=True)
    champs = load(DATA / "meta" / "champions.json")
    patch = load(DATA / "meta" / "current_patch.json")
    release = (load(DATA / "meta" / "patches.json").get(patch["patch"]) or {}).get("release", "0000")

    index = {"main_champion": CONFIG["champion"], "theme": CONFIG.get("ui_theme", "demacia"), "patch": patch,
             "exported": date.today().isoformat(), "roles": {}}
    for role in ROLES:
        (OUT / role).mkdir(parents=True)
        rows = []
        for p in sorted((DATA / "matchups" / role).glob("*.json")):
            if p.name.endswith(".synth.json"):
                continue
            shutil.copy2(p, OUT / role / p.name)
            if p.name.startswith("_"):
                continue
            m = load(p)
            cap_path = DATA / "clean" / "onetricks" / f"{role}_{p.stem}.json"
            capture = load(cap_path) if cap_path.exists() else None
            stats = m.get("stats") or {}
            rows.append({"id": p.stem, "name": champs.get(p.stem, {}).get("name", p.stem), "difficulty": m["difficulty"],
                         "win_rate": {k: (stats.get(k) or {}).get("win_rate") for k in ("ugg", "lolalytics")},
                         "games": {k: (stats.get(k) or {}).get("games") for k in ("ugg", "lolalytics")},
                         "small_sample": bool(stats.get("small_sample")), "has_tips": bool(m.get("key_tips")),
                         "freshness": freshness_dot(m, capture, release)})
        index["roles"][role] = rows
    shutil.copy2(DATA / "matchups" / "_general.json", OUT / "_general.json")
    for p in (DATA / "clean" / "onetricks").glob("*.json"):
        shutil.copy2(p, OUT / "onetricks" / p.name)
    shutil.copy2(DATA / "clean" / "federals1" / "sheet.json", OUT / "federals1_sheet.json")
    for name in ("freshness_report.json", "refresh_todo.md", "current_patch.json"):
        if (DATA / "meta" / name).exists():
            shutil.copy2(DATA / "meta" / name, OUT / name)
    (OUT / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    n = sum(len(v) for v in index["roles"].values())
    dots = {}
    for v in index["roles"].values():
        for r in v:
            dots[r["freshness"]["level"]] = dots.get(r["freshness"]["level"], 0) + 1
    print(f"exported {n} matchups to {OUT} (freshness dots: {dots})")


if __name__ == "__main__":
    main()
