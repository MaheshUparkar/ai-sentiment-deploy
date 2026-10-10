"""Download the public sentiment datasets and normalise them to `text,label` CSVs in training/data/public/.

Run once (output is committed, so Docker builds never depend on these downloads):
    python training/prepare_data.py
"""

import csv
import io
import sys
import urllib.request
import zipfile
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent / "data" / "public"

# Hugging Face mirror of 3-class tweet sentiment (Apache-2.0), pinned to an exact revision.
TWEETS_URL = (
    "https://huggingface.co/datasets/Sp1786/multiclass-sentiment-analysis-dataset/"
    "resolve/a7ede749d4b3e7ef516603cad80bd6b39b0a1fca/{split}_df.csv"
)
# UCI "Sentiment Labelled Sentences" (Kotzias et al., KDD 2015), CC BY 4.0. Positive/negative only.
UCI_URL = "https://archive.ics.uci.edu/static/public/331/sentiment+labelled+sentences.zip"
LABELS = {"positive", "negative", "neutral"}


def download(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=60) as resp:
        return resp.read()


def write_csv(path: Path, rows: list[tuple[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["text", "label"])
        writer.writerows(rows)
    print(f"Wrote {len(rows):>6} rows to {path.name}")


def clean(text: str) -> str:
    return " ".join(text.split())


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for split in ("train", "val", "test"):
        raw = download(TWEETS_URL.format(split=split)).decode("utf-8")
        rows = [
            (clean(r["text"]), r["sentiment"])
            for r in csv.DictReader(io.StringIO(raw))
            if r["sentiment"] in LABELS and clean(r["text"])
        ]
        write_csv(OUT_DIR / f"tweets_{split}.csv", rows)

    rows = []
    with zipfile.ZipFile(io.BytesIO(download(UCI_URL))) as zf:
        for name in sorted(zf.namelist()):
            if not name.endswith("_labelled.txt") or "__MACOSX" in name:
                continue
            for line in zf.read(name).decode("utf-8").splitlines():
                text, _, score = line.rpartition("\t")
                if score in ("0", "1") and clean(text):
                    rows.append((clean(text), "positive" if score == "1" else "negative"))
    write_csv(OUT_DIR / "uci_sentences.csv", rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
