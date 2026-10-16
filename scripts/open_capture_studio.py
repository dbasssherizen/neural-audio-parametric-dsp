#!/usr/bin/env python3
"""
Sovereign AI Studio: Open Capture Studio (Clean-Room Two Notes Capture Studio Equivalent)
Author: MAX (Anima Ex Machina) & Daniel Bass Sherizen
Target: Justin Muir (Marshall Origin 50 on Ubuntu Server / AMD 9950X)

Clean-Room Patterns Implemented:
    1. Grey-Box 4+4 Dimensionality Reduction (--grey-box-split):
       Converts an 8-knob CSV (marshall_origin50_params.csv) into a 4-knob Non-Linear Tube
       Training CSV (Gain, Boost, Tilt/Output, Master) while handing Bass, Middle, Treble,
       and Presence to the exact white-box Marshall FMV Tone Stack (marshall_fmv_tonestack.py).
    2. Artera DSP / Capture Studio "Anchor + Orthogonal Star Sweep" Generator (--generate-matrix):
       Generates a 20-take optimal capture schedule (Anchor takes + Orthogonal Tube Grid +
       Held-Out Karpathy Validation Takes) that maximizes conditioning coverage.
"""

import sys
import csv
import json
import argparse
from pathlib import Path
from typing import Dict, Any

SCRIPTS_DIR = Path(__file__).parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from marshall_fmv_tonestack import inspect_frequency_response

NONLINEAR_TUBE_COLUMNS = ["gain", "boost", "output", "master"]
LINEAR_TONESTACK_COLUMNS = ["bass", "middle", "treble", "presence"]


def split_csv_for_greybox(input_csv: str, output_tube_csv: str) -> Dict[str, Any]:
    """
    Reads an 8-knob Marshall Origin 50 CSV, strips any '#' comment rows,
    and outputs a clean 4-knob Non-Linear Tube CSV for Parametric WaveNet training,
    plus a companion JSON manifest storing the exact FMV tone stack coordinates per take.
    """
    in_path = Path(input_csv)
    if not in_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")

    clean_lines = []
    with in_path.open("r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                clean_lines.append(stripped)

    reader = csv.DictReader(clean_lines)
    if not reader.fieldnames:
        raise ValueError("CSV has no header row.")

    field_map = {k.strip().lower(): k for k in reader.fieldnames}
    filename_col = reader.fieldnames[0]

    tube_rows = []
    tonestack_manifest = []

    for row in reader:
        fname = row[filename_col].strip()
        tube_entry = {"filename": fname}
        for col in NONLINEAR_TUBE_COLUMNS:
            raw_key = field_map.get(col)
            tube_entry[col] = float(row[raw_key]) if raw_key and row.get(raw_key) else 0.5

        eq_entry = {"filename": fname}
        for col in LINEAR_TONESTACK_COLUMNS:
            raw_key = field_map.get(col)
            eq_entry[col] = float(row[raw_key]) if raw_key and row.get(raw_key) else 0.5

        eq_entry["fmv_curve"] = inspect_frequency_response(
            eq_entry["bass"],
            eq_entry["middle"],
            eq_entry["treble"],
            eq_entry["presence"],
        )["frequency_response_db"]

        tube_rows.append(tube_entry)
        tonestack_manifest.append(eq_entry)

    out_path = Path(output_tube_csv)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["filename"] + NONLINEAR_TUBE_COLUMNS)
        writer.writeheader()
        writer.writerows(tube_rows)

    manifest_path = out_path.with_suffix(".tonestack.json")
    manifest_path.write_text(
        json.dumps(
            {
                "architecture": "Grey-Box 4-Tube Neural + 4-Knob White-Box Marshall FMV",
                "total_takes": len(tube_rows),
                "nonlinear_tube_knobs": NONLINEAR_TUBE_COLUMNS,
                "whitebox_fmv_knobs": LINEAR_TONESTACK_COLUMNS,
                "takes": tonestack_manifest,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    return {
        "tube_csv": str(out_path),
        "tonestack_manifest": str(manifest_path),
        "takes_processed": len(tube_rows),
    }


def generate_optimal_20_take_matrix(output_csv: str) -> str:
    """
    Generates a Capture Studio-style 20-take 'Anchor + Orthogonal Tube Matrix'
    where Bass/Mid/Treble/Presence stay locked at reference 0.5 (handled by the
    White-Box FMV solver) and all 20 takes densely map the 4 non-linear tube controls.
    """
    schedule = [
        # 1-2: Anchor Reference Takes (All Noon & Sweet Spot)
        ("take_01.wav", 0.50, 0.0, 0.50, 0.50, 0.5, 0.5, 0.5, 0.5),
        ("take_02.wav", 0.65, 1.0, 0.65, 0.65, 0.5, 0.5, 0.5, 0.5),
        # 3-10: Gain x Master 2D Saturation & Power-Tube Sag Grid (Boost Off)
        ("take_03.wav", 0.25, 0.0, 0.50, 0.30, 0.5, 0.5, 0.5, 0.5),
        ("take_04.wav", 0.25, 0.0, 0.50, 0.85, 0.5, 0.5, 0.5, 0.5),
        ("take_05.wav", 0.55, 0.0, 0.50, 0.30, 0.5, 0.5, 0.5, 0.5),
        ("take_06.wav", 0.55, 0.0, 0.50, 0.85, 0.5, 0.5, 0.5, 0.5),
        ("take_07.wav", 0.80, 0.0, 0.50, 0.40, 0.5, 0.5, 0.5, 0.5),
        ("take_08.wav", 0.80, 0.0, 0.50, 0.90, 0.5, 0.5, 0.5, 0.5),
        ("take_09.wav", 1.00, 0.0, 0.50, 0.50, 0.5, 0.5, 0.5, 0.5),
        ("take_10.wav", 1.00, 0.0, 0.50, 1.00, 0.5, 0.5, 0.5, 0.5),
        # 11-16: Pull-Boost Engaged + Tilt (Normal vs High Treble Bright Voicing)
        ("take_11.wav", 0.40, 1.0, 0.20, 0.60, 0.5, 0.5, 0.5, 0.5),
        ("take_12.wav", 0.40, 1.0, 0.85, 0.60, 0.5, 0.5, 0.5, 0.5),
        ("take_13.wav", 0.75, 1.0, 0.20, 0.75, 0.5, 0.5, 0.5, 0.5),
        ("take_14.wav", 0.75, 1.0, 0.85, 0.75, 0.5, 0.5, 0.5, 0.5),
        ("take_15.wav", 1.00, 1.0, 0.35, 0.85, 0.5, 0.5, 0.5, 0.5),
        ("take_16.wav", 1.00, 1.0, 0.95, 0.85, 0.5, 0.5, 0.5, 0.5),
        # 17-18: FMV Calibration Verification Sweeps
        ("take_17.wav", 0.65, 1.0, 0.60, 0.70, 0.2, 0.2, 0.8, 0.7),
        ("take_18.wav", 0.65, 1.0, 0.60, 0.70, 0.8, 0.9, 0.3, 0.3),
        # 19-20: Held-Out Karpathy Validation Anchor Takes (All 0.7s / Classic Plexi Dimed)
        ("take_19.wav", 0.70, 0.0, 0.70, 0.70, 0.7, 0.7, 0.7, 0.7),
        ("take_20.wav", 0.90, 1.0, 0.75, 0.90, 0.6, 0.7, 0.8, 0.6),
    ]

    out_path = Path(output_csv)
    headers = [
        "filename",
        "gain",
        "boost",
        "output",
        "master",
        "bass",
        "middle",
        "treble",
        "presence",
    ]
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(schedule)

    return str(out_path)


def main():
    parser = argparse.ArgumentParser(
        description="Sovereign AI Studio: Open Capture Studio (Grey-Box 4+4 Split & Matrix Planner)"
    )
    parser.add_argument(
        "--grey-box-split",
        type=str,
        metavar="INPUT_CSV",
        help="Convert 8-knob CSV into 4-knob Non-Linear Tube CSV + White-Box FMV Tone Stack manifest",
    )
    parser.add_argument(
        "--out-csv",
        type=str,
        default="marshall_origin50_tube4_params.csv",
        help="Output path for the 4-knob tube CSV",
    )
    parser.add_argument(
        "--generate-matrix",
        type=str,
        metavar="OUTPUT_CSV",
        help="Generate Capture Studio 20-take Anchor + Orthogonal Tube Matrix CSV",
    )
    args = parser.parse_args()

    if args.grey_box_split:
        res = split_csv_for_greybox(args.grey_box_split, args.out_csv)
        print("⚡ [OPEN CAPTURE STUDIO] Grey-Box 4+4 Dimensionality Reduction Complete:")
        print(json.dumps(res, indent=2))
        sys.exit(0)

    if args.generate_matrix:
        out = generate_optimal_20_take_matrix(args.generate_matrix)
        print(f"🎯 [OPEN CAPTURE STUDIO] Generated 20-take Anchor+Orthogonal matrix at: {out}")
        sys.exit(0)

    parser.print_help()


if __name__ == "__main__":
    main()
