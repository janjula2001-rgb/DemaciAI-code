"""Fetch transcripts for every full (non-Shorts) video of each OTP creator in config.yaml.

Listing and upload dates come from yt-dlp (metadata only, nothing is downloaded);
transcripts from youtube-transcript-api. Raw data -> data/raw/youtube/,
cleaned text (header + transcript) -> data/clean/youtube/<video_id>.txt.
Already-fetched videos are skipped unless --refresh.

  fetch_youtube.py                 all full videos of every creator in config.yaml
  fetch_youtube.py --ids ID [ID…]  specific videos (e.g. matchup guides found by search)
"""
from __future__ import annotations

import json
import subprocess
import sys

from youtube_transcript_api import YouTubeTranscriptApi

from polite_http import CONFIG, ROOT, _wait_turn

RAW = ROOT / "data" / "raw" / "youtube"
CLEAN = ROOT / "data" / "clean" / "youtube"
REFRESH = "--refresh" in sys.argv


def ytdlp(*args: str) -> list[str]:
    _wait_turn()
    r = subprocess.run([sys.executable, "-m", "yt_dlp", *args], capture_output=True, text=True,
                       encoding="utf-8", check=True)
    return [l for l in r.stdout.splitlines() if l.strip()]


def list_videos(handle: str) -> list[dict]:
    cache = RAW / f"videos_{handle.lstrip('@')}.json"
    if cache.exists() and not REFRESH:
        return json.loads(cache.read_text(encoding="utf-8"))
    ids = [l.split("|", 1) for l in ytdlp("--flat-playlist", "--print", "%(id)s|%(title)s",
                                         f"https://www.youtube.com/{handle}/videos")]
    videos = []
    for vid, title in ids:
        date = ytdlp("--skip-download", "--print", "%(upload_date)s|%(duration)s",
                     f"https://www.youtube.com/watch?v={vid}")[0].split("|")
        videos.append({"video_id": vid, "title": title,
                       "date": f"{date[0][:4]}-{date[0][4:6]}-{date[0][6:]}", "duration_s": int(date[1])})
    RAW.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(videos, indent=1), encoding="utf-8")
    return videos


def video_meta(vid: str) -> dict:
    cache = RAW / f"meta_{vid}.json"
    if cache.exists() and not REFRESH:
        return json.loads(cache.read_text(encoding="utf-8"))
    line = ytdlp("--skip-download", "--print", "%(upload_date)s|%(duration)s|%(channel)s|%(title)s",
                 f"https://www.youtube.com/watch?v={vid}")[0]
    d, dur, channel, title = line.split("|", 3)
    meta = {"video_id": vid, "title": title, "channel": channel,
            "date": f"{d[:4]}-{d[4:6]}-{d[6:]}", "duration_s": int(dur)}
    RAW.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(meta), encoding="utf-8")
    return meta


def fetch_transcript(api: YouTubeTranscriptApi, v: dict, author: str) -> str:
    raw = RAW / f"transcript_{v['video_id']}.json"
    if raw.exists() and not REFRESH:
        data = json.loads(raw.read_text(encoding="utf-8"))
    else:
        _wait_turn()
        tr = api.list(v["video_id"]).find_transcript(["en", "en-US", "en-GB"])
        _wait_turn()
        data = {**v, "language": tr.language_code, "is_generated": tr.is_generated,
                "snippets": tr.fetch().to_raw_data()}
        raw.write_text(json.dumps(data), encoding="utf-8")
    text = " ".join(s["text"].replace("\n", " ") for s in data["snippets"])
    header = (f"title: {v['title']}\nurl: https://www.youtube.com/watch?v={v['video_id']}\n"
              f"author: {author}\nsource_date: {v['date']}\nauto_generated: {data['is_generated']}\n\n")
    CLEAN.mkdir(parents=True, exist_ok=True)
    (CLEAN / f"{v['video_id']}.txt").write_text(header + text, encoding="utf-8")
    return text




def main():
    api = YouTubeTranscriptApi()
    if "--ids" in sys.argv:
        for vid in [a for a in sys.argv[sys.argv.index("--ids") + 1:] if not a.startswith("--")]:
            v = video_meta(vid)
            try:
                words = len(fetch_transcript(api, v, v["channel"]).split())
                print(f"ok   {v['date']} {vid} {words:>6} words  {v['channel']}: {v['title'][:60]}")
            except Exception as e:  # noqa: BLE001
                print(f"FAIL {v['date']} {vid} {type(e).__name__}: {str(e).splitlines()[0][:100]}")
        return
    for creator in CONFIG["sources"]["otp_creators"]:
        for v in list_videos(creator["youtube_handle"]):
            try:
                words = len(fetch_transcript(api, v, creator["name"]).split())
                print(f"ok   {v['date']} {v['video_id']} {words:>6} words  {v['title'][:60]}")
            except Exception as e:  # noqa: BLE001 — report and continue with the next video
                print(f"FAIL {v['date']} {v['video_id']} {type(e).__name__}: {str(e).splitlines()[0][:100]}")


if __name__ == "__main__":
    main()
