#!/usr/bin/env python3
"""
reamp_automation.py - Automated Headless Re-Amping CLI for Parametric NAM
Justin Muir - 48kHz 24-bit Audio DSP Lab

Eliminates manual DAW recording, file naming, and exporting!
Plays inputTrunc.wav and records the amp output simultaneously,
advancing through the run sheet on [Enter] keypresses.

Requirements:
    pip install sounddevice soundfile numpy pandas
"""

import os
import sys
import time
import argparse
import json
import csv
import numpy as np
import soundfile as sf
import sounddevice as sd

def list_audio_devices():
    print("\n--- Available Audio Devices ---")
    devices = sd.query_devices()
    for idx, d in enumerate(devices):
        in_ch = d['max_input_channels']
        out_ch = d['max_output_channels']
        print(f"[{idx:2d}] {d['name']} (Inputs: {in_ch}, Outputs: {out_ch}, Default SR: {int(d['default_samplerate'])})")
    print("--------------------------------\n")

def generate_default_run_sheet(csv_path):
    def mulberry32(a):
        def next_rand():
            nonlocal a
            a = (a + 0x6D2B79F5) & 0xFFFFFFFF
            t = (a ^ (a >> 15)) * (a | 1) & 0xFFFFFFFF
            t = (t ^ (t + ((t ^ (t >> 7)) * (t | 61) & 0xFFFFFFFF))) & 0xFFFFFFFF
            return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296.0
        return next_rand

    def snap_val(val, step):
        return round(round(val / step) * step, 1)

    rng = mulberry32(42)
    takes = []
    # Anchor
    takes.append({
        'take_id': 'take_00', 'type': 'Anchor',
        'gain': 5.0, 'bass': 5.0, 'mid': 5.0, 'treble': 5.0, 'master': 7.0,
        'output_filename': 'take_00_anchor_G5.0_B5.0_M5.0_T5.0_M7.0.wav', 'recorded': 0
    })
    # LHS Training takes
    for i in range(1, 41):
        g = snap_val(1.0 + rng() * 9.0, 0.5)
        b = snap_val(1.0 + rng() * 9.0, 0.5)
        m = snap_val(1.0 + rng() * 9.0, 0.5)
        t = snap_val(1.0 + rng() * 9.0, 0.5)
        v = snap_val(2.0 + rng() * 8.0, 0.5)
        pad = f'{i:02d}'
        fn = f'take_{pad}_G{g:.1f}_B{b:.1f}_M{m:.1f}_T{t:.1f}_M{v:.1f}.wav'
        takes.append({
            'take_id': f'take_{pad}', 'type': 'LHS Train',
            'gain': g, 'bass': b, 'mid': m, 'treble': t, 'master': v,
            'output_filename': fn, 'recorded': 0
        })
    # Holdout Validation & Edge takes
    edges = [
        ('Holdout Val', 2.0, 6.0, 4.0, 8.0, 6.0),
        ('Holdout Val', 7.5, 3.0, 7.0, 5.5, 7.0),
        ('Extreme Edge', 10.0, 2.0, 8.0, 9.0, 5.0),
        ('Extreme Edge', 8.5, 9.5, 1.0, 4.0, 6.0)
    ]
    for e_type, eg, eb, em, et, ev in edges:
        pad = f'{len(takes):02d}'
        fn = f'take_{pad}_{e_type.lower().replace(" ", "_")}_G{eg}_B{eb}_M{em}_T{et}_M{ev}.wav'
        takes.append({
            'take_id': f'take_{pad}', 'type': e_type,
            'gain': eg, 'bass': eb, 'mid': em, 'treble': et, 'master': ev,
            'output_filename': fn, 'recorded': 0
        })

    fieldnames = ['take_id', 'type', 'gain', 'bass', 'mid', 'treble', 'master', 'output_filename', 'recorded']
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(takes)
    print(f"✅ Auto-generated '{csv_path}' with {len(takes)} takes ready.")

def run_automation(sweep_file, run_sheet_csv, output_dir, in_ch, out_ch, device_idx=None):
    if not os.path.exists(sweep_file):
        sys.exit(f"❌ Sweep file not found: {sweep_file}. Make sure inputTrunc.wav is in this directory.")

    if not os.path.exists(run_sheet_csv):
        print(f"ℹ️ Run sheet '{run_sheet_csv}' not found. Auto-generating standard 45-take Latin Hypercube run sheet...")
        generate_default_run_sheet(run_sheet_csv)

    os.makedirs(output_dir, exist_ok=True)

    # 1. Load Sweep WAV
    sweep_data, sr = sf.read(sweep_file, dtype='float32')
    if sweep_data.ndim > 1:
        sweep_data = sweep_data[:, 0] # convert to mono
    
    print(f"✅ Loaded sweep: {sweep_file} ({len(sweep_data)} samples @ {sr}Hz = {len(sweep_data)/sr:.1f}s)")
    if sr != 48000:
        print(f"⚠️ Warning: Sample rate is {sr}Hz, NAM expects 48000Hz!")

    # 2. Load Run Sheet
    with open(run_sheet_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        takes_list = list(reader)
    total_takes = len(takes_list)
    print(f"📋 Loaded {total_takes} takes from {run_sheet_csv}")

    # Set audio device if provided
    if device_idx is not None:
        sd.default.device = device_idx
        print(f"🎛️ Audio Device set to [{device_idx}]: {sd.query_devices(device_idx)['name']}")

    print("\n=======================================================")
    print("🎸 AUTOMATED PARAMETRIC RE-AMPING WORKFLOW ACTIVATED")
    print("=======================================================")
    print(f"• Output Channel: {out_ch} (Connect to Re-Amp Box -> Amp Input)")
    print(f"• Input Channel:  {in_ch} (Connect to Mic Preamp / Load Box)")
    print("• Workflow: Dial knobs on your amp -> Press [Enter] -> Take records -> Repeats!\n")

    manifest_entries = []

    for idx, row in enumerate(takes_list):
        take_id = row.get("take_id", f"take_{idx:02d}")
        take_type = row.get("type", "Train")
        g = float(row.get("gain", 5.0))
        b = float(row.get("bass", 5.0))
        m = float(row.get("mid", 5.0))
        t = float(row.get("treble", 5.0))
        v = float(row.get("master", 7.0))
        
        target_filename = row.get("output_filename", f"{take_id}.wav")
        out_filepath = os.path.join(output_dir, target_filename)

        # Check if already recorded
        if os.path.exists(out_filepath):
            print(f"⏩ [{idx+1}/{total_takes}] {take_id} already exists ({target_filename}). Skipping...")
            manifest_entries.append({
                "val": [round(g/10.0, 3), round(b/10.0, 3), round(m/10.0, 3), round(t/10.0, 3), round(v/10.0, 3)],
                "path": target_filename,
                "is_validation": "holdout" in str(take_type).lower()
            })
            continue

        print(f"\n-------------------------------------------------------")
        print(f"📍 TAKE [{idx+1}/{total_takes}]: {take_id} ({take_type})")
        print(f"🎛️  DIAL KNOBS ON AMP:")
        print(f"   ▶ GAIN:   {g:4.1f} / 10")
        print(f"   ▶ BASS:   {b:4.1f} / 10")
        print(f"   ▶ MID:    {m:4.1f} / 10")
        print(f"   ▶ TREBLE: {t:4.1f} / 10")
        print(f"   ▶ MASTER: {v:4.1f} / 10")
        print(f"-------------------------------------------------------")
        
        try:
            input("Press [ENTER] when knobs are dialed to trigger re-amp sweep... (Ctrl+C to pause)")
        except KeyboardInterrupt:
            print("\n⏸️ Paused session. You can re-run this script anytime and it will resume right here!")
            break

        print(f"🔴 RECORDING... ({len(sweep_data)/sr:.1f}s) Playing to Out {out_ch} & Recording from In {in_ch}...")
        
        # Prepare playback buffer (multichannel if needed)
        max_out = sd.query_devices(sd.default.device[1] if isinstance(sd.default.device, (list, tuple)) else sd.default.device)['max_output_channels']
        play_buf = np.zeros((len(sweep_data), max(out_ch, max_out)), dtype='float32')
        play_buf[:, out_ch - 1] = sweep_data

        # Record buffer
        rec_data = sd.playrec(play_buf, samplerate=sr, channels=max(in_ch, 2), dtype='float32')
        sd.wait()

        # Extract recorded channel
        take_audio = rec_data[:, in_ch - 1]

        # Check for signal presence (prevent silent takes)
        rms = np.sqrt(np.mean(take_audio**2))
        peak = np.max(np.abs(take_audio))
        if peak < 0.001:
            print(f"⚠️ WARNING: Recorded audio is nearly silent! (Peak: {peak:.4f}). Check your cable routing.")
        else:
            print(f"✓ Recorded successfully! Peak: {peak:.2f} ({20*np.log10(peak+1e-6):.1f}dBFS)")

        # Save WAV
        sf.write(out_filepath, take_audio, sr, subtype='PCM_24')
        print(f"💾 Saved -> {out_filepath}")

        manifest_entries.append({
            "val": [round(g/10.0, 3), round(b/10.0, 3), round(m/10.0, 3), round(t/10.0, 3), round(v/10.0, 3)],
            "path": target_filename,
            "is_validation": "holdout" in str(take_type).lower()
        })

    # 3. Generate data.json manifest
    if manifest_entries:
        data_json_path = os.path.join(output_dir, "data.json")
        manifest = {
            "x": sweep_file,
            "sample_rate": sr,
            "y": manifest_entries
        }
        with open(data_json_path, "w") as f:
            json.dump(manifest, f, indent=2)
        print(f"\n🎉 ALL SET! Generated {data_json_path} with {len(manifest_entries)} takes mapped!")
        print(f"📦 Ready to zip and send offsite to Colab or run locally:")
        print(f"   nam-full-parametric {data_json_path} configs/model_concat.json configs/learning_concat.json ./output/")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automated Headless Re-Amping CLI for Parametric NAM")
    parser.add_argument("--list-devices", action="store_true", help="List audio input/output devices and exit")
    parser.add_argument("--sweep", default="inputTrunc.wav", help="Path to input calibration sweep WAV (default: inputTrunc.wav)")
    parser.add_argument("--csv", default="justin_nam_run_sheet.csv", help="Path to run sheet CSV (default: justin_nam_run_sheet.csv)")
    parser.add_argument("--outdir", default="./takes", help="Directory to save recorded takes (default: ./takes)")
    parser.add_argument("--in-ch", type=int, default=1, help="Audio interface input channel number (1-based, default: 1)")
    parser.add_argument("--out-ch", type=int, default=3, help="Audio interface output channel number to re-amp box (1-based, default: 3)")
    parser.add_argument("--device", type=int, default=None, help="Audio device index (run --list-devices to find)")
    args = parser.parse_args()

    if args.list_devices:
        list_audio_devices()
        sys.exit(0)

    run_automation(args.sweep, args.csv, args.outdir, args.in_ch, args.out_ch, args.device)
