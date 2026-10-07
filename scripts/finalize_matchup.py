"""Merge the LLM synthesis with the deterministic claim assessment -> data/matchups/<role>/<Enemy>.json

  finalize_matchup.py <role> <Enemy>

Inputs: <Enemy>.synth.json (summary, difficulty, grouped items citing claim ids, conflicts),
data/claims/<role>/<Enemy>.assessed.json, data/clean/stats/<role>_<Enemy>.json.
Per item: freshness = best status among its non-invalid claims; confidence from source strength
(archetype-only items are capped at low, per CLAUDE.md); source references attached.
Also records which items/runes the matchup mentions, for the app's Garen-relevant freshness check.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date

from polite_http import ROOT

META = ROOT / "data" / "meta"
RANK = {"valid": 0, "aging": 1, "possibly_outdated": 2, "invalid": 3}
CATEGORIES = ["overview", "runes", "summoners", "starting_items", "first_back", "core_build", "situational_items",
              "skill_order", "laning_1_3", "laning_3_6", "post_6", "wave_management", "jungle", "midgame",
              "teamfight", "enemy_key_abilities"]


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def source_ref(c: dict) -> dict:
    return {k: c.get(k) for k in ("id", "author", "source_url", "source_date", "source_type", "elo_context",
                                  "freshness", "freshness_reason", "scope", "claim", "abilities", "type", "category")}


def confidence(claims: list[dict], freshness: str) -> str:
    if all(c["scope"].startswith("archetype") for c in claims):
        return "low"
    strong = {c["author"].split(" (")[0] for c in claims if c["weight"] >= 0.9}  # same person = one source
    if freshness == "possibly_outdated" or not strong:
        return "low"
    if len(strong) >= 2 and freshness == "valid":
        return "high"
    return "medium"


PCT = r"(?<![\d.])(\d+(?:\.\d+)?)%"  # whole percentages, so 48.0% is not read as 0%


def numbers_out_of_sync(text: str, claims: list[dict]) -> list[str]:
    """Percentages in a synth item's text that no longer match the scripted claims it cites (after a re-capture).
    Only checked when the item cites scripted data (onetricks / sheet); a text percentage matches if any cited number
    rounds to it (texts round 65.9% to 66%)."""
    if not any(c.get("slot") for c in claims):
        return []
    have = [float(x) for c in claims for x in re.findall(PCT, c["claim"])]
    return [f"{n}%" for n in re.findall(PCT, text) if not any(abs(float(n) - h) < 1.0 for h in have)]


def main():
    role, enemy = sys.argv[1], sys.argv[2]
    general = enemy == "_general"  # shared Garen game plan, shown under every matchup
    mdir = ROOT / "data" / "matchups" / ("" if role == "-" else role)  # "-": shared plan; "mid/_general": mid-only plan
    synth = load(mdir / f"{enemy}.synth.json")
    assessed = load(ROOT / "data" / "claims" / (f"{enemy}.assessed.json" if role == "-" else f"{role}/{enemy}.assessed.json"))
    by_id = {c["id"]: c for c in assessed["claims"]}
    stats_path = ROOT / "data" / "clean" / "stats" / f"{role}_{enemy}.json"
    problems, used = [], set()

    def resolve(ids: list[str], where: str) -> list[dict]:
        out = []
        for i in ids:
            if i not in by_id:
                problems.append(f"{where}: unknown claim id {i}")
            elif by_id[i]["freshness"] == "invalid":
                problems.append(f"{where}: claim {i} is invalid ({by_id[i]['freshness_reason']}) - dropped")
            else:
                out.append(by_id[i])
                used.add(i)
        return out

    def build_item(it: dict, where: str) -> dict | None:
        claims = resolve(it["claims"], where)
        if not claims:
            problems.append(f"{where}: item dropped, no valid claims: {it['text'][:60]}")
            return None
        fresh = min((c["freshness"] for c in claims), key=RANK.get)
        stale_numbers = numbers_out_of_sync(it["text"], claims)
        if stale_numbers:
            problems.append(f"{where}: numbers out of sync with the current data ({', '.join(stale_numbers)}): {it['text'][:60]}")
        types = {c["type"] for c in claims}
        return {"text": it["text"], "weight": round(sum(c["weight"] for c in claims), 2),
                "type": types.pop() if len(types) == 1 else "mixed",
                "confidence": confidence(claims, fresh), "freshness": fresh,
                "archetype_only": all(c["scope"].startswith("archetype") for c in claims),
                "top_lane_only": all(c["scope"] == "top_lane" for c in claims),
                "stale_numbers": stale_numbers,
                "sources": [source_ref(c) for c in claims]}

    sections = {cat: [x for it in synth["sections"].get(cat, []) if (x := build_item(it, cat))] for cat in CATEGORIES}
    # Cheat-sheet tips: up to 3 short must-knows, each citing the same claims as the full advice it condenses.
    key_tips = [x for it in synth.get("key_tips", [])[:3] if (x := build_item(it, "key_tips"))]

    conflicts = []
    for cf in synth.get("conflicts", []):
        sides = []
        for s in cf["sides"]:
            claims = resolve(s["claims"], f"conflict {cf['topic']}")
            if claims:
                sides.append({"position": s["position"], "weight": round(sum(c["weight"] for c in claims), 2),
                              "sources": [source_ref(c) for c in claims]})
        if len(sides) >= 2:
            conflicts.append({"topic": cf["topic"], "sides": sides})

    unused = [c for c in assessed["claims"] if c["id"] not in used and c["freshness"] != "invalid"]
    problems += [f"unused non-invalid claim {c['id']} ({c['category']}): {c['claim'][:70]}" for c in unused]

    items_sr = load(META / "items_sr.json")
    runes = load(META / "runes.json")["by_name"]
    text = " ".join(c["claim"] for c in assessed["claims"] if c["freshness"] != "invalid")
    items_ref = sorted({v["name"] for v in items_sr.values() if re.search(rf"\b{re.escape(v['name'])}\b", text)})
    runes_ref = sorted({n for n in runes if re.search(rf"\b{re.escape(n)}\b", text)})

    # Summary / difficulty basis percentages must still appear in the page's claims or its Platinum+ stats.
    stats = load(stats_path) if stats_path.exists() else None
    page_text = text + " " + json.dumps(stats or {})
    have = [float(x) * k for x in re.findall(r"\d+(?:\.\d+)?", page_text) for k in (1, 100) if float(x) * k <= 100]
    summary_stale = {f: [f"{n}%" for n in re.findall(PCT, synth[f]) if not any(abs(float(n) - h) < 1.0 for h in have)]
                     for f in ("summary", "difficulty_basis")}
    summary_stale = {f: v for f, v in summary_stale.items() if v}
    problems += [f"{f}: numbers out of sync with the current data ({', '.join(v)})" for f, v in summary_stale.items()]

    patch = load(META / "current_patch.json")
    out = {
        "enemy": enemy, "role": role, "difficulty": synth["difficulty"], "difficulty_basis": synth["difficulty_basis"],
        "summary": synth["summary"], "key_tips": key_tips, **{c: sections[c] for c in CATEGORIES},
        "conflicts": conflicts,
        "outdated": [source_ref(c) for c in assessed["claims"] if c["freshness"] == "invalid"],
        "stats": stats, "summary_stale_numbers": summary_stale,
        "last_kit_change": assessed["kit"],
        "ability_names": assessed["ability_names"],
        "references": {"items": items_ref, "runes": runes_ref,
                       "sources": sorted({c["source_url"] for c in assessed["claims"]})},
        "generated_at_patch": patch["patch"], "generated_at_patch_display": patch["display"],
        "generated_at_date": date.today().isoformat(),
    }
    (mdir / f"{enemy}.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    n = sum(len(v) for v in sections.values())
    conf = {}
    for v in sections.values():
        for it in v:
            conf[it["confidence"]] = conf.get(it["confidence"], 0) + 1
    print(f"{enemy}: {n} items {conf}, {len(conflicts)} conflicts, {len(out['outdated'])} outdated claims shown separately; "
          f"items referenced: {len(items_ref)}, runes: {len(runes_ref)}")
    for p in problems:
        print("  !", p)


if __name__ == "__main__":
    main()
