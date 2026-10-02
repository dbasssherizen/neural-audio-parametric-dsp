#!/usr/bin/env python3
"""
generate_run_sheet.py - Sampling Matrix & data.json Manifest Generator for Parametric NAM
Justin Muir - 48kHz 24-bit Audio DSP Lab

Generates:
1. 'data/justin_nam_run_sheet.csv': 45-take Latin Hypercube tracking run sheet for REAPER / Python.
2. 'data/data.json': Training manifest mapping rendered WAV takes to normalized [0.0, 1.0] knob coordinates.
"""

import os
import sys
import json
import csv
import argparse

def mulberry32(a):
    """Deterministic, fast seeded PRNG for consistent run sheet generation."""
    def next_rand():
        nonlocal a
        a = (a + 0x6D2B79F5) & 0xFFFFFFFF
        t = (a ^ (a >> 15)) * (a | 1) & 0xFFFFFFFF
        t = (t ^ (t + ((t ^ (t >> 7)) * (t | 61) & 0xFFFFFFFF))) & 0xFFFFFFFF
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296.0
    return next_rand

def snap_val(val, step=0.5):
    return round(round(val / step) * step, 1)

def generate_matrix(num_train=40, seed=42, step=0.5):
    rng = mulberry32(seed)
    takes = []

    # 1. Center Anchor Take (All Knobs at Noon = 5.0, Master 7.0)
    takes.append({
        'take_id': 'take_00',
        'type': 'Anchor',
        'gain': 5.0, 'bass': 5.0, 'mid': 5.0, 'treble': 5.0, 'master': 7.0,
        'output_filename': 'take_00_anchor_G5.0_B5.0_M5.0_T5.0_M7.0.wav',
        'is_validation': False,
        'recorded': 0
    })

    # 2. Latin Hypercube Training Takes (40 points across 5D space)
    for i in range(1, num_train + 1):
        g = snap_val(1.0 + rng() * 9.0, step)
        b = snap_val(1.0 + rng() * 9.0, step)
        m = snap_val(1.0 + rng() * 9.0, step)
        t = snap_val(1.0 + rng() * 9.0, step)
        v = snap_val(2.0 + rng() * 8.0, step)
        pad = f"{i:02d}"
        fn = f"take_{pad}_G{g:.1f}_B{b:.1f}_M{m:.1f}_T{t:.1f}_M{v:.1f}.wav"
        takes.append({
            'take_id': f"take_{pad}",
            'type': 'LHS Train',
            'gain': g, 'bass': b, 'mid': m, 'treble': t, 'master': v,
            'output_filename': fn,
            'is_validation': False,
            'recorded': 0
        })

    # 3. Holdout Validation & Extreme Edge Takes (4 takes)
    edges = [
        ('Holdout Val', 2.0, 6.0, 4.0, 8.0, 6.0, True),
        ('Holdout Val', 7.5, 3.0, 7.0, 5.5, 7.0, True),
        ('Extreme Edge', 10.0, 2.0, 8.0, 9.0, 5.0, False),
        ('Extreme Edge', 8.5, 9.5, 1.0, 4.0, 6.0, False)
    ]
    for e_type, eg, eb, em, et, ev, is_val in edges:
        pad = f"{len(takes):02d}"
        fn = f"take_{pad}_{e_type.lower().replace(' ', '_')}_G{eg}_B{eb}_M{em}_T{et}_M{ev}.wav"
        takes.append({
            'take_id': f"take_{pad}",
            'type': e_type,
            'gain': eg, 'bass': eb, 'mid': em, 'treble': et, 'master': ev,
            'output_filename': fn,
            'is_validation': is_val,
            'recorded': 0
        })

    return takes

def write_csv(takes, csv_path):
    os.makedirs(os.path.dirname(os.path.abspath(csv_path)), exist_ok=True)
    fieldnames = ['take_id', 'type', 'gain', 'bass', 'mid', 'treble', 'master', 'output_filename', 'is_validation', 'recorded']
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(takes)
    print(f"✅ Generated Run Sheet CSV: {csv_path} ({len(takes)} takes)")

def write_data_json(takes, json_path, wav_dir="./takes", input_file="inputTrunc.wav", sample_rate=48000):
    os.makedirs(os.path.dirname(os.path.abspath(json_path)), exist_ok=True)
    y_entries = []
    for t in takes:
        wav_path = os.path.join(wav_dir, t['output_filename'])
        # Normalize knob coordinates between 0.0 and 1.0
        normalized_coords = [
            round(t['gain'] / 10.0, 3),
            round(t['bass'] / 10.0, 3),
            round(t['mid'] / 10.0, 3),
            round(t['treble'] / 10.0, 3),
            round(t['master'] / 10.0, 3)
        ]
        y_entries.append({
            "val": normalized_coords,
            "path": wav_path,
            "is_validation": t.get('is_validation', False)
        })

    manifest = {
        "x": os.path.join(wav_dir, input_file),
        "sample_rate": sample_rate,
        "y": y_entries
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    val_count = sum(1 for e in y_entries if e['is_validation'])
    train_count = len(y_entries) - val_count
    print(f"✅ Generated PyTorch Manifest: {json_path}")
    print(f"   Total Takes: {len(y_entries)} | Training: {train_count} | Validation Holdouts: {val_count}")

def main():
    parser = argparse.ArgumentParser(description="Generate Parametric NAM run sheet CSV and data.json manifest.")
    parser.add_argument("--takes", type=int, default=40, help="Number of Latin Hypercube training points (default: 40)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for sampling (default: 42)")
    parser.add_argument("--step", type=float, default=0.5, help="Knob dial rounding step (default: 0.5)")
    parser.add_argument("--csv", type=str, default="data/justin_nam_run_sheet.csv", help="Output CSV path")
    parser.add_argument("--json", type=str, default="data/data.json", help="Output JSON path")
    parser.add_argument("--wav-dir", type=str, default="./takes", help="Directory where recorded WAVs will reside")
    args = parser.parse_args()

    takes = generate_matrix(num_train=args.takes, seed=args.seed, step=args.step)
    write_csv(takes, args.csv)
    write_data_json(takes, args.json, wav_dir=args.wav_dir)

if __name__ == "__main__":
    main()
