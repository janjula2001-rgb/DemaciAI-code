"""Assess every claim for one matchup (deterministic) -> data/claims/<role>/<Enemy>.assessed.json

  prepare_claims.py <role> <Enemy>

Inputs: data/claims/<role>/<Enemy>.jsonl (extracted), data/claims/_archetype/<archetype>.jsonl (if the
enemy fits), and onetricks build data turned into claims here. Adds id, weight, scope, patch_at_date and
freshness per the CLAUDE.md validity rule, using data/meta/change_log + config item_overhaul_patches.
Prints a compact listing for synthesis.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import date, timedelta

from polite_http import CONFIG, ROOT, fetch

META = ROOT / "data" / "meta"
CLAIMS = ROOT / "data" / "claims"
CHAMP = CONFIG["champion"]
TODAY = date.today().isoformat()
STABLE_AGING_DAYS = 365
VOLATILE_AGING_DAYS = 90
# Older sources (before the 13.10 durability update) stay valid for kit tips but count for less (user, 2026-10-07).
OLDER_BEFORE = CONFIG.get("older_source_before", "2023-05-17")
OLDER_WEIGHT = CONFIG.get("older_source_weight", 0.75)
RANGED_MIN_RANGE = 325


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def patch_at(day: str, patches: dict) -> str | None:
    best = None
    for p, d in patches.items():
        if d["release"] and d["release"] <= day and (best is None or d["release"] > patches[best]["release"]):
            best = p
    return best


def ability_names(champ: str) -> dict[str, str]:
    """'Q' -> 'Blinding Dart' etc. from Data Dragon champion detail."""
    ver = load_json(META / "current_patch.json")["ddragon"]
    data = json.loads(fetch(f"https://ddragon.leagueoflegends.com/cdn/{ver}/data/en_US/champion/{champ}.json",
                            "ddragon", f"champion_{champ}_{ver}.json").text)["data"][champ]
    return {"P": data["passive"]["name"], **{k: s["name"] for k, s in zip("QWER", data["spells"])}}


TOP_CARRY_CATEGORIES = {"enemy_key_abilities", "laning_1_3", "laning_3_6", "post_6", "teamfight"}


def archetypes(enemy: str, role: str) -> list[str]:
    """Role-specific archetype files: data/claims/_archetype/ranged_<role>.jsonl (top advice doesn't carry to mid)."""
    ver = load_json(META / "current_patch.json")["ddragon"]
    champs = json.loads(fetch(f"https://ddragon.leagueoflegends.com/cdn/{ver}/data/en_US/champion.json",
                              "ddragon", f"champion_{ver}.json").text)["data"]
    arch = f"ranged_{role}"
    ranged = champs[enemy]["stats"]["attackrange"] >= RANGED_MIN_RANGE
    return [arch] if ranged and (CLAIMS / "_archetype" / f"{arch}.jsonl").exists() else []


# Scripted claims get an id from their slot, not their text, so a re-capture (new percentages) or a sheet edit keeps the
# synth files' references valid; finalize_matchup then flags item texts whose numbers no longer match.
ONETRICKS_SLOTS = [("Keystones", "keystones"), ("Summoners", "summoners"), ("Start:", "start"), ("Most common early", "early"),
                   ("First completed", "first_item"), ("Boots:", "boots"), ("Most built", "items"), ("Skill max order", "skills")]
SHEET_SLOTS = [("Skill max order", "sheet_skills"), ("Runes:", "sheet_runes"), ("Build path", "sheet_build"),
               ("Summoners", "sheet_summoners"), ("Rated", "sheet_rating")]


def slot_of(claim: str, table) -> str:
    return next(slot for prefix, slot in table if claim.startswith(prefix))


def claim_id(c: dict) -> str:
    key = f"{c['source_url']}#{c['slot']}" if c.get("slot") else c["source_url"] + c["claim"]
    return hashlib.sha1(key.encode()).hexdigest()[:8]


def onetricks_claims(role: str, enemy: str) -> list[dict]:
    path = ROOT / "data" / "clean" / "onetricks" / f"{role}_{enemy}.json"
    if not path.exists():
        return []
    d = load_json(path)
    rng = d["patches"]
    base = {"type": "volatile", "source_url": d["url"], "source_type": "onetricks_data", "author": "onetricks.gg (Master+ OTPs)",
            "source_date": d["captured"], "patch": rng.split("-")[0] if rng else None, "elo_context": "master",
            "upvotes_or_signal": f"Master+ OTP games, patches {rng}; no game counts shown", "abilities": []}
    pct = lambda x: f"{x:g}%"
    out = []
    if d["keystones"]:
        ks = ", ".join(f"{k['name']} {pct(k['pct'])}" for k in d["keystones"])
        out.append({"claim": f"Keystones used by Master+ Garen OTPs: {ks}. Most common page: {', '.join(d['rune_page_shown'])}.",
                    "category": "runes"})
    if d["summoners"]:
        out.append({"claim": "Summoners: " + ", ".join(f"{' + '.join(s['spells'])} {pct(s['pct'])}" for s in d["summoners"]) + ".",
                    "category": "summoners"})
    if d["starting_items"]:
        s = d["starting_items"]
        out.append({"claim": f"Start: {' + '.join(s['items'])} ({pct(s['pct'])} of games).", "category": "starting_items"})
    if d["early_purchase_order"]:
        s = d["early_purchase_order"]
        out.append({"claim": f"Most common early purchase order: {' > '.join(s['items'])} ({pct(s['pct'])}).", "category": "first_back"})
    if d["first_item"]:
        f = d["first_item"]
        out.append({"claim": f"First completed item: {' + '.join(f['items'])} ({pct(f['pct'])}).", "category": "core_build"})
    if d["popular_boots"]:
        out.append({"claim": "Boots: " + ", ".join(f"{b['item']} {pct(b['pct'])}" for b in d["popular_boots"]) + ".",
                    "category": "core_build"})
    if d["popular_items"]:
        out.append({"claim": "Most built items: " + ", ".join(f"{b['item']} {pct(b['pct'])}" for b in d["popular_items"]) + ".",
                    "category": "situational_items"})
    lv = "; ".join(f"{'-'.join(o['order'])} ({pct(o['pct'])})" for o in d["levels_1_3"])
    out.append({"claim": f"Skill max order {' > '.join(d['skill_max_order'])}; levels 1-3: {lv}.", "category": "skill_order",
                "abilities": []})
    return [base | c | {"slot": slot_of(c["claim"], ONETRICKS_SLOTS)} for c in out]


def federals1_claims(enemy: str, role: str) -> list[dict]:
    """Federals1's matchup spreadsheet row for this enemy (Challenger OTP; rows undated)."""
    path = ROOT / "data" / "clean" / "federals1" / "sheet.json"
    if not path.exists():
        return []
    sheet = load_json(path)
    row = sheet["champions"].get(enemy)
    if not row:
        return []
    # The sheet is for Garen top; on other roles it's shown, but labelled as top-lane data.
    label = "matchup spreadsheet" if role == "top" else "top-lane matchup spreadsheet"
    base = {"source_url": sheet["source_url"], "source_type": "otp_guide", "author": f"Federals1 ({label})",
            "source_date": sheet["source_date"], "date_uncertain": True, "patch": None,
            "elo_context": sheet["elo_context"], "upvotes_or_signal": None, "abilities": []}
    out = [{"claim": f"Skill max order: {row['skill_order']}.", "category": "skill_order", "type": "volatile"},
           {"claim": "Runes: " + " | ".join(row["runes"]) + ".", "category": "runes", "type": "volatile"},
           {"claim": f"Build path: {' > '.join(row['build_path'])}.", "category": "core_build", "type": "volatile"}]
    if row["summoners"]:
        out.append({"claim": f"Summoners: {row['summoners']}.", "category": "summoners", "type": "volatile"})
    if row["difficulty_label"]:
        out.append({"claim": f"Rated '{row['difficulty_label']}'" + (" (top lane)." if role != "top" else "."), "category": "overview", "type": "volatile",  # balance verdict
                    "difficulty": row["difficulty"]})
    return [base | c | {"slot": f"{enemy}:" + slot_of(c["claim"], SHEET_SLOTS)} for c in out]


# Mechanic changes reviewed against a claim and found harmless (data/meta/reviewed_changes.json); only that exact change is excused.
_rev = META / "reviewed_changes.json"
REVIEWED = {(r["claim"], r["ability"], r["patch"]) for r in (load_json(_rev)["reviews"] if _rev.exists() else [])
            if r["verdict"] == "still_valid"}


def assess(c: dict, logs: dict, names: dict, overhaul_date: str, patches: dict) -> tuple[str, str]:
    day = c["source_date"]
    if c["type"] == "volatile":
        if day < overhaul_date:
            return "invalid", f"build/rune advice from before the item overhaul ({overhaul_date})"
        old = (date.fromisoformat(TODAY) - date.fromisoformat(day)).days > VOLATILE_AGING_DAYS
        if old:
            return "aging", f"older than {VOLATILE_AGING_DAYS} days"
        if c.get("date_uncertain"):
            return "aging", "source date is a last-update date; this part may be older"
        return "valid", ""
    for champ, log in logs.items():
        base = (log.get("kit_baseline") or {}).get("release")
        if base and day < base:
            return "invalid", f"before {champ}'s {log['kit_baseline']['kind']} in {log['kit_baseline']['patch']} ({base})"
    for ab in c.get("abilities", []):
        champ, key = ab.split(":")
        name = names.get(champ, {}).get(key)
        changes = logs.get(champ, {}).get("last_mechanic_change_by_ability", {})
        hit = next((v for sec, v in changes.items() if name and (sec == name or sec.startswith(name + " "))), None)
        if hit and hit.get("release") and hit["release"] > day and (c.get("id"), ab, hit["patch"]) not in REVIEWED:
            return "possibly_outdated", f"{champ} {key} ({name}) mechanic change in {hit['patch']}: {hit['text'][:120]}"
    if day < OLDER_BEFORE:
        return "aging", f"older source: before the durability update (13.10, {OLDER_BEFORE}), so it counts for less"
    old = (date.fromisoformat(TODAY) - date.fromisoformat(day)).days > STABLE_AGING_DAYS
    if old:
        return "aging", f"older than {STABLE_AGING_DAYS} days"
    if c.get("date_uncertain"):
        return "aging", "source date is a last-update date; the note itself may be older"
    return "valid", ""


def main():
    role, enemy = sys.argv[1], sys.argv[2]  # enemy "_general": shared Garen game plan (data/claims/_general.jsonl)
    general = enemy == "_general"
    weights = CONFIG["source_weights"]
    patches = load_json(META / "patches.json")
    overhaul = max(CONFIG["item_overhaul_patches"], key=lambda p: tuple(map(int, p.split("."))))
    overhaul_date = patches[overhaul]["release"]
    champs = (CHAMP,) if general else (CHAMP, enemy)
    logs = {ch: load_json(META / "change_log" / f"{ch}.json") for ch in champs}
    names = {ch: ability_names(ch) for ch in champs}

    claims = []
    rdir = CLAIMS if role == "-" else CLAIMS / role  # role "-": shared plan; "<role>/_general": role-only plan
    src = rdir / f"{enemy}.jsonl"
    scope = "general" if general else "matchup"
    claims += [json.loads(l) | {"scope": scope} for l in src.read_text(encoding="utf-8").splitlines() if l.strip()]
    for arch in ([] if general else archetypes(enemy, role)):
        p = CLAIMS / "_archetype" / f"{arch}.jsonl"
        claims += [json.loads(l) | {"scope": f"archetype:{arch}"} for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    top_src = CLAIMS / "top" / f"{enemy}.jsonl"
    if not general and role != "top" and top_src.exists():
        # Kit-based advice about the enemy carries across lanes; wave/build advice from top does not.
        claims += [c | {"scope": "top_lane"} for c in map(json.loads, filter(str.strip, top_src.read_text(encoding="utf-8").splitlines()))
                   if c["type"] == "stable" and c["category"] in TOP_CARRY_CATEGORIES]
    if not general:
        claims += [c | {"scope": "matchup"} for c in onetricks_claims(role, enemy)]
        claims += [c | {"scope": "matchup"} for c in federals1_claims(enemy, role)]

    for c in claims:
        c["id"] = claim_id(c)
        c["weight"] = round(weights.get(c["source_type"], 0.3) * (OLDER_WEIGHT if c["source_date"] < OLDER_BEFORE else 1), 2)
        c["patch_at_date"] = patch_at(c["source_date"], patches)
        c["freshness"], c["freshness_reason"] = assess(c, logs, names, overhaul_date, patches)

    out = {"role": role, "enemy": enemy, "assessed_at": TODAY, "overhaul_cutoff": {"patch": overhaul, "date": overhaul_date},
           "ability_names": names,
           "kit": {ch: {k: logs[ch].get(k) for k in ("kit_baseline", "last_mechanic_change")} for ch in logs},
           "claims": claims}
    dest = rdir / f"{enemy}.assessed.json"
    dest.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")

    counts = {}
    for c in claims:
        counts[c["freshness"]] = counts.get(c["freshness"], 0) + 1
    print(f"{enemy}: {len(claims)} claims {counts}; archetypes {[] if general else archetypes(enemy, role)}; overhaul cutoff {overhaul} ({overhaul_date})")
    for c in sorted(claims, key=lambda c: c["category"]):
        tag = "" if c["scope"] == "matchup" else f" [{c['scope']}]"
        print(f"{c['id']} {c['category']:<18} {c['freshness']:<17} {c['author'][:22]:<22} {c['source_date']} w{c['weight']}{tag} | {c['claim'][:150]}"
              + (f"\n{'':9}-> {c['freshness_reason']}" if c["freshness"] in ("invalid", "possibly_outdated") else ""))


if __name__ == "__main__":
    main()
