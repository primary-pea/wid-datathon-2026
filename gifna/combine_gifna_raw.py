"""
Rebuild gifna_mechanisms.csv, gifna_policies.csv, and gifna_programmes_and_actions.csv
by combining the per-country raw exports in Africa_Data/.

Africa_Data/ holds one file per (type, country, export-date), e.g.
  gifna_policies_BDI_2026-09-03.csv
  gifna_programmes and actions_LBR_2026-09-03 (1).csv
Some countries were exported twice (2026-09-01 and 2026-09-03); where both exist
for the same (type, country) this script keeps only the latest-dated one. A " (1)"
suffix marks a duplicate download of the same export, not a different one.

Each file is parsed with Python's csv module (not pandas' own reader), which
handles embedded literal newlines inside a quoted field correctly -- some Brief
Description fields are pasted-from-Word HTML running hundreds of lines long.
Every row is checked against the header's column count: a short row is padded
(harmless -- some exports drop trailing empty commas), a long row means a
field's closing quote never matched and later lines bled into extra columns --
that row is dropped and reported rather than silently misaligned.

After picking one file per (type, country), rows are still deduplicated exactly
(all columns equal) before writing out -- a handful of raw files (e.g. the Guinea
export) contain rows for other countries too, which would otherwise double-count
against that country's own dedicated file.

Usage:
    py combine_gifna_raw.py
    py combine_gifna_raw.py --input-dir "C:\\path\\to\\Africa_Data" --output-dir "C:\\path\\to\\project"
"""

import argparse
import csv
import re
from pathlib import Path

import pandas as pd

FILENAME_RE = re.compile(
    r"^(gifna_mechanisms|gifna_policies|gifna_programmes and actions)_"
    r"([A-Z]{3})_(\d{4}-\d{2}-\d{2})(?: \(\d+\))?\.csv$"
)

OUTPUT_NAMES = {
    "gifna_mechanisms": "gifna_mechanisms.csv",
    "gifna_policies": "gifna_policies.csv",
    "gifna_programmes and actions": "gifna_programmes_and_actions.csv",
}


def pick_latest_per_country(input_dir):
    """For each (type, country), keep only the file with the latest export date.
    Returns {type: [Path, ...]}."""
    candidates = {}  # (type, iso3) -> (date_str, Path)
    for path in sorted(input_dir.glob("*.csv")):
        match = FILENAME_RE.match(path.name)
        if not match:
            print(f"  skipping (unrecognized name): {path.name}")
            continue
        file_type, iso3, date_str = match.groups()
        key = (file_type, iso3)
        if key not in candidates or date_str > candidates[key][0]:
            candidates[key] = (date_str, path)

    by_type = {file_type: [] for file_type in OUTPUT_NAMES}
    for (file_type, iso3), (date_str, path) in sorted(candidates.items()):
        by_type[file_type].append(path)
    return by_type


def read_csv_validated(path):
    """Read one CSV with Python's csv module (not pandas) so embedded literal
    newlines inside a quoted field -- e.g. a pasted-from-Word HTML blob spanning
    hundreds of lines -- are handled per RFC 4180 rather than by pandas' own
    (usually but not always reliable) quote handling. Every data row is checked
    against the header's column count: a short row is padded with empty strings
    (common -- many exports drop trailing empty commas), a long row means a
    field's closing quote never matched and content bled into extra columns --
    that row is dropped, not guessed at, and reported so the source file can be
    fixed by hand.

    Returns (DataFrame, [(row_number, actual_column_count), ...] for dropped rows).
    Columns are not dropped here even if empty in this one file -- a column
    blank for this country may hold data for another, so that check happens
    once on the fully combined data in combine_type instead.
    """
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        n_cols = len(header)
        rows = []
        dropped = []
        for row_number, row in enumerate(reader, start=2):  # header is line 1
            if len(row) == n_cols:
                rows.append(row)
            elif len(row) < n_cols:
                rows.append(row + [""] * (n_cols - len(row)))
            else:
                dropped.append((row_number, len(row)))
    df = pd.DataFrame(rows, columns=header)
    return df, dropped


def combine_type(paths):
    frames = []
    header_sets = set()
    for path in paths:
        df, dropped = read_csv_validated(path)
        header_sets.add(tuple(df.columns))
        frames.append(df)
        for row_number, actual_cols in dropped:
            print(
                f"  WARNING: {path.name} line {row_number} has {actual_cols} columns, "
                f"expected {len(df.columns)} -- likely an unclosed quote swallowing "
                f"a later line; row dropped, fix the source file to recover it"
            )

    if len(header_sets) > 1:
        print(f"  WARNING: inconsistent columns across {len(paths)} files for this type")

    combined = pd.concat(frames, ignore_index=True, sort=False)
    before = len(combined)
    combined = combined.drop_duplicates(keep="first").reset_index(drop=True)
    removed = before - len(combined)

    is_blank = combined.apply(lambda col: col.isna() | (col.astype(str).str.strip() == ""))
    blank_cols = combined.columns[is_blank.all(axis=0)]
    if len(blank_cols):
        combined = combined.drop(columns=blank_cols)

    return combined, removed, list(blank_cols)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input-dir", default="Africa_Data", help="Folder holding the per-country raw exports")
    parser.add_argument("--output-dir", default=".", help="Folder to write the three combined CSVs to")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    by_type = pick_latest_per_country(input_dir)

    for file_type, out_name in OUTPUT_NAMES.items():
        paths = by_type[file_type]
        print(f"{file_type}: {len(paths)} countries selected")
        combined, removed, blank_cols = combine_type(paths)
        if removed:
            print(f"  removed {removed} exact-duplicate row(s)")
        if blank_cols:
            print(f"  dropped {len(blank_cols)} all-blank column(s): {', '.join(blank_cols)}")
        out_path = output_dir / out_name
        combined.to_csv(out_path, index=False, encoding="utf-8-sig")
        print(f"  wrote {len(combined):,} rows x {combined.shape[1]} columns to {out_path}")


if __name__ == "__main__":
    main()
