"""Download and cache the official Riot Data Dragon art the frontend needs (never hotlinked).

  fetch_frontend_assets.py [--check]

Writes frontend/public/assets/:
  champ/<Id>/splash-1215.webp, splash-640.webp, loading.webp, icon-120.webp, icon-64.webp, P|Q|W|E|R.webp
  item/<itemId>.webp, rune/<runeId>.webp, spell/<SummonerKey>.webp
  assets.json   names, item cost/stats/plain description, rune/spell names, champion titles + ability names
Patch comes from data/meta/current_patch.json. Every download goes through polite_http (2 s pacing, cached in
data/raw/ddragon_img/), so re-runs only fetch what's new. --check lists data names with no local asset.
"""
from __future__ import annotations

import difflib
import io
import json
import re
import sys
from html import unescape
from pathlib import Path

from PIL import Image

from polite_http import ROOT, fetch, fetch_bytes

META = ROOT / "data" / "meta"
OUT = ROOT / "frontend" / "public" / "assets"
CDN = "https://ddragon.leagueoflegends.com/cdn"
V = json.loads((META / "current_patch.json").read_text(encoding="utf-8"))["ddragon"]
MAIN = "Garen"


def ddjson(kind: str, url: str) -> dict:
    """Data Dragon JSON via the same cache keys as fetch_ddragon.py."""
    return json.loads(fetch(url, "ddragon", key=f"{kind}_{V}.json").text)


def save_webp(url: str, key: str, dest: Path, widths: dict[str, int | None], quality=82) -> bool:
    """Download url once and write one WebP per width ({suffix: width or None for native})."""
    targets = {dest.with_name(dest.stem + sfx + ".webp"): w for sfx, w in widths.items()}
    if all(p.exists() for p in targets):
        return True
    raw = fetch_bytes(url, "ddragon_img", key=key)
    if raw is None:
        print("  missing upstream:", url)
        return False
    img = Image.open(io.BytesIO(raw)).convert("RGBA" if url.endswith(".png") else "RGB")
    for p, w in targets.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        im = img if not w or img.width <= w else img.resize((w, round(img.height * w / img.width)), Image.LANCZOS)
        im.save(p, "WEBP", quality=quality, method=6)
    return True


def matchup_files() -> list[Path]:
    return [p for role in ("top", "mid") for p in sorted((ROOT / "data" / "matchups" / role).glob("*.json"))
            if not p.name.endswith(".synth.json") and not p.name.startswith("_")]


def champions_needed() -> list[str]:
    return sorted({MAIN} | {p.stem for p in matchup_files()})


def item_names_needed() -> set[str]:
    names = set()
    for p in (ROOT / "data" / "clean" / "onetricks").glob("*.json"):
        d = json.loads(p.read_text(encoding="utf-8"))
        for k in ("starting_items", "early_purchase_order", "first_item"):
            names |= set((d.get(k) or {}).get("items", []))
        names |= {g for grp in d.get("build_path_groups", []) for g in grp["items"]}
        names |= {b["item"] for b in d.get("popular_boots", []) + d.get("popular_items", [])}
    sheet = json.loads((ROOT / "data" / "clean" / "federals1" / "sheet.json").read_text(encoding="utf-8"))
    names |= {i for row in sheet["champions"].values() for i in row.get("build_path", [])}
    for p in matchup_files() + [ROOT / "data" / "matchups" / "_general.json", ROOT / "data" / "matchups" / "mid" / "_general.json"]:
        if p.exists():
            names |= set(json.loads(p.read_text(encoding="utf-8")).get("references", {}).get("items", []))
    return names


def resolve_item(raw: str, by_name: dict[str, str]) -> list[str]:
    """Federals1's sheet has typos and free text ("Merucry's Treads", "Youmuu's Ghostblade/ Black Cleaver",
    "Mortal Reminder if you bought Cleaver"). Map each "/"-separated part to a real item name: exact, then
    case-insensitive, then an item name it starts with, then a close spelling (difflib >= 0.85)."""
    lower = {n.lower(): n for n in by_name}
    out = []
    for part in (x.strip() for x in raw.split("/")):
        hit = by_name.get(part) and part or lower.get(part.lower())
        if not hit:
            hit = next((lower[n] for n in sorted(lower, key=len, reverse=True) if part.lower().startswith(n + " ")), None)
        if not hit:
            close = difflib.get_close_matches(part.lower(), list(lower), n=1, cutoff=0.85)
            hit = lower[close[0]] if close else None
        if hit and hit not in out:
            out.append(hit)
    return out


def plain(desc: str) -> str:
    """Data Dragon item description HTML -> short plain text."""
    s = re.sub(r"<br\s*/?>", "\n", desc)
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\n{2,}", "\n", unescape(s)).strip()


def main():
    manifest = {"patch": V, "champions": {}, "items": {}, "item_aliases": {}, "runes": {}, "spells": {}}

    champ_list = ddjson("champion", f"{CDN}/{V}/data/en_US/champion.json")["data"]
    for cid in champions_needed():
        c = ddjson(f"champion_{cid}", f"{CDN}/{V}/data/en_US/champion/{cid}.json")["data"][cid]
        d = OUT / "champ" / cid
        save_webp(f"{CDN}/img/champion/splash/{cid}_0.jpg", f"splash_{cid}_0.jpg", d / "splash", {"-1215": None, "-640": 640})
        save_webp(f"{CDN}/img/champion/loading/{cid}_0.jpg", f"loading_{cid}_0.jpg", d / "loading", {"": None})
        save_webp(f"{CDN}/{V}/img/champion/{cid}.png", f"icon_{cid}_{V}.png", d / "icon", {"-120": None, "-64": 64})
        abilities = {"P": c["passive"]}
        abilities.update(zip("QWER", c["spells"]))
        for k, a in abilities.items():
            folder = "passive" if k == "P" else "spell"
            save_webp(f"{CDN}/{V}/img/{folder}/{a['image']['full']}", f"{folder}_{a['image']['full']}_{V}", d / k, {"": None})
        manifest["champions"][cid] = {"name": c["name"], "title": c["title"], "tags": champ_list.get(cid, {}).get("tags", []),
                                      "abilities": {k: a["name"] for k, a in abilities.items()}}
        print("champion", cid)

    items = ddjson("item", f"{CDN}/{V}/data/en_US/item.json")["data"]
    sr = json.loads((META / "items_sr.json").read_text(encoding="utf-8"))
    by_name = {v["name"]: k for k, v in sr.items()}
    wanted = set()
    for name in sorted(item_names_needed()):
        resolved = resolve_item(name, by_name)
        if not resolved:
            print("  no item for", name)
        elif resolved != [name]:
            manifest["item_aliases"][name] = resolved
        wanted |= set(resolved)
    for name in sorted(wanted):
        iid = by_name[name]
        if iid not in items:
            print("  not in item.json:", name)
            continue
        it = items[iid]
        save_webp(f"{CDN}/{V}/img/item/{iid}.png", f"item_{iid}_{V}.png", OUT / "item" / iid, {"": None})
        manifest["items"][name] = {"id": iid, "cost": it["gold"]["total"], "plaintext": it.get("plaintext", ""),
                                   "description": plain(it["description"]), "tags": it.get("tags", [])}
    print("items", len(manifest["items"]))

    for style in ddjson("runes", f"{CDN}/{V}/data/en_US/runesReforged.json"):
        entries = [style] + [r for slot in style["slots"] for r in slot["runes"]]
        for r in entries:
            save_webp(f"{CDN}/img/{r['icon']}", f"rune_{r['id']}.png", OUT / "rune" / str(r["id"]), {"": None})
            manifest["runes"][r["name"]] = {"id": r["id"], "style": style["name"], "short": plain(r.get("shortDesc", ""))}
    print("runes", len(manifest["runes"]))

    for s in ddjson("summoner", f"{CDN}/{V}/data/en_US/summoner.json")["data"].values():
        if "CLASSIC" not in s.get("modes", []):
            continue
        save_webp(f"{CDN}/{V}/img/spell/{s['image']['full']}", f"summ_{s['id']}_{V}.png", OUT / "spell" / s["id"], {"": None})
        manifest["spells"][s["name"]] = {"id": s["id"], "description": plain(s["description"])}
    print("summoner spells", len(manifest["spells"]))

    (OUT / "assets.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    print("wrote", OUT / "assets.json")


def check():
    m = json.loads((OUT / "assets.json").read_text(encoding="utf-8"))
    missing = sorted(n for n in item_names_needed() if n not in m["items"] and n not in m["item_aliases"])
    missing += [f"champion {c}" for c in champions_needed() if not (OUT / "champ" / c / "splash-1215.webp").exists()]
    print("missing:", missing or "none")


if __name__ == "__main__":
    check() if "--check" in sys.argv else main()
