"""Find item-system overhaul patches by diffing Data Dragon item data patch-to-patch.

For each patch since FIRST, compare the Summoner's Rift purchasable item pool (by item ID, all tiers)
with the previous patch. churn = (added + removed) / previous pool size; a patch is flagged as an
overhaul when churn >= THRESHOLD. Items whose effect wording changed are counted for information only:
Data Dragon tooltip text is unreliable (e.g. 14.19 shortened most descriptions without gameplay changes).
Output: data/meta/item_churn.json (all patches) — build/rune claims sourced before the newest
flagged overhaul are invalid (see CLAUDE.md "volatile").
"""
from __future__ import annotations

import json
import re

from fetch_ddragon import DD, sr_items
from polite_http import ROOT, fetch

FIRST = (13, 1)
THRESHOLD = 0.10


def patch_versions() -> list[tuple[tuple[int, int], str]]:
    versions = json.loads(fetch(DD["versions"], "ddragon", "versions.json").text)
    best = {}
    for v in versions:
        parts = v.split(".")
        if len(parts) < 3 or not all(p.isdigit() for p in parts):
            continue
        key = (int(parts[0]), int(parts[1]))
        if key >= FIRST and key not in best:  # versions.json is newest-first
            best[key] = v
    return sorted(best.items())


def effect_text(desc: str) -> str:
    """Description reduced to its wording: no tags, numbers, punctuation or case."""
    desc = re.sub(r"<[^>]+>", " ", desc)
    desc = re.sub(r"[\d.,%+()\-:]+", " ", desc)
    return " ".join(desc.lower().split())


def completed(version: str) -> dict:
    items = json.loads(fetch(DD["items"].format(patch=version), "ddragon", f"item_{version}.json").text)["data"]
    sr = sr_items(items)
    return {i: (sr[i]["name"], effect_text(items[i].get("description", ""))) for i in sr}


def main():
    rows, prev = [], None
    for key, version in patch_versions():
        cur = completed(version)
        if prev is not None:
            added = sorted(cur[i][0] for i in set(cur) - set(prev))
            removed = sorted(prev[i][0] for i in set(prev) - set(cur))
            changed = [i for i in set(cur) & set(prev) if cur[i][1] != prev[i][1]]
            churn = (len(added) + len(removed)) / max(len(prev), 1)
            rows.append({"patch": f"{key[0]}.{key[1]}", "ddragon": version, "sr_items": len(cur),
                         "added": added, "removed": removed, "text_changed_count": len(changed),
                         "churn": round(churn, 3), "overhaul": churn >= THRESHOLD})
        prev = cur
    out = ROOT / "data" / "meta" / "item_churn.json"
    out.write_text(json.dumps({"threshold": THRESHOLD, "patches": rows}, indent=1, ensure_ascii=False),
                   encoding="utf-8")
    for r in sorted(rows, key=lambda r: -r["churn"])[:10]:
        print(f"{r['patch']:>6} churn {r['churn']:.2f}  +{len(r['added'])} -{len(r['removed'])} of {r['sr_items']} "
              f"(text ~{r['text_changed_count']}){'  <-- OVERHAUL' if r['overhaul'] else ''}  "
              f"removed e.g. {r['removed'][:4]}")


if __name__ == "__main__":
    main()
