"""Split a batch onetricks capture into per-matchup files.

The built-in browser returns one JSON object {Enemy: capture_text} for a whole batch (iframe capture of
scripts/onetricks_extract.js). Save it as data/raw/onetricks/_batch.json, then:
  split_onetricks_batch.py <role>   ->  data/raw/onetricks/<role>_<Enemy>.txt (and deletes _batch.json)
"""
from __future__ import annotations

import json
import sys

from polite_http import ROOT

RAW = ROOT / "data" / "raw" / "onetricks"


def main():
    role = sys.argv[1]
    batch = RAW / "_batch.json"
    data = json.loads(batch.read_text(encoding="utf-8"))
    for enemy, text in data.items():
        if not text or text.startswith("TIMEOUT"):
            print(f"skip {enemy}: {text!r:.40}")
            continue
        (RAW / f"{role}_{enemy}.txt").write_text(text + "\n", encoding="utf-8", newline="")
        print(f"saved {role}_{enemy}.txt")
    batch.unlink()


if __name__ == "__main__":
    main()
