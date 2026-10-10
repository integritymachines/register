#!/usr/bin/env python3
"""Generate and freeze the complete 300-author Class-D prediction panel.

The pipeline is deliberately upstream of corpus measurement and 10D
projection. It uses only the predictive manifest, fixed roll-call lexicon, and
previously frozen D24 background guesses bundled with this repository.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def validate(output_dir: Path) -> None:
    table = output_dir / "D300_ROLLCALL_FULL.csv"
    rows = list(csv.DictReader(table.open(encoding="utf-8", newline="")))
    if len(rows) != 300 * 48:
        raise RuntimeError(f"expected 14,400 rows, found {len(rows)}")
    keys = {(row["d_id"], row["pair_id"]) for row in rows}
    if len(keys) != len(rows):
        raise RuntimeError("duplicate author/pair rows")
    if any(not row["predicted_score_0_10"] for row in rows):
        raise RuntimeError("the completed panel contains abstentions")
    if any(not 0 <= float(row["predicted_score_0_10"]) <= 10 for row in rows):
        raise RuntimeError("score outside [0, 10]")

    freeze = json.loads((output_dir / "FREEZE.json").read_text())
    for name, expected in freeze["output_sha256"].items():
        actual = hashlib.sha256((output_dir / name).read_bytes()).hexdigest()
        if actual != expected:
            raise RuntimeError(f"hash mismatch: {name}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=ROOT / "data/D300_author_manifest.csv")
    parser.add_argument("--lexicon", type=Path, default=ROOT / "data/lexicon.csv")
    parser.add_argument("--templates", type=Path, default=ROOT / "data/D24_template_guesses.csv")
    parser.add_argument("--output-dir", type=Path, default=Path("D300_predictions_full"))
    parser.add_argument("--archive", type=Path, help="optional output ZIP")
    args = parser.parse_args()

    output = args.output_dir.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="d300-stage1-") as temporary:
        stage1 = Path(temporary) / "D300_predictions"
        run([
            sys.executable,
            str(ROOT / "scripts/d300_stage1.py"),
            "--manifest", str(args.manifest.resolve()),
            "--lexicon", str(args.lexicon.resolve()),
            "--templates", str(args.templates.resolve()),
            "--output-dir", str(stage1),
        ])
        command = [
            sys.executable,
            str(ROOT / "scripts/d300_stage2.py"),
            str(stage1),
            "--output-dir", str(output),
        ]
        if args.archive:
            command.extend(["--archive", str(args.archive.resolve())])
        run(command)

    validate(output)
    print(f"validated complete Class-D panel: {output / 'D300_ROLLCALL_FULL.csv'}")


if __name__ == "__main__":
    main()
