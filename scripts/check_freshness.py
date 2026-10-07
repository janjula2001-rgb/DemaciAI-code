"""Garen-focused freshness check -> data/meta/freshness_report.json

  check_freshness.py [--since <patch>] [--offline]

Compares what the matchup files were built on with what is current and reports only what matters
for Garen: his own kit changes, changes to items/runes the matchups reference, kit changes of enemies
we have matchups for, item-system overhauls, new videos from OTP creators, and claims that aged.
Every finding names the affected matchups/sections and a to-do line to paste into a Claude Code session.
--since 16.17 pretends the data was built on 16.17 (to test the check without waiting for a patch).
--offline skips network calls (uses cached Data Dragon / wiki / YouTube data).
"""
from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import date

from polite_http import CONFIG, ROOT, fetch

META = ROOT / "data" / "meta"
MATCHUPS = ROOT / "data" / "matchups"
CHAMP = CONFIG["champion"]
OFFLINE = "--offline" in sys.argv
LETTER_SECTIONS = {"Q": ["laning_1_3", "laning_3_6", "post_6", "enemy_key_abilities"],
                   "W": ["laning_1_3", "laning_3_6", "post_6", "enemy_key_abilities"],
                   "E": ["laning_1_3", "laning_3_6", "post_6", "skill_order"],
                   "R": ["post_6", "teamfight"], "P": ["laning_3_6", "wave_management"]}
ITEM_SECTIONS = ["starting_items", "first_back", "core_build", "situational_items"]


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def pkey(p: str) -> tuple:
    return tuple(int(x) for x in p.split(".")[:2])


def ddragon_version(patch: str) -> str | None:
    versions = json.loads(fetch(CONFIG["sources"]["data_dragon"]["versions"], "ddragon", "versions.json",
                                refresh=not OFFLINE).text)
    return next((v for v in versions if pkey(v) == pkey(patch) and v.count(".") == 2), None)


def dd(kind: str, version: str):
    url = CONFIG["sources"]["data_dragon"][kind].format(patch=version)
    return json.loads(fetch(url, "ddragon", f"{'item' if kind == 'items' else kind}_{version}.json").text)


def matchup_files() -> list[dict]:
    files = [p for p in sorted(MATCHUPS.glob("*/*.json")) if not p.name.endswith(".synth.json")]
    general = MATCHUPS / "_general.json"  # shared game plan: affected by Garen/item/rune changes too
    return [load(p) for p in files + ([general] if general.exists() else [])]


def sections_using(m: dict, pred) -> list[str]:
    cats = []
    for cat, items in m.items():
        if isinstance(items, list) and items and isinstance(items[0], dict) and "sources" in items[0]:
            if any(pred(it) for it in items):
                cats.append(cat)
    return cats


def finding(kind, severity, what, detail, affects, todo):
    return {"kind": kind, "severity": severity, "what": what, "detail": detail, "affects": affects, "todo": todo}


def kit_findings(champ: str, since: tuple, matchups: list[dict], is_garen: bool) -> list[dict]:
    """One finding per (patch, ability, kind); affected sections = those citing a claim about that ability."""
    log = load(META / "change_log" / f"{champ}.json")
    targets = matchups if is_garen else [m for m in matchups if m["enemy"] == champ]
    grouped = {}
    for e in log["entries"]:
        if tuple(e["key"]) <= since:
            continue
        for c in e["changes"]:
            if c["kind"] in ("mechanic", "number", "rework", "ambiguous"):
                section = "whole kit" if c["kind"] == "rework" else c["section"]
                grouped.setdefault((e["patch"], section, c["kind"]), []).append(c["text"])
    out = []
    for (patch, section, kind), lines in grouped.items():
        affects = []
        for m in targets:
            names = m.get("ability_names", {}).get(champ, {})
            letter = next((k for k, n in names.items() if section == n or section.startswith(n + " ")), None)
            tag = f"{champ}:{letter}" if letter else None
            secs = sections_using(m, lambda it: tag is not None and any(tag in (src.get("abilities") or []) for src in it["sources"]))
            if kind == "rework":
                secs = [c for c in m if isinstance(m[c], list) and m[c] and isinstance(m[c][0], dict) and "sources" in m[c][0]]
            affects.append({"matchup": f"{m['role']}/{m['enemy']}", "ability": letter, "sections": secs})
        sev = {"rework": "high", "mechanic": "high", "ambiguous": "medium", "number": "low"}[kind]
        if kind == "mechanic" and not any(a["sections"] for a in affects):
            sev = "medium"  # mechanic change, but no stored advice depends on that ability
        who = "Garen" if is_garen else champ
        out.append(finding(f"kit_{kind}", sev, f"{who} {section} ({kind}, {len(lines)} line(s)) in {patch}",
                           " | ".join(lines), affects,
                           f"Re-check {who}'s {section} {kind} change in {patch}; affected: " +
                           (", ".join(f"{a['matchup']} [{', '.join(a['sections'])}]" for a in affects if a["sections"]) or
                            "no stored advice cites this ability")))
    return out


def item_findings(old_v: str, new_v: str, matchups: list[dict]) -> list[dict]:
    old, new = dd("items", old_v)["data"], dd("items", new_v)["data"]
    referenced = {}
    for m in matchups:
        for name in m["references"]["items"]:
            referenced.setdefault(name, []).append(m)
    by_name_old = {v["name"]: (k, v) for k, v in old.items() if v.get("maps", {}).get("11")}
    by_name_new = {v["name"]: (k, v) for k, v in new.items() if v.get("maps", {}).get("11")}
    out = []
    for name, ms in sorted(referenced.items()):
        o, n = by_name_old.get(name), by_name_new.get(name)
        if o and not n:
            change, sev = "removed from Summoner's Rift", "high"
        elif o and n:
            ov, nv = o[1], n[1]
            diffs = []
            if ov["gold"]["total"] != nv["gold"]["total"]:
                diffs.append(f"cost {ov['gold']['total']} -> {nv['gold']['total']}")
            for s in sorted(set(ov.get("stats", {})) | set(nv.get("stats", {}))):
                if ov.get("stats", {}).get(s) != nv.get("stats", {}).get(s):
                    diffs.append(f"{s} {ov.get('stats', {}).get(s)} -> {nv.get('stats', {}).get(s)}")
            if re.sub(r"<[^>]+>|\d", "", ov.get("description", "")) != re.sub(r"<[^>]+>|\d", "", nv.get("description", "")):
                diffs.append("effect text changed")
            elif ov.get("description") != nv.get("description"):
                diffs.append("effect numbers changed")
            if not diffs:
                continue
            change, sev = "; ".join(diffs), ("medium" if "effect text changed" in diffs else "low")
        else:
            continue
        affects = [{"matchup": f"{m['role']}/{m['enemy']}",
                    "sections": sections_using(m, lambda it, nm=name: nm in it["text"])} for m in ms]
        out.append(finding("item", sev, f"Item {name}: {change}", change, affects,
                           f"Item {name} changed ({change}); re-check build advice in "
                           f"{', '.join(a['matchup'] for a in affects)}"))
    return out


def rune_findings(old_v: str, new_v: str, matchups: list[dict]) -> list[dict]:
    def flat(rs):
        return {r["name"]: r.get("longDesc", "") for t in rs for s in t["slots"] for r in s["runes"]}
    old, new = flat(dd("runes", old_v)), flat(dd("runes", new_v))
    out = []
    referenced = {n for m in matchups for n in m["references"]["runes"]}
    for name in sorted(referenced):
        if name in old and name not in new:
            change, sev = "removed", "high"
        elif name in old and old[name] != new.get(name):
            same_words = re.sub(r"<[^>]+>|\d", "", old[name]) == re.sub(r"<[^>]+>|\d", "", new[name])
            change, sev = ("numbers changed", "low") if same_words else ("effect text changed", "medium")
        else:
            continue
        affects = [{"matchup": f"{m['role']}/{m['enemy']}", "sections": ["runes"]}
                   for m in matchups if name in m["references"]["runes"]]
        out.append(finding("rune", sev, f"Rune {name}: {change}", change, affects,
                           f"Rune {name} {change}; re-check rune advice in {', '.join(a['matchup'] for a in affects)}"))
    return out


def video_findings() -> list[dict]:
    out = []
    for creator in CONFIG["sources"]["otp_creators"]:
        known = {p.stem.removeprefix("transcript_") for p in (ROOT / "data/raw/youtube").glob("transcript_*.json")}
        cached = ROOT / "data/raw/youtube" / f"videos_{creator['youtube_handle'].lstrip('@')}.json"
        if not cached.exists():
            continue
        # Channel id from the Phase 0 probe cache; RSS = latest 15 uploads, no API key needed.
        ch_html = (ROOT / "data/raw/youtube" / f"channel_{creator['youtube_handle']}.html")
        m = re.search(r'"(?:externalId|channelId)":"(UC[\w-]{22})"', ch_html.read_text(encoding="utf-8")) if ch_html.exists() else None
        if not m:
            continue
        feed = fetch(f"https://www.youtube.com/feeds/videos.xml?channel_id={m.group(1)}", "youtube",
                     f"feed_{m.group(1)}.xml", refresh=not OFFLINE)
        ns = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}
        for e in ET.fromstring(feed.text).findall("a:entry", ns):
            vid, link = e.find("yt:videoId", ns).text, e.find("a:link", ns).get("href")
            if "/shorts/" in link or vid in known:
                continue
            title, day = e.find("a:title", ns).text, e.find("a:published", ns).text[:10]
            out.append(finding("new_video", "medium", f"New {creator['name']} video: {title}", f"{day} {link}",
                               [], f"New {creator['name']} video '{title}' ({day}): fetch transcript, extract claims"))
    return out


def sheet_findings() -> list[dict]:
    """Federals1's public matchup sheet: did any row change since we parsed it?"""
    if OFFLINE:
        return []
    from parse_federals1_sheet import CSV_URL
    raw = ROOT / "data/raw/federals1/sheet_gid0.csv"
    old = fetch(CSV_URL, "federals1", "sheet_gid0.csv").text if raw.exists() else ""
    new = fetch(CSV_URL, "federals1", "sheet_gid0.csv", refresh=True).text
    lines = lambda t: [l.strip() for l in t.splitlines() if l.strip()]  # ignore line-ending differences
    if old and lines(old) != lines(new):
        return [finding("source_changed", "medium", "Federals1's matchup sheet was edited", "row-level diff: rerun parse_federals1_sheet.py",
                        [], "Federals1's matchup sheet changed: run parse_federals1_sheet.py, then prepare_claims + finalize for every matchup and review the diff")]
    return []


def aging_findings(matchups: list[dict]) -> list[dict]:
    out = []
    for m in matchups:
        rel = f"{m['enemy']}.assessed.json" if m["role"] == "-" else f"{m['role']}/{m['enemy']}.assessed.json"
        assessed = load(ROOT / "data/claims" / rel)
        days = (date.today() - date.fromisoformat(m["generated_at_date"])).days
        if days > 30:
            out.append(finding("stale_matchup", "low", f"{m['role']}/{m['enemy']} built {days} days ago",
                               f"assessed {assessed['assessed_at']}", [{"matchup": f"{m['role']}/{m['enemy']}", "sections": []}],
                               f"Re-run prepare_claims + finalize for {m['role']}/{m['enemy']} (freshness only, no LLM)"))
    return out


def main():
    matchups = matchup_files()
    if not matchups:
        print("no matchups yet"); return
    since_arg = sys.argv[sys.argv.index("--since") + 1] if "--since" in sys.argv else None
    built = since_arg or min((m["generated_at_patch"] for m in matchups), key=pkey)
    versions = json.loads(fetch(CONFIG["sources"]["data_dragon"]["versions"], "ddragon", "versions.json",
                                refresh=not OFFLINE).text)
    current = versions[0]
    findings = []
    if pkey(current) > pkey(built):
        findings.append(finding("new_patch", "medium", f"New patch {'.'.join(current.split('.')[:2])} (data built on {built})",
                                "Volatile data (builds, runes, stats) should be re-captured.",
                                [{"matchup": f"{m['role']}/{m['enemy']}", "sections": ITEM_SECTIONS + ["runes", "summoners"]} for m in matchups],
                                f"New patch {current}: refresh onetricks captures + stats for all matchups"))
    findings += kit_findings(CHAMP, pkey(built), matchups, True)
    for enemy in sorted({m["enemy"] for m in matchups} - {"_general"}):
        findings += kit_findings(enemy, pkey(built), matchups, False)
    old_v = ddragon_version(built)
    if old_v and old_v != current:
        findings += item_findings(old_v, current, matchups)
        findings += rune_findings(old_v, current, matchups)
    churn = load(META / "item_churn.json")
    for r in churn["patches"]:
        if pkey(r["patch"]) > pkey(built) and r["overhaul"]:
            findings.append(finding("item_overhaul", "high", f"Item overhaul in {r['patch']} (churn {r['churn']})",
                                    f"+{len(r['added'])} / -{len(r['removed'])} items", [],
                                    f"Item overhaul in {r['patch']}: add it to item_overhaul_patches and re-do all build sections"))
    findings += video_findings()
    findings += sheet_findings()
    findings += aging_findings(matchups)
    order = {"high": 0, "medium": 1, "low": 2}
    findings.sort(key=lambda f: order[f["severity"]])
    report = {"checked_at": date.today().isoformat(), "current_patch": current, "data_built_on": built,
              "manual_checks": [{"source": "MOBAFire guides", "how": "open the guide and compare 'Updated on' with the capture date",
                                 "items": CONFIG["sources"]["mobafire_guides"] + [{"author": "AddictedToBacon", "url": CONFIG["sources"]["otp_creators"][0]["mobafire_guide"]}],
                                 "captured": "2026-10-06"},
                                {"source": "onetricks.gg", "how": "re-capture after a new patch (browser only)",
                                 "captured": sorted({m['role'] + '/' + m['enemy'] for m in matchups})}],
              "findings": findings}
    (META / "freshness_report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"current {current}, data built on {built}: {len(findings)} findings")
    for f in findings:
        print(f"  [{f['severity']:<6}] {f['what'][:110]}")


if __name__ == "__main__":
    main()
