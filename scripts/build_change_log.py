"""Kit-change log for every champion, from the LoL Wiki '<Champion>/Patch history' pages.

Every changed line is classified:
  release   — the champion's release entry (oldest on the page): kit baseline
  rework    — the whole patch entry is a relaunch / gameplay update (invalidates all stable claims)
  mechanic  — ability behaviour changed (new/removed effect, "now ...", "no longer ...")
  number    — pure tuning ("increased to X from Y"), base stats
  ignore    — bug fixes, skins, VFX/SFX, tooltips, animations
  ambiguous — none of the rules fired; queued in data/meta/change_log/_ambiguous.jsonl

Outputs:
  data/meta/patches.json              ddragon patch -> wiki name, display name, release date
  data/meta/change_log/<ChampId>.json per-champion log + last_rework / last_mechanic_change
  data/meta/change_log/_summary.json  one line per champion
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime
from urllib.parse import quote

from polite_http import ROOT, CONFIG, fetch

API = CONFIG["sources"]["lol_wiki"]["api"]
META = ROOT / "data" / "meta"
OUT = META / "change_log"
REFRESH = "--refresh" in sys.argv  # re-download wiki pages (e.g. after a new patch)
REVIEW_FROM = (14, 1)  # only queue ambiguous lines from this patch on; older ones predate any usable source

# --- wiki access -----------------------------------------------------------------

def wiki_pages(titles: list[str], key: str) -> dict[str, str]:
    """Fetch current wikitext for up to 50 titles in one request. Returns requested title -> content."""
    out = {}
    for i in range(0, len(titles), 50):
        batch = titles[i:i + 50]
        url = (f"{API}?action=query&prop=revisions&rvprop=content&rvslots=main&format=json"
               f"&formatversion=2&redirects=1&titles=" + quote("|".join(batch), safe="|"))
        digest = hashlib.sha1("|".join(batch).encode()).hexdigest()[:10]
        q = json.loads(fetch(url, "wiki", f"{key}_{digest}.json", refresh=REFRESH).text)["query"]
        back = {t: t for t in batch}
        for step in ("normalized", "redirects"):
            for m in q.get(step, []):
                for orig, cur in list(back.items()):
                    if cur == m["from"]:
                        back[orig] = m["to"]
        content = {p["title"]: p["revisions"][0]["slots"]["main"]["content"]
                   for p in q["pages"] if "revisions" in p}
        out.update({orig: content.get(cur, "") for orig, cur in back.items()})
    return out


# --- wikitext helpers -------------------------------------------------------------

TEMPLATE = re.compile(r"\{\{([^{}]*)\}\}")


def _template(m: re.Match) -> str:
    parts = [p.strip() for p in m.group(1).split("|")]
    name, args = parts[0].lower(), [a for a in parts[1:] if "=" not in a]
    if name == "csl" and len(args) >= 2:
        return f"{args[1]} {args[0]} skin"
    if name in ("numbersup",):
        return args[0] if args else ""
    if not args:
        return name
    return args[0].replace(" to ", "→") if name in ("ap", "pp") else args[0]


def plain(text: str) -> str:
    """Strip wiki templates/links to readable text."""
    for _ in range(6):
        new = TEMPLATE.sub(_template, text)
        if new == text:
            break
        text = new
    text = re.sub(r"<ref[^>]*>.*?</ref>|<ref[^>]*/>|<!--.*?-->|<[^>]+>", "", text)
    text = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", text)
    text = re.sub(r"\[https?://\S+\s*([^\]]*)\]", r"\1", text)
    text = re.sub(r"'{2,}", "", text)
    return re.sub(r"\s+", " ", text).strip()


def norm_patch(wiki: str) -> tuple[str, tuple]:
    """'V26.14' -> ('16.14', (16, 14)); 'V25.S1.2' -> ('15.2', (15, 2)); 'V4.20' -> ('4.20', (4, 20))."""
    v = wiki.lstrip("V")
    m = re.match(r"(\d+)\.S\d+\.(\d+)$", v)
    if m:
        major, minor = int(m.group(1)), int(m.group(2))
    else:
        nums = [int(x) for x in re.findall(r"\d+", v)]
        major, minor = nums[0], (nums[1] if len(nums) > 1 else 0)
        if len(nums) > 2 and major < 4:  # V1.0.0.85 style
            return v, tuple(nums)
    if major >= 25:
        major -= 10
    return f"{major}.{minor}", (major, minor)


# --- classification ------------------------------------------------------------------

REWORK_HEAD = re.compile(r"relaunch|gameplay update|champion update|rework|\bVGU\b|mini.?update", re.I)
IGNORE = re.compile(
    r"bug ?fix|\bvfx\b|\bsfx\b|visual|particle|animation|splash|icon|tooltip|voice|\bvo\b|audio|sound|"
    r"skin|chroma|recall|portrait|lore|title changed|indicator|now displays|properly displays|"
    r"no longer displays|cosmetic|emote|model|\bbug\b|\bunchanged\b|recommended (?:items|runes)|"
    r"^\d+ |^\[?note\b|did not happen|:$", re.I)  # footnotes, editor notes, sub-headers
MECHANIC = re.compile(
    r"\bnew effect|\bremoved\b|\bno longer\b|\bnow\b|\binstead of\b|\breplaced\b|\bcan now\b|"
    r"\binnate\b|\bactive:|\bpassive:|\bnew passive|\bnew active|\brenamed\b|\bno longer\b|"
    r"\bnow (?:also|deals|grants|applies|scales|has)|\bupdated\b|\brework|^old:|^new:", re.I)
NUMBER = re.compile(r"\b(?:increased|reduced|decreased|lowered|raised|adjusted|changed)\b.*\b(?:to|from)\b|"
                    r"\d+(?:\.\d+)?%?\s*(?:→|->)\s*\d", re.I)
STAT_SECTIONS = re.compile(r"^(?:stats|base stats)$", re.I)
# Crit-scaling formula changes (e.g. the 16.1 system-wide crit rework) change damage, not how an ability plays.
CRIT_TUNING = re.compile(r"critical (?:strike )?damage|critically strikes? at \S+ effectiveness|critical damage formula", re.I)
NUMERIC_WORDS = re.compile(r"damage|ratio|\bAD\b|\bAP\b|armor|magic resist|resistance|attack speed|health|heal|"
                           r"cooldown|mana|cost|range|duration|movement speed|per spin|per second", re.I)
BEHAVIOUR_WORDS = re.compile(r"stun|knock|airborne|root|silence|taunt|fear|charm|suppress|dash|blink|leap|"
                             r"untargetable|invulnerab|stealth|invisib|camouflage|reveal|cleanse|spell shield|"
                             r"can now|can no longer|recast|toggle|channel|on-hit effect|instead of", re.I)


def classify(section: str, line: str) -> str:
    if section.endswith(" skin") or IGNORE.search(line) or IGNORE.search(section) and section.lower() != "general":
        return "ignore"
    if STAT_SECTIONS.match(section) or CRIT_TUNING.search(line):
        return "number"
    # Numbers + damage/stat words, without crowd-control or movement behaviour, is tuning even when the
    # line says "Removed:" or "no longer" (e.g. a removed base-damage term). Behaviour changes stay mechanic.
    if re.search(r"\d", line) and NUMERIC_WORDS.search(line) and not BEHAVIOUR_WORDS.search(line):
        return "number"
    mech, num = MECHANIC.search(line), NUMBER.search(line)
    if mech:
        return "mechanic"
    if num:
        return "number"
    return "ambiguous"


# --- parsing -----------------------------------------------------------------------

HEAD = re.compile(r"^;\s*\[\[(?:V[^\]|#]*#[^\]|]*\|)?(V[^\]|#]+)\]\]\s*(?:-\s*(.*))?$")


def parse_history(wikitext: str) -> list[dict]:
    entries, cur, section = [], None, ""
    for raw in wikitext.splitlines():
        h = HEAD.match(raw.strip())
        if h:
            patch, key = norm_patch(h.group(1))
            label = plain(h.group(2) or "")
            cur = {"patch": patch, "wiki": h.group(1), "key": list(key), "label": label,
                   "rework": bool(REWORK_HEAD.search(label)), "changes": []}
            entries.append(cur)
            continue
        if cur is None or not raw.startswith("*"):
            continue
        depth = len(raw) - len(raw.lstrip("*"))
        text = plain(raw.lstrip("*"))
        if not text:
            continue
        if depth == 1:
            section = text.replace("(Innate)", "").strip()
            continue
        kind = "rework" if cur["rework"] else classify(section, text)
        cur["changes"].append({"section": section, "depth": depth, "kind": kind, "text": text})
    # Page is newest-first; the last entry is the champion's release (its kit baseline).
    if entries:
        entries[-1]["release"] = True
        for c in entries[-1]["changes"]:
            c["kind"] = "release"
    return entries


# --- patch release dates ------------------------------------------------------------------

def release_date(infobox: str) -> str | None:
    m = re.search(r"^\|\s*Release\s*=\s*(.+)$", infobox, re.M | re.I)
    if not m:
        return None
    txt = re.sub(r"\{\{NumberSup\|(\d+)\}\}", r"\1", m.group(1), flags=re.I)
    txt = re.sub(r"(\d+)(st|nd|rd|th)\b", r"\1", plain(txt))
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%d %B %Y"):
        try:
            return datetime.strptime(txt.strip(), fmt).date().isoformat()
        except ValueError:
            pass
    return None


def build_patch_dates(wiki_names: set[str]) -> dict:
    # every patch, back to release: old kit tips are valid unless a mechanic changed after them, which needs dates
    names = sorted(wiki_names, key=lambda w: norm_patch(w)[1])
    pages = wiki_pages(names, "patchpages")
    out = {}
    for w in names:
        p, _ = norm_patch(w)
        if p in out and not re.fullmatch(r"V[\d.]+|V\d+\.S\d+\.\d+", w):
            continue  # keep the base patch (V13.1), not a letter re-release (V13.1b)
        out[p] = {"wiki": w, "display": w.lstrip("V"), "release": release_date(pages.get(w, ""))}
    return out


# --- main -------------------------------------------------------------------------------

def summarize(entries: list[dict], dates: dict) -> dict:
    def stamp(e):
        return {"patch": e["patch"], "release": dates.get(e["patch"], {}).get("release"), "label": e["label"]}

    by_key = sorted(entries, key=lambda e: tuple(e["key"]), reverse=True)
    rework = next((e for e in by_key if e["rework"]), None)
    release = next((e for e in by_key if e.get("release")), None)
    baseline = rework or release
    last_mech, by_ability = None, {}
    for e in by_key:
        for c in e["changes"]:
            if c["kind"] in ("mechanic", "rework", "release"):
                # For a rework/release, describe the whole entry rather than one random line of it.
                text = (e["label"] or ("Champion release" if c["kind"] == "release" else "Rework"))                     if c["kind"] in ("rework", "release") else c["text"][:200]
                by_ability.setdefault(c["section"], stamp(e) | {"text": text})
                if last_mech is None:
                    last_mech = stamp(e) | {"section": "whole kit" if c["kind"] in ("rework", "release") else c["section"],
                                            "text": text}
    return {"release": stamp(release) if release else None,
            "last_rework": stamp(rework) if rework else None,
            # Newest of release / full rework: nothing said about the champion before it still holds.
            "kit_baseline": stamp(baseline) | {"kind": "rework" if rework else "release"} if baseline else None,
            "last_mechanic_change": last_mech,
            "last_mechanic_change_by_ability": by_ability}


def main():
    champs = json.loads((META / "champions.json").read_text(encoding="utf-8"))
    titles = {cid: f"{c['name']}/Patch history" for cid, c in champs.items()}
    pages = wiki_pages(sorted(titles.values()), "patch_history")
    parsed = {cid: parse_history(pages.get(t, "")) for cid, t in titles.items()}
    missing = [cid for cid, e in parsed.items() if not e]

    dates = build_patch_dates({e["wiki"] for es in parsed.values() for e in es})
    (META / "patches.json").write_text(json.dumps(dates, indent=1), encoding="utf-8")

    OUT.mkdir(parents=True, exist_ok=True)
    summary, ambiguous, counts = {}, [], {}
    for cid, entries in parsed.items():
        if not entries:
            continue
        s = summarize(entries, dates)
        log = {"champion": cid, "wiki_page": titles[cid], **s, "entries": entries}
        (OUT / f"{cid}.json").write_text(json.dumps(log, indent=1, ensure_ascii=False), encoding="utf-8")
        summary[cid] = {k: s[k] for k in ("kit_baseline", "last_rework", "last_mechanic_change")}
        for e in entries:
            for c in e["changes"]:
                counts[c["kind"]] = counts.get(c["kind"], 0) + 1
                if c["kind"] == "ambiguous" and tuple(e["key"]) >= REVIEW_FROM:
                    ambiguous.append({"champion": cid, "patch": e["patch"], "section": c["section"], "text": c["text"]})
    (OUT / "_summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    with open(OUT / "_ambiguous.jsonl", "w", encoding="utf-8") as f:
        for a in ambiguous:
            f.write(json.dumps(a, ensure_ascii=False) + "\n")

    undated = [p for p, d in dates.items() if not d["release"]]
    print(f"champions parsed: {len(parsed) - len(missing)}/{len(parsed)}; missing pages: {missing}")
    print(f"line kinds (all patches): {counts}")
    print(f"ambiguous since {REVIEW_FROM[0]}.{REVIEW_FROM[1]}: {len(ambiguous)}")
    print(f"patches: {len(dates)}; without release date ({len(undated)}): {undated[:40]}")


if __name__ == "__main__":
    main()
