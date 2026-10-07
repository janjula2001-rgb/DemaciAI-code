"""Read-only Reddit search for Garen matchup advice. Needs Reddit API approval and credentials in .env.

  fetch_reddit.py <Enemy> [<Enemy> ...] [--sub Garenmains] [--limit 15] [--refresh]

App-only OAuth (client_credentials grant, no user login). For each enemy it searches the subreddit for posts
about that matchup, then reads each post's top comments. It never posts, comments, votes or messages.
Every request goes through polite_http: at least 2 s apart, cached in data/raw/reddit/, never fetched twice
unless --refresh. Writes data/clean/reddit/<post_id>.txt (title, url, author, date, score, post text, top
comments with author and score) as source text for claim extraction; every claim keeps the thread link and author.

Requires REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET and REDDIT_USER_AGENT in .env, and reddit.enabled: true in
config.yaml (switched on only after Reddit approves API access).
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from urllib.parse import quote

import requests
from dotenv import load_dotenv

from polite_http import CONFIG, ROOT, fetch

API = "https://oauth.reddit.com"
CLEAN = ROOT / "data" / "clean" / "reddit"
MIN_COMMENT_SCORE = 2
REFRESH = "--refresh" in sys.argv


def arg(name: str, default: str) -> str:
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def token(ua: str) -> str:
    """App-only bearer token (read-only access to public data)."""
    r = requests.post("https://www.reddit.com/api/v1/access_token",
                      auth=(os.environ["REDDIT_CLIENT_ID"], os.environ["REDDIT_CLIENT_SECRET"]),
                      data={"grant_type": "client_credentials"}, headers={"User-Agent": ua}, timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]


def get(url: str, key: str, headers: dict) -> dict | list:
    resp = fetch(url, "reddit", key=key, refresh=REFRESH, headers=headers)
    if resp.status != 200:
        raise SystemExit(f"Reddit answered HTTP {resp.status} for {url}; stopping (no retries, no workarounds).")
    return json.loads(resp.text)


def day(ts: float) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).date().isoformat()


def comments(listing: list, depth: int = 0) -> list[str]:
    out = []
    for ch in listing:
        d = ch.get("data", {})
        if ch.get("kind") != "t1" or d.get("author") in (None, "[deleted]") or d.get("score", 0) < MIN_COMMENT_SCORE:
            continue
        out.append(f"{'  ' * depth}- u/{d['author']} ({d['score']} points, {day(d['created_utc'])}): {d['body'].strip()}")
        replies = d.get("replies")
        if depth < 1 and isinstance(replies, dict):
            out += comments(replies["data"]["children"], depth + 1)
    return out


def main():
    cfg = CONFIG["sources"]["reddit"]
    if not cfg.get("enabled"):
        raise SystemExit("reddit.enabled is false in config.yaml (switch it on once Reddit approves API access).")
    load_dotenv(ROOT / ".env")
    ua = os.environ["REDDIT_USER_AGENT"]
    headers = {"Authorization": f"bearer {token(ua)}", "User-Agent": ua}
    sub = arg("--sub", cfg["primary"])
    limit = int(arg("--limit", "15"))
    names = json.loads((ROOT / "data" / "meta" / "champions.json").read_text(encoding="utf-8"))
    args, skip = [], False
    for a in sys.argv[1:]:  # enemies = positional args; --sub/--limit take a value
        if skip:
            skip = False
        elif a in ("--sub", "--limit"):
            skip = True
        elif not a.startswith("--"):
            args.append(a)
    enemies = args
    CLEAN.mkdir(parents=True, exist_ok=True)

    for enemy in enemies:
        name = names.get(enemy, {}).get("name", enemy)
        q = f'"{name}"' if sub.lower() == "garenmains" else f"garen {name}"
        url = f"{API}/r/{sub}/search?q={quote(q)}&restrict_sr=1&sort=relevance&t=all&limit={limit}&raw_json=1"
        posts = [c["data"] for c in get(url, f"search_{sub}_{enemy}.json", headers)["data"]["children"]]
        saved = 0
        for p in posts:
            if p.get("removed_by_category") or (not p.get("selftext") and p.get("num_comments", 0) == 0):
                continue
            thread = get(f"{API}/comments/{p['id']}?limit=40&depth=2&sort=top&raw_json=1", f"comments_{p['id']}.json", headers)
            lines = [f"title: {p['title']}", f"url: https://www.reddit.com{p['permalink']}", f"author: u/{p['author']}",
                     f"source_date: {day(p['created_utc'])}", f"score: {p['score']}", f"subreddit: r/{sub}", f"enemy: {enemy}", "",
                     p.get("selftext", "").strip(), "", "Top comments:", *comments(thread[1]["data"]["children"])]
            (CLEAN / f"{p['id']}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
            saved += 1
        print(f"{enemy}: {len(posts)} posts found in r/{sub}, {saved} saved")


if __name__ == "__main__":
    main()
