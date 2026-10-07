"""Frame-time check for the web app's two busiest moments (Playwright, Chromium).

  perf_frontend.py [--base http://localhost:5173] [--css "<extra css>"]

1. Home: 3 s of mouse movement over the splash and grid (Ken Burns, parallax, dust, tile hover).
2. Matchup page: scroll from top to bottom in wheel steps (reveals, ScrollTrigger, sticky nav).
Reports frames, p50/p95 frame time and how many frames took over 20 ms. Headless Chromium renders on the CPU,
so absolute numbers are pessimistic; use it to compare changes. --css injects a stylesheet (A/B a suspect).
"""
from __future__ import annotations

import statistics
import sys

from playwright.sync_api import sync_playwright

BASE = sys.argv[sys.argv.index("--base") + 1] if "--base" in sys.argv else "http://localhost:5173"
CSS = sys.argv[sys.argv.index("--css") + 1] if "--css" in sys.argv else ""

COLLECT = """() => { window.__frames = []; let last = performance.now();
  const tick = (t) => { window.__frames.push(t - last); last = t; if (window.__frames.length < 100000) requestAnimationFrame(tick); };
  requestAnimationFrame(tick); }"""


def report(name, frames):
    frames = frames[2:]
    if not frames:
        print(name, "no frames"); return
    q = statistics.quantiles(frames, n=20)
    print(f"{name}: {len(frames)} frames, p50 {statistics.median(frames):.1f} ms, p95 {q[18]:.1f} ms, "
          f"over 20 ms: {sum(f > 20 for f in frames)} ({100 * sum(f > 20 for f in frames) / len(frames):.0f}%)")


def main():
    with sync_playwright() as p:
        # use the real GPU when the machine allows it (much closer to what the app gets in a normal browser)
        b = p.chromium.launch(args=["--enable-gpu", "--ignore-gpu-blocklist", "--use-angle=d3d11", "--enable-gpu-rasterization"])
        page = b.new_page(viewport={"width": 1920, "height": 1080})
        if CSS:
            page.add_init_script(f"document.addEventListener('DOMContentLoaded', () => {{ const s = document.createElement('style'); s.textContent = {CSS!r}; document.head.append(s); }})")

        print("renderer:", page.evaluate("""() => { const gl = document.createElement('canvas').getContext('webgl');
            const ext = gl && gl.getExtension('WEBGL_debug_renderer_info'); return ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : 'unknown'; }"""))
        page.goto(BASE + "/"); page.wait_for_timeout(3000)
        page.evaluate(COLLECT)
        for i in range(60):
            page.mouse.move(300 + i * 25, 200 + (i % 10) * 60)
            page.wait_for_timeout(50)
        report("home, mouse moving", page.evaluate("window.__frames"))

        page.goto(BASE + "/top/Darius"); page.wait_for_timeout(2500)
        page.evaluate(COLLECT)
        for _ in range(45):
            page.mouse.wheel(0, 260)
            page.wait_for_timeout(90)
        report("matchup, scrolling", page.evaluate("window.__frames"))
        b.close()


if __name__ == "__main__":
    main()
