"""Map onetricks.gg keystone sprite cells -> keystone names by matching against Data Dragon icons.

onetricks shows non-default keystones as cells of keystone_sprites2.webp without a name. Each cell is
compared (mean pixel difference on a small greyscale thumbnail) with every Data Dragon keystone icon;
the best match wins if its distance is <= MAX_DIST (exact matches are ~1; cells for keystones no longer in
Data Dragon score ~20 and are stored with name null). Output: data/meta/onetricks_keystones.json {cell_index: {name, distance}}.
"""
from __future__ import annotations

import io
import json

from PIL import Image, ImageChops, ImageStat

from polite_http import ROOT, _session, _wait_turn

SPRITE = "https://assets.onetricks.net/onetricks/img/perk-images/sprite/keystone_sprites2.webp"
COLS = 5
MAX_DIST = 5.0


def download(url: str) -> Image.Image:
    _wait_turn()
    r = _session.get(url, timeout=30)
    r.raise_for_status()
    return Image.open(io.BytesIO(r.content)).convert("RGBA")


def thumb(im: Image.Image) -> Image.Image:
    bg = Image.new("RGBA", im.size, "black")
    return Image.alpha_composite(bg, im).convert("L").resize((24, 24))


def main():
    patch = json.loads((ROOT / "data/meta/current_patch.json").read_text())["ddragon"]
    runes = json.loads((ROOT / f"data/raw/ddragon/runes_{patch}.json").read_text(encoding="utf-8"))
    keystones = {r["name"]: r["icon"] for tree in runes for r in tree["slots"][0]["runes"]}
    icons = {n: thumb(download(f"https://ddragon.leagueoflegends.com/cdn/img/{p}")) for n, p in keystones.items()}

    sheet = download(SPRITE)
    size = sheet.width // COLS
    out = {}
    for idx in range(COLS * (sheet.height // size)):
        x, y = idx % COLS, idx // COLS
        cell = sheet.crop((x * size, y * size, (x + 1) * size, (y + 1) * size))
        if cell.getbbox() is None:  # empty cell
            continue
        t = thumb(cell)
        dist = {n: ImageStat.Stat(ImageChops.difference(t, ic)).mean[0] for n, ic in icons.items()}
        best = sorted(dist, key=dist.get)
        out[idx] = {"name": best[0] if dist[best[0]] <= MAX_DIST else None, "distance": round(dist[best[0]], 1),
                    "runner_up": best[1], "runner_up_distance": round(dist[best[1]], 1)}
    (ROOT / "data/meta/onetricks_keystones.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    for i, m in out.items():
        print(f"{i:>2} {str(m['name']):<22} d={m['distance']:<5} (next: {m['runner_up']} d={m['runner_up_distance']})")


if __name__ == "__main__":
    main()
