"""Meta layer from Riot Data Dragon -> data/meta/.

current_patch.json  ddragon version + Riot display name (16.N <-> 26.N)
champions.json      id -> name (+ wiki page name, used by build_change_log.py)
items_sr.json       Summoner's Rift purchasable items: id -> name, gold, tags, from/into
runes.json          rune / tree id -> name, plus name -> id
summoners.json      summoner spells incl. sprite positions (to decode onetricks sprites)
"""
from __future__ import annotations

import json

from polite_http import CONFIG, ROOT, fetch

META = ROOT / "data" / "meta"
DD = CONFIG["sources"]["data_dragon"]


def display_patch(patch: str) -> str:
    """Data Dragon '16.19.1' -> Riot/wiki display name '26.19' (year-based since 2025)."""
    major, minor = patch.split(".")[:2]
    major = int(major)
    return f"{major + 10}.{minor}" if major >= 15 else f"{major}.{minor}"


def get(url: str, key: str) -> dict | list:
    return json.loads(fetch(url, "ddragon", key).text)


def write(name: str, data) -> None:
    (META / name).write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")


def sr_items(items: dict) -> dict:
    out = {}
    for iid, it in items.items():
        if not it.get("maps", {}).get("11") or not it.get("gold", {}).get("purchasable"):
            continue
        if it.get("inStore") is False or it.get("requiredChampion") or it.get("requiredAlly"):
            continue
        out[iid] = {"name": it["name"], "gold": it["gold"]["total"], "tags": it.get("tags", []),
                    "from": it.get("from", []), "into": it.get("into", []),
                    "depth": it.get("depth", 1)}
    return out


def main():
    # Always refresh the version list; everything else is cached per patch.
    patch = json.loads(fetch(DD["versions"], "ddragon", "versions.json", refresh=True).text)[0]
    champs = get(DD["champions"].format(patch=patch), f"champion_{patch}.json")["data"]
    items = get(DD["items"].format(patch=patch), f"item_{patch}.json")["data"]
    runes = get(DD["runes"].format(patch=patch), f"runes_{patch}.json")
    spells = get(f"https://ddragon.leagueoflegends.com/cdn/{patch}/data/en_US/summoner.json",
                 f"summoner_{patch}.json")["data"]

    META.mkdir(parents=True, exist_ok=True)
    write("current_patch.json", {"ddragon": patch, "patch": ".".join(patch.split(".")[:2]),
                                 "display": display_patch(patch)})
    write("champions.json", {c["id"]: {"name": c["name"], "key": c["key"], "tags": c["tags"]}
                             for c in champs.values()})
    sr = sr_items(items)
    write("items_sr.json", sr)
    rune_names = {str(t["id"]): t["name"] for t in runes}
    rune_names.update({str(r["id"]): r["name"] for t in runes for s in t["slots"] for r in s["runes"]})
    write("runes.json", {"by_id": rune_names, "by_name": {v: k for k, v in rune_names.items()}})
    write("summoners.json", {s["key"]: {"id": s["id"], "name": s["name"], "modes": s["modes"],
                                        "sprite": s["image"]["sprite"], "x": s["image"]["x"], "y": s["image"]["y"]}
                             for s in spells.values()})
    legendary = sum(1 for i in sr.values() if not i["into"] and i["depth"] >= 3)
    print(f"patch {patch} ({display_patch(patch)}): {len(champs)} champions, {len(sr)} SR items "
          f"({legendary} completed depth>=3), {len(rune_names)} runes, {len(spells)} summoner spells")


if __name__ == "__main__":
    main()
