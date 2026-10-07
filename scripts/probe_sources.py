"""Phase 0: test access to every source in config.yaml.

Writes data/meta/feasibility.json, cleaned page text to data/clean/_probe/,
and prints a short summary. Raw responses are cached in data/raw/.
Re-running uses the cache; pass --refresh to re-download.
"""
from __future__ import annotations

import json
import re
import sys
import traceback
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup

from polite_http import CONFIG, ROOT, fetch, render, robots_allowed, _wait_turn

REFRESH = "--refresh" in sys.argv
SRC = CONFIG["sources"]
CHAMP = CONFIG["champion"]
CLEAN = ROOT / "data" / "clean" / "_probe"
CLEAN.mkdir(parents=True, exist_ok=True)
ctx: dict = {}  # values shared between probes (patch, item names)


def clean_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for t in soup(["script", "style", "noscript", "svg"]):
        t.decompose()
    lines = (l.strip() for l in soup.get_text("\n").splitlines())
    return "\n".join(l for l in lines if l)


def save_clean(name: str, text: str) -> str:
    path = CLEAN / f"{name}.txt"
    path.write_text(text, encoding="utf-8")
    return str(path.relative_to(ROOT))


def result(source, status, http=None, robots=None, extractable="", notes=""):
    return dict(source=source, status=status, http=http, robots=robots,
                extractable=extractable, notes=notes)


def blocked_by_robots(source, url):
    allowed = robots_allowed(url)
    if allowed is False:
        return allowed, result(source, "blocked", robots=False,
                               notes=f"robots.txt disallows {url}; not fetched")
    return allowed, None


# --- probes ---------------------------------------------------------------

def probe_data_dragon():
    dd = SRC["data_dragon"]
    v = fetch(dd["versions"], "ddragon", "versions.json", refresh=True)
    patch = json.loads(v.text)[0]
    champs = json.loads(fetch(dd["champions"].format(patch=patch), "ddragon", f"champion_{patch}.json").text)
    items = json.loads(fetch(dd["items"].format(patch=patch), "ddragon", f"item_{patch}.json").text)
    runes = json.loads(fetch(dd["runes"].format(patch=patch), "ddragon", f"runes_{patch}.json").text)
    ctx["patch"] = patch
    ctx["items"] = {k: v["name"] for k, v in items["data"].items()}
    ctx["runes"] = {str(r["id"]): r["name"] for tree in runes for slot in tree["slots"] for r in slot["runes"]}
    ctx["runes"].update({str(t["id"]): t["name"] for t in runes})
    ctx["champions"] = sorted(champs["data"])
    return result("Data Dragon", "works", v.status, None,
                  f"patch {patch}; {len(champs['data'])} champions; {len(items['data'])} items; "
                  f"{len(ctx['runes'])} runes/trees",
                  f"{CHAMP} present: {CHAMP in champs['data']}; item 3078 = {ctx['items'].get('3078')}")


def probe_wiki():
    api = SRC["lol_wiki"]["api"]
    allowed, blocked = blocked_by_robots("LoL Wiki", api)
    if blocked:
        return blocked
    # Discover the champion's subpages instead of guessing the patch-history title.
    q = fetch(f"{api}?action=query&list=prefixsearch&pssearch={CHAMP}/&pslimit=50&format=json",
              "wiki", f"{CHAMP}_subpages.json")
    if q.status != 200:
        return result("LoL Wiki", "blocked", q.status, allowed, notes=q.text[:150])
    titles = [p["title"] for p in json.loads(q.text)["query"]["prefixsearch"]]
    hist = sorted((t for t in titles if "history" in t.lower()), key=lambda t: "patch" not in t.lower())
    if not hist:
        return result("LoL Wiki", "partial", q.status, allowed, notes=f"no history subpage; subpages: {titles}")
    page = hist[0]
    p = fetch(f"{api}?action=parse&page={page}&prop=wikitext&format=json", "wiki", f"{page}.json")
    wt = json.loads(p.text)["parse"]["wikitext"]["*"]
    versions = re.findall(r"^;\s*\[\[(V\d+\.[\w.]+)\]\]", wt, re.M)
    save_clean("wiki_patch_history_head", wt[:6000])
    return result("LoL Wiki", "works", p.status, allowed,
                  f"page '{page}': {len(wt)} chars wikitext, {len(versions)} patch headings "
                  f"(newest: {versions[:3]}, oldest: {versions[-2:]})",
                  f"other history-like subpages: {hist[1:]}")


def _image_ids(html: str):
    srcs = re.findall(r'(?:src|srcset)="([^"]+)"', html)
    item_ids = {m for s in srcs for m in re.findall(r"/items?/(\d{4,6})\.(?:png|webp)", s)}
    perk_ids = {m for s in srcs for m in re.findall(r"/(?:perks?|runes?|perk-images)/[^\"]*?(\d{4})\.(?:png|webp)", s)}
    return item_ids, perk_ids, srcs


def probe_onetricks():
    out = []
    url = SRC["onetricks"]["matchup"].format(champion=CHAMP, enemy="Teemo", role="top")
    allowed, blocked = blocked_by_robots("onetricks.gg matchup", url)
    if blocked:
        return [blocked]
    raw = fetch(url, "onetricks", "matchup_Teemo_top.html", refresh=REFRESH)
    has_json = bool(re.search(r"__NEXT_DATA__|__NUXT__|application/json", raw.text))
    out.append(result("onetricks.gg (plain HTTP)", "info", raw.status, allowed,
                      f"{len(raw.text)} bytes; embedded JSON: {has_json}; "
                      f"mentions Teemo: {'Teemo' in clean_text(raw.text)}"))

    r = render(url, "onetricks", "matchup_Teemo_top.rendered.html", refresh=REFRESH, wait_ms=6000)
    item_ids, perk_ids, srcs = _image_ids(r.text)
    named = {i: ctx.get("items", {}).get(i, "?") for i in sorted(item_ids)}
    text = clean_text(r.text)
    clean_path = save_clean("onetricks_matchup_Teemo_top", text)
    img_hosts = sorted({re.sub(r"^https?://([^/]+).*", r"\1", s) for s in srcs if s.startswith("http")})[:6]
    status = "works" if item_ids else "partial"
    out.append(result("onetricks.gg (Playwright)", status, r.status, allowed,
                      f"{len(item_ids)} item image IDs -> {list(named.values())[:8]}; "
                      f"{len(perk_ids)} rune image IDs; clean text {len(text)} chars ({clean_path})",
                      f"image hosts: {img_hosts}"))

    for name in ("ranking", "streamers"):
        u = SRC["onetricks"][name].format(champion=CHAMP)
        rr = render(u, "onetricks", f"{name}_{CHAMP}.rendered.html", refresh=REFRESH, wait_ms=6000)
        t = clean_text(rr.text)
        p = save_clean(f"onetricks_{name}", t)
        out.append(result(f"onetricks.gg {name}", "works" if len(t) > 500 else "partial", rr.status,
                          robots_allowed(u), f"clean text {len(t)} chars ({p})"))
    return out


def probe_mobafire():
    url = SRC["otp_creators"][0]["mobafire_guide"]
    allowed, blocked = blocked_by_robots("MOBAFire", url)
    if blocked:
        return blocked
    r = fetch(url, "mobafire", "addictedtobacon_garen.html", refresh=REFRESH)
    cf = "Just a moment" in r.text or "cf-chl" in r.text
    if r.status != 200 or cf:
        return result("MOBAFire", "blocked", r.status, allowed, notes=f"cloudflare challenge: {cf}")
    text = clean_text(r.text)
    p = save_clean("mobafire_addictedtobacon", text)
    updated = re.search(r"(?:Updated on|Last updated)[^\n]*\n?[^\n]*", text)
    threats = len(re.findall(r"\bThreats?\b", text))
    return result("MOBAFire", "works", r.status, allowed,
                  f"clean text {len(text)} chars ({p}); 'Threat' mentions: {threats}",
                  f"update marker: {updated.group(0).strip()[:80] if updated else 'not found'}")


def probe_youtube():
    from youtube_transcript_api import YouTubeTranscriptApi

    handle = SRC["otp_creators"][0]["youtube_handle"]
    ch = fetch(f"https://www.youtube.com/{handle}", "youtube", f"channel_{handle}.html", refresh=REFRESH)
    m = re.search(r'"(?:externalId|channelId)":"(UC[\w-]{22})"', ch.text)
    if not m:
        consent = "consent.youtube.com" in ch.text
        return result("YouTube", "partial", ch.status, None, notes=f"channel ID not found; consent page: {consent}")
    cid = m.group(1)
    feed = fetch(f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}", "youtube", f"feed_{cid}.xml",
                 refresh=REFRESH)
    ns = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}
    all_entries = ET.fromstring(feed.text).findall("a:entry", ns)
    # RSS mixes Shorts in; only full videos are useful for transcripts.
    entries = [(e.find("yt:videoId", ns).text, e.find("a:title", ns).text, e.find("a:published", ns).text[:10])
               for e in all_entries if "/shorts/" not in e.find("a:link", ns).get("href")]
    api = YouTubeTranscriptApi()
    got, notes = [], []
    for vid, title, date in entries[:2]:
        cache = ROOT / "data" / "raw" / "youtube" / f"transcript_{vid}.json"
        try:
            if cache.exists() and not REFRESH:
                data = json.loads(cache.read_text(encoding="utf-8"))
            else:
                _wait_turn()
                tl = api.list(vid)
                tr = tl.find_transcript(["en", "en-US", "en-GB"])
                _wait_turn()
                snippets = tr.fetch().to_raw_data()
                data = {"video_id": vid, "title": title, "date": date, "language": tr.language_code,
                        "is_generated": tr.is_generated, "snippets": snippets}
                cache.write_text(json.dumps(data), encoding="utf-8")
            words = sum(len(s["text"].split()) for s in data["snippets"])
            got.append(f"{vid} ({date}, {data['language']}, auto={data['is_generated']}, {words} words)")
        except Exception as e:  # noqa: BLE001 — report any library/IP-block error
            notes.append(f"{vid}: {type(e).__name__}: {str(e).splitlines()[0][:120]}")
    status = "works" if got else "blocked"
    return result("YouTube transcripts", status, feed.status, None,
                  f"channel {cid}; RSS gives {len(all_entries)} latest uploads ({len(entries)} non-Shorts); newest {entries[0][2] if entries else '-'}; "
                  f"transcripts: {got}", "; ".join(notes))


def probe_reddit():
    url = "https://www.reddit.com/r/Garenmains/top.json?t=year&limit=5"
    allowed = robots_allowed(url)
    notes = ("Official API: self-service keys closed since 2025-11-11; new OAuth apps need manual "
             "approval (Responsible Builder Policy), personal scripts rarely approved.")
    if allowed is False:
        return result("Reddit", "blocked", None, False, "", f"robots.txt disallows .json endpoint; not fetched. {notes}")
    r = fetch(url, "reddit", "garenmains_top_year.json", refresh=REFRESH)
    if r.status != 200:
        return result("Reddit", "blocked", r.status, allowed, notes=notes)
    posts = [c["data"]["title"][:60] for c in json.loads(r.text)["data"]["children"]]
    return result("Reddit", "works", r.status, allowed, f"{len(posts)} posts via public JSON", notes)


def _stats_probe(name, url, key, needles):
    allowed, blocked = blocked_by_robots(name, url)
    if blocked:
        return blocked
    raw = fetch(url, "stats", f"{key}.html", refresh=REFRESH)
    r = render(url, "stats", f"{key}.rendered.html", refresh=REFRESH, wait_ms=6000)
    text = clean_text(r.text)
    p = save_clean(key, text)
    found = {n: bool(re.search(n, text, re.I)) for n in needles}
    status = "works" if all(found.values()) else ("partial" if any(found.values()) else "blocked")
    cf = "Just a moment" in r.text
    return result(name, status, r.status, allowed,
                  f"plain HTTP {raw.status}/{len(raw.text)}B; rendered text {len(text)} chars ({p}); found {found}",
                  f"cloudflare: {cf}")


def probe_ugg():
    url = SRC["stats"]["ugg_matchups"].format(champion_lower=CHAMP.lower(), role="top", rank="platinum_plus")
    return _stats_probe("u.gg", url, "ugg_garen_matchups_top", [r"win ?rate", r"matches|games", r"teemo", r"platinum"])


def probe_lolalytics():
    url = f"https://lolalytics.com/lol/{CHAMP.lower()}/vs/teemo/build/?lane=top&tier=platinum_plus"
    return _stats_probe("lolalytics", url, "lolalytics_garen_vs_teemo_top",
                        [r"win ?rate|WR", r"games", r"teemo", r"platinum"])


PROBES = [probe_data_dragon, probe_wiki, probe_onetricks, probe_mobafire, probe_youtube,
          probe_reddit, probe_ugg, probe_lolalytics]


def main():
    results = []
    for probe in PROBES:
        try:
            r = probe()
            results.extend(r if isinstance(r, list) else [r])
        except Exception as e:  # noqa: BLE001 — one failing source must not stop the rest
            results.append(result(probe.__name__, "error", notes=f"{type(e).__name__}: {e}"[:300]))
            traceback.print_exc(limit=1, file=sys.stderr)
    out = ROOT / "data" / "meta" / "feasibility.json"
    out.write_text(json.dumps({"patch": ctx.get("patch"), "results": results}, indent=2), encoding="utf-8")
    for r in results:
        print(f"[{r['status'].upper():8}] {r['source']}  http={r['http']} robots={r['robots']}")
        if r["extractable"]:
            print(f"    {r['extractable']}")
        if r["notes"]:
            print(f"    note: {r['notes']}")


if __name__ == "__main__":
    main()
