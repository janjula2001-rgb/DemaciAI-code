"""Polite, cached HTTP access shared by every fetch script.

Rules (CLAUDE.md): >=2 s between requests, cache everything in data/raw/,
never re-download what's cached unless refresh=True.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
import yaml

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
CONFIG = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))

_HTTP = CONFIG["http"]
_session = requests.Session()
_session.headers["User-Agent"] = _HTTP["user_agent"]
_last_request = 0.0


@dataclass
class Response:
    url: str
    status: int
    text: str
    fetched_at: str
    from_cache: bool


def _wait_turn() -> None:
    global _last_request
    gap = time.monotonic() - _last_request
    if gap < _HTTP["min_delay_s"]:
        time.sleep(_HTTP["min_delay_s"] - gap)
    _last_request = time.monotonic()


def _cache_path(source: str, key: str | None, url: str) -> Path:
    if key is None:
        key = hashlib.sha1(url.encode()).hexdigest()[:16]
    key = re.sub(r"[^A-Za-z0-9._-]", "_", key)
    return RAW / source / key


def _load(path: Path) -> Response | None:
    meta = path.with_suffix(".meta.json")
    if not (path.exists() and meta.exists()):
        return None
    m = json.loads(meta.read_text(encoding="utf-8"))
    with open(path, encoding="utf-8", newline="") as f:  # newline="": return the text exactly as fetched
        text = f.read()
    return Response(m["url"], m["status"], text, m["fetched_at"], True)


def _save(path: Path, resp: Response) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(resp.text, encoding="utf-8", newline="")  # no CRLF translation on Windows
    meta = {"url": resp.url, "status": resp.status, "fetched_at": resp.fetched_at}
    path.with_suffix(".meta.json").write_text(json.dumps(meta), encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def fetch(url: str, source: str, key: str | None = None, refresh: bool = False,
          headers: dict | None = None) -> Response:
    """GET url, caching the body under data/raw/<source>/<key>."""
    path = _cache_path(source, key, url)
    if not refresh and (cached := _load(path)):
        return cached
    _wait_turn()
    r = _session.get(url, timeout=_HTTP["timeout_s"], headers=headers)
    resp = Response(url, r.status_code, r.text, _now(), False)
    _save(path, resp)
    return resp


def fetch_bytes(url: str, source: str, key: str | None = None, refresh: bool = False) -> bytes | None:
    """GET a binary file (images), cached under data/raw/<source>/<key>; None on a non-200 answer (also cached)."""
    path = _cache_path(source, key, url)
    meta = path.with_suffix(path.suffix + ".meta.json")
    if not refresh and meta.exists():
        m = json.loads(meta.read_text(encoding="utf-8"))
        return path.read_bytes() if m["status"] == 200 and path.exists() else None
    _wait_turn()
    r = _session.get(url, timeout=_HTTP["timeout_s"])
    path.parent.mkdir(parents=True, exist_ok=True)
    if r.status_code == 200:
        path.write_bytes(r.content)
    meta.write_text(json.dumps({"url": url, "status": r.status_code, "fetched_at": _now()}), encoding="utf-8")
    return r.content if r.status_code == 200 else None


def render(url: str, source: str, key: str | None = None, refresh: bool = False,
           wait_ms: int = 4000) -> Response:
    """Render a JS-heavy page with headless Chromium; cache the final HTML."""
    path = _cache_path(source, key, url)
    if not refresh and (cached := _load(path)):
        return cached
    from playwright.sync_api import sync_playwright

    _wait_turn()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(user_agent=_HTTP["user_agent"])
        nav = page.goto(url, timeout=_HTTP["timeout_s"] * 1000, wait_until="domcontentloaded")
        page.wait_for_timeout(wait_ms)
        resp = Response(url, nav.status if nav else 0, page.content(), _now(), False)
        browser.close()
    _save(path, resp)
    return resp


def robots_allowed(url: str) -> bool | None:
    """True/False per the site's robots.txt for our UA; None if robots.txt unreadable."""
    parts = urlparse(url)
    host = parts.netloc
    robots_url = f"{parts.scheme}://{host}/robots.txt"
    try:
        r = fetch(robots_url, "robots", key=host)
    except requests.RequestException:
        return None
    if r.status >= 400:
        return None if r.status >= 500 or r.status in (401, 403) else True
    rp = RobotFileParser()
    rp.parse(r.text.splitlines())
    return rp.can_fetch(_HTTP["user_agent"], url)
