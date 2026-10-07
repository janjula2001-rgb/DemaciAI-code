"""Parse onetricks captures (data/raw/onetricks/<role>_<Enemy>.txt, made with onetricks_extract.js)
into structured JSON: data/clean/onetricks/<role>_<Enemy>.json. Deterministic, no LLM.
"""
from __future__ import annotations

import json
import re
import sys

from polite_http import ROOT, fetch

RAW = ROOT / "data" / "raw" / "onetricks"
OUT = ROOT / "data" / "clean" / "onetricks"
META = ROOT / "data" / "meta"
TOKEN = re.compile(r"\[([^\]]+)\]|(\d+(?:\.\d+)?)%|SP:(\S+)|L(\d+):([QWER])")


def tokens(text: str) -> list[tuple]:
    out = []
    for m in TOKEN.finditer(text):
        if m.group(1):
            out.append(("name", m.group(1)))
        elif m.group(2):
            out.append(("pct", float(m.group(2))))
        elif m.group(3):
            out.append(("sprite", m.group(3)))
        else:
            out.append(("level", (int(m.group(4)), m.group(5))))
    return out


def sections(lines: list[str]) -> dict[str, str]:
    body = " ".join(l for l in lines if not l.startswith("# ") and not l.startswith("http"))
    parts = re.split(r"#([A-Z][A-Za-z0-9 -]+?)(?= \[|\s\d|\sSP:|\sL\d|$)", body)
    return {parts[i].strip(): parts[i + 1] for i in range(1, len(parts) - 1, 2)}


def groups(toks: list[tuple]) -> list[dict]:
    """Items followed by the percentage(s) shown after them."""
    out, items = [], []
    for kind, val in toks:
        if kind == "name":
            items.append(val)
        elif kind == "pct":
            if items:
                out.append({"items": items, "pct": val})
                items = []
            elif out:
                out[-1].setdefault("extra_pcts", []).append(val)
    return out


def groups_pct_first(toks: list[tuple]) -> list[dict]:
    """Percentage shown before its items (Starting Items card)."""
    out = []
    for kind, val in toks:
        if kind == "pct":
            out.append({"items": [], "pct": val})
        elif kind == "name" and out:
            out[-1]["items"].append(val)
    return [g for g in out if g["items"]]


_summoner_cache: dict[str, dict] = {}


def summoner_at(sprite: str) -> str:
    """'16.13.1/spell0@-112,0/28' -> 'Ignite' using that version's Data Dragon summoner.json."""
    ver, rest = sprite.split("/", 1)
    sheet, pos = rest.split("@")
    xy, w = pos.split("/")
    x, y = (int(round(-float(v) * 48 / float(w))) for v in xy.split(","))
    if ver not in _summoner_cache:
        data = json.loads(fetch(f"https://ddragon.leagueoflegends.com/cdn/{ver}/data/en_US/summoner.json",
                                "ddragon", f"summoner_{ver}.json").text)["data"]
        _summoner_cache[ver] = {(s["image"]["sprite"], s["image"]["x"], s["image"]["y"]): s["name"]
                                for s in data.values() if "CLASSIC" in s["modes"]}
    return _summoner_cache[ver].get((f"{sheet}.png", x, y), f"?{sprite}")


def keystone_name(raw: str, cells: dict) -> str:
    m = re.fullmatch(r"cell:(\d+)", raw)
    if not m:
        return raw
    hit = cells.get(m.group(1), {}).get("name")
    return hit or f"unknown keystone (sprite cell {m.group(1)})"


def parse(path) -> dict:
    lines = path.read_text(encoding="utf-8").splitlines()
    url = lines[0].strip()
    patches = next((l.split()[-1] for l in lines if l.startswith("# patches")), None)
    secs = sections(lines)
    cells = json.loads((META / "onetricks_keystones.json").read_text(encoding="utf-8"))
    items_sr = json.loads((META / "items_sr.json").read_text(encoding="utf-8"))
    boot_ids = {k for k, v in items_sr.items() if "Boots" in v["tags"]}
    # tier-3 boots upgrade a boot; Data Dragon leaves the "Boots" tag off some of them (e.g. Gunmetal Greaves)
    boots = {v["name"] for k, v in items_sr.items() if k in boot_ids or set(v.get("from", [])) & boot_ids}

    keystones = []
    ks_line = next((l for l in lines if l.startswith("#Keystones")), "")
    for part in ks_line.removeprefix("#Keystones").split("|"):
        m = re.search(r"\[([^\]]+)\]\s*(\d+(?:\.\d+)?)%", part)
        if m:
            keystones.append({"name": keystone_name(m.group(1), cells), "pct": float(m.group(2)),
                              "shown_page": "shown below" in part})

    # Rune page: the 9-name sequence shown twice (desktop + mobile layout) in the Runes section.
    names = [v for k, v in tokens(secs.get("Runes", "")) if k == "name"]
    page = next((names[i:i + 9] for i in range(len(names) - 17) if names[i:i + 9] == names[i + 9:i + 18]), names[:9])

    pop = groups(tokens(secs.get("Popular Items", "")))
    popular = [{"item": g["items"][0], "pct": g["pct"], "boots": g["items"][0] in boots} for g in pop
               if len(g["items"]) == 1 and g["items"][0] != "Deprecated item"]  # onetricks placeholder for removed items

    sk = tokens(secs.get("Skills and Spells", ""))
    summoners, pair, level_opts, cur = [], [], [], []
    for kind, val in sk:
        if kind == "sprite":
            pair.append(summoner_at(val))
        elif kind == "pct" and pair:
            summoners.append({"spells": sorted(set(pair)), "pct": val})
            pair = []
        elif kind == "level":
            cur.append(val)
        elif kind == "pct" and cur:
            level_opts.append({"order": "".join(s for _, s in sorted(cur)), "pct": val})
            cur = []
    full_order = "".join(s for _, s in sorted(cur))  # trailing L1..L13 sequence has no percentage
    counts, max_order = {}, []
    for s in full_order:
        counts[s] = counts.get(s, 0) + 1
        if counts[s] == 5 and s != "R":
            max_order.append(s)
    max_order += [s for s in "QWE" if s not in max_order]

    start = groups_pct_first(tokens(secs.get("Starting Items", "")))
    path_groups = groups(tokens(secs.get("Build Path", "")))
    return {
        "url": url, "role": path.stem.split("_")[0], "enemy": path.stem.split("_", 1)[1],
        "patches": patches, "elo": "master+", "captured": "2026-10-06",
        "keystones": keystones, "rune_page_shown": page,
        "starting_items": start[0] if start else None,
        # Second group in the Starting Items card is shown with ">" arrows: most common early purchase order.
        "early_purchase_order": start[1] if len(start) > 1 else None,
        "first_item": path_groups[0] if path_groups else None,
        "build_path_groups": path_groups[1:],
        "popular_boots": [p for p in popular if p["boots"]],
        "popular_items": [p for p in popular if not p["boots"]],
        "summoners": summoners,
        "levels_1_3": level_opts,
        "skill_order_1_13": full_order, "skill_max_order": "".join(max_order),
        "note": "onetricks shows no game counts; percentages are Master+ OTP preferences over the patch range, "
                "not win-rate statistics. A wide patch range means few games.",
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    targets = [RAW / f"{a}.txt" for a in sys.argv[1:]] or sorted(RAW.glob("*_*.txt"))
    for path in targets:
        data = parse(path)
        (OUT / f"{path.stem}.json").write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
        ks = ", ".join(f"{k['name']} {k['pct']:.0f}%" for k in data["keystones"])
        sm = ", ".join(f"{'+'.join(s['spells'])} {s['pct']:.0f}%" for s in data["summoners"])
        print(f"{path.stem}: patches {data['patches']} | {ks} | {sm} | start {data['starting_items']} | "
              f"first {data['first_item']} | max {data['skill_max_order']} | page {data['rune_page_shown']}")


if __name__ == "__main__":
    main()
