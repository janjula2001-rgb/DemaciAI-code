"""Rank-filtered matchup stats (Platinum+) from u.gg and lolalytics -> data/clean/stats/<role>_<Enemy>.json.

u.gg: one rendered matchup table per role (all enemies). lolalytics: one rendered 'Garen vs <Enemy>' page each.
Usage: fetch_stats.py <role> <Enemy> [<Enemy> ...] [--refresh]
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date

from bs4 import BeautifulSoup

from polite_http import CONFIG, ROOT, render

CHAMP = CONFIG["champion"]
OUT = ROOT / "data" / "clean" / "stats"
REFRESH = "--refresh" in sys.argv
MIN_GAMES = 1000  # below this, the stat is shown but flagged as a small sample


def text_lines(html: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    for t in soup(["script", "style", "noscript", "svg"]):
        t.decompose()
    return [l.strip() for l in soup.get_text("\n").splitlines() if l.strip()]


def num(s: str) -> float:
    return float(s.replace(",", "").replace("%", ""))


def ugg_table(role: str) -> tuple[dict, str | None]:
    url = CONFIG["sources"]["stats"]["ugg_matchups"].format(champion_lower=CHAMP.lower(), role=role, rank="platinum_plus")
    # Key matches the Phase 0 probe cache for top.
    lines = text_lines(render(url, "stats", f"ugg_{CHAMP.lower()}_matchups_{role}.rendered.html", refresh=REFRESH,
                              wait_ms=6000).text)
    patch = next((l.split()[-1] for l in lines if re.fullmatch(r"Patch \d+\.\d+", l)), None)
    start = lines.index("Matches") + 1
    rows = {}
    for i in range(start, len(lines) - 8):
        if re.fullmatch(r"\d+", lines[i]) and re.fullmatch(r"\d+\.\d+%", lines[i + 2]):
            name = lines[i + 1]
            try:
                rows[name] = {"win_rate": num(lines[i + 2]), "gold_diff_15": num(lines[i + 3]),
                              "xp_diff_15": num(lines[i + 4]), "games": int(num(lines[i + 8]))}
            except ValueError:
                continue
    return {"url": url, "rows": rows}, patch


def lolalytics(role: str, enemy: str) -> dict:
    slug = re.sub(r"[^a-z]", "", enemy.lower())
    lane = {"mid": "middle"}.get(role, role)  # lolalytics lane names
    url = f"https://lolalytics.com/lol/{CHAMP.lower()}/vs/{slug}/build/?lane={lane}&tier=platinum_plus"
    key = f"lolalytics_{CHAMP.lower()}_vs_{slug}_{role}.rendered.html"
    lines = text_lines(render(url, "stats", key, refresh=REFRESH, wait_ms=6000).text)
    text = " ".join(lines)
    m = re.search(r"(\d+\.\d+) % Win Rate ([\d,]+) Games", text)
    delta = re.search(r"(wins|loses) against \w+ (\d+\.\d+)% of the time which is (-?\d+\.\d+)% different", text)
    norm = re.search(r"(-?\d+\.\d+)% different than would be expected", text)
    patch = re.search(r"Patch (\d+\.\d+)", text)
    return {"url": url, "patch": patch.group(1) if patch else None,
            "win_rate": num(m.group(1)) if m else None, "games": int(num(m.group(2))) if m else None,
            "delta_vs_avg_opponent": float(delta.group(3)) if delta else None,
            "normalized_delta": float(norm.group(1)) if norm else None}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    role, enemies = args[0], args[1:]
    OUT.mkdir(parents=True, exist_ok=True)
    ugg, ugg_patch = ugg_table(role)
    for enemy in enemies:
        names = json.loads((ROOT / "data/meta/champions.json").read_text(encoding="utf-8"))
        u = ugg["rows"].get(names.get(enemy, {}).get("name", enemy)) or ugg["rows"].get(enemy)  # u.gg uses display names
        lo = lolalytics(role, enemy)
        out = {"enemy": enemy, "role": role, "elo_filter": "platinum+", "fetched": date.today().isoformat(),
               "ugg": ({"url": ugg["url"], "patch_display": ugg_patch, **u} if u else
                       {"url": ugg["url"], "missing": "matchup not in u.gg table (too few games?)"}),
               "lolalytics": lo}
        games = [g for g in ((u or {}).get("games"), lo.get("games")) if g]
        out["small_sample"] = not games or max(games) < MIN_GAMES
        (OUT / f"{role}_{enemy}.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
        print(f"{enemy}: u.gg {u} | lolalytics WR {lo['win_rate']} games {lo['games']} "
              f"delta {lo['delta_vs_avg_opponent']} norm {lo['normalized_delta']} patch {lo['patch']}")


if __name__ == "__main__":
    main()
