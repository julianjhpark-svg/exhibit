"""Download the two test papers. PDFs are gitignored — this keeps the repo public-safe."""

from __future__ import annotations

import urllib.request
from pathlib import Path

IDS = ["2307.03172", "2305.14627"]
DEST = Path(__file__).resolve().parents[1] / "data" / "sources"
UA = "exhibit-hackathon-demo/0.1 (educational; contact: replace-me@example.com)"


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    for arxiv_id in IDS:
        target = DEST / f"{arxiv_id}.pdf"
        if target.exists():
            print(f"skip  {target.name} (already here)")
            continue
        url = f"https://arxiv.org/pdf/{arxiv_id}"
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        print(f"fetch {arxiv_id} ...", end=" ", flush=True)
        with urllib.request.urlopen(req, timeout=60) as resp:
            target.write_bytes(resp.read())
        print(f"{target.stat().st_size // 1024} KB")
    print(f"\nDone. Sources in {DEST}")


if __name__ == "__main__":
    main()
