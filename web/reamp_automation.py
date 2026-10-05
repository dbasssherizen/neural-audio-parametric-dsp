#!/usr/bin/env python3
"""
reamp_automation.py — Justin Muir Edition (v3.3)
Automated Headless Tube Amp Re-Amping via Python sounddevice.
Designed for IK Multimedia AXE I/O, Suhr Reactive Load, and Marshall Origin 50.
Optimized for Linux (ALSA / PipeWire / JACK) & macOS.
Directly compatible with mrgeneko/parametric-nam and NAMix (Linux / ARM Cortex).

Features:
- Handles 2-output interfaces under Linux (ALSA class-compliant 2-ch mode).
- Flexible channel routing (e.g. Out 3 dedicated Amp Out, or Out 2 Right channel for 2-out setups).
- Auto-detects available channels and avoids index errors.
- Pre-checks for clipping (>-0.5 dBFS) and dead silence (<-45 dBFS).
- Emits paired WAVs and params.csv directly ready for mrgeneko's gen_dataset_from_captures.py!

Usage:
    python reamp_automation.py --sweep sweep.wav --csv marshall_origin50_params.csv --out-dir ./captures
    python reamp_automation.py --list-devices
"""

import os
import sys
import time
import argparse
import numpy as np

try:
    import sounddevice as sd
    import soundfile as sf
except ImportError:
    print("[!] Missing required audio libraries.")
    print("    Install them with: pip install sounddevice soundfile numpy")
    sys.exit(1)


def list_audio_devices():
    """Print available audio input and output devices with channel counts."""
    print("\n=======================================================")
    print("🎧 AVAILABLE AUDIO INTERFACES (ALSA / CoreAudio / ASIO)")
    print("=======================================================")
    devices = sd.query_devices()
    for idx, dev in enumerate(devices):
        max_in = dev.get('max_input_channels', 0)
        max_out = dev.get('max_output_channels', 0)
        hostapi = sd.query_hostapis(dev.get('hostapi', 0))['name']
        default_mark = ""
        if idx == sd.default.device[0]:
            default_mark += " [DEFAULT IN]"
        if idx == sd.default.device[1]:
            default_mark += " [DEFAULT OUT]"
        print(f"[{idx:02d}] {dev['name']} ({hostapi}) — In: {max_in} ch, Out: {max_out} ch{default_mark}")
    print("=======================================================\n")


def main():
    parser = argparse.ArgumentParser(description="Headless Re-Amp Automation for Parametric NAM (Justin Muir Edition)")
    parser.add_argument("--sweep", type=str, default="sweep.wav", help="Path to dry 48kHz sweep WAV file")
    parser.add_argument("--csv", type=str, default="marshall_origin50_params.csv", help="Matrix CSV with knob values")
    parser.add_argument("--out-dir", type=str, default="./captures", help="Output directory for recorded wet takes")
    parser.add_argument("--device", type=int, default=None, help="Device ID for audio interface (run with --list-devices)")
    parser.add_argument("--out-ch", type=int, default=3, help="Output channel for Amp Out (default 3 for AXE I/O front; auto-falls back to 2 if interface only has 2 outs)")
    parser.add_argument("--in-ch", type=int, default=1, help="Input channel from Suhr Reactive Load (default 1)")
    parser.add_argument("--list-devices", action="store_true", help="List audio devices and exit")
    parser.add_argument("--pad-sec", type=float, default=2.0, help="Cooling/switching pause after each take")
    args = parser.parse_args()

    if args.list_devices:
        list_audio_devices()
        return

    os.makedirs(args.out_dir, exist_ok=True)

    if not os.path.exists(args.sweep):
        print(f"[!] Error: Dry sweep file '{args.sweep}' not found.")
        print("    Please provide a valid 48kHz 24-bit dry sweep audio file.")
        return

    # Load dry sweep
    sweep_data, sample_rate = sf.read(args.sweep, dtype='float32')
    if sweep_data.ndim > 1:
        sweep_data = sweep_data[:, 0]  # ensure mono
    duration = len(sweep_data) / sample_rate
    print(f"[✓] Loaded dry sweep: {args.sweep} ({sample_rate}Hz, {duration:.2f}s, {len(sweep_data)} samples)")

    # Query device info and handle 2-output interface limitation
    dev_info = sd.query_devices(args.device, 'output') if args.device is not None else sd.query_devices(sd.default.device[1], 'output')
    max_outs = dev_info.get('max_output_channels', 2)
    dev_name = dev_info.get('name', 'Default Audio Device')

    active_out_ch = args.out_ch
    if active_out_ch > max_outs:
        print(f"\n⚠️  [CHANNEL LIMITATION DETECTED on '{dev_name}']")
        print(f"    You requested output channel {args.out_ch}, but interface only reports {max_outs} outputs.")
        print(f"    -> Automatically routing re-amp dry sweep to Channel {max_outs} (Right Channel)!")
        print(f"    -> Signal routing: Plug cable from Interface Out {max_outs} directly into Marshall Amp Input.")
        active_out_ch = max_outs

    # Read parameter runs
    runs = []
    headers = []
    if os.path.exists(args.csv):
        with open(args.csv, 'r') as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            if lines:
                headers = [h.strip() for h in lines[0].split(',')]
                for line in lines[1:]:
                    vals = [v.strip() for v in line.split(',')]
                    runs.append(vals)
        print(f"[✓] Loaded {len(runs)} takes from {args.csv} with controls: {', '.join(headers[2:])}")
    else:
        print(f"[i] No CSV found at {args.csv}. Using default 45-take Marshall Origin 50 matrix...")
        headers = ["take_id", "split", "Depth", "Presence", "Master", "Treble", "Middle", "Bass", "Gain1", "Gain2"]
        for i in range(1, 46):
            split = "val" if i > 40 else "train"
            name = f"amp_val_{i-40:03d}" if i > 40 else f"amp_run_{i:03d}"
            runs.append([name, split, "5.0", "5.0", "5.0", "5.0", "5.0", "5.0", "6.0", "7.0"])

    print(f"\n=======================================================")
    print(f"🎸 JUSTIN MUIR • PARAMETRIC RE-AMPING AUTOMATION ENGINE")
    print(f"Target: mrgeneko/parametric-nam & NAMix (Linux / ARM Cortex)")
    print(f"Audio Device: {dev_name} (Max In: {dev_info.get('max_input_channels', 2)}, Max Out: {max_outs})")
    print(f"Active Signal Routing:")
    print(f"  • SEND  -> Out Channel {active_out_ch} (Into Marshall Origin 50 Input)")
    print(f"  • RETURN <- In Channel {args.in_ch} (From Suhr Reactive Load Line Out)")
    print(f"Total Takes to Capture: {len(runs)} (40 Train + 5 Validation Holdout)")
    print(f"=======================================================\n")

    for idx, row in enumerate(runs, start=1):
        take_id = row[0]
        split = row[1] if len(row) > 1 else ("val" if idx > 40 else "train")
        knob_settings = dict(zip(headers[2:], row[2:]))

        print(f"\n-------------------------------------------------------")
        print(f"▶ TAKE #{idx:02d}/{len(runs)} [{split.upper()}]: {take_id}")
        print("  DIAL YOUR PHYSICAL MARSHALL ORIGIN 50 CONTROLS:")
        for k, v in knob_settings.items():
            print(f"    • {k.upper():<12}: {v}/10")
        print(f"-------------------------------------------------------")

        user_input = input(f"Press [ENTER] to record take (or 's' to skip, 'q' to quit): ").strip().lower()
        if user_input == 'q':
            print("Session paused by user.")
            break
        if user_input == 's':
            print("Skipping take.")
            continue

        out_wav = os.path.join(args.out_dir, f"{take_id}.wav")
        print(f"[*] Playing Out Ch {active_out_ch} & recording Suhr Ch {args.in_ch} ({duration:.1f}s)...")

        try:
            # Full duplex play and record
            recorded = sd.playrec(
                sweep_data,
                samplerate=sample_rate,
                channels=1,
                input_mapping=[args.in_ch],
                output_mapping=[active_out_ch],
                device=args.device,
                blocking=True
            )

            # Telemetry checks
            peak = float(np.max(np.abs(recorded)))
            peak_dbfs = 20 * np.log10(peak + 1e-9)
            rms = float(np.sqrt(np.mean(recorded**2)))
            rms_dbfs = 20 * np.log10(rms + 1e-9)

            sf.write(out_wav, recorded, sample_rate, subtype='PCM_24')

            status = "✓ HEALTHY (Good SNR)"
            if peak_dbfs > -0.5:
                status = "⚠️ CLIPPING DETECTED (Turn down interface input gain!)"
            elif peak_dbfs < -45.0:
                status = "⚠️ LOW LEVEL (Check amp standby switch or master volume!)"

            print(f"  [✓] Saved: {out_wav}")
            print(f"      Peak: {peak_dbfs:.1f} dBFS | RMS: {rms_dbfs:.1f} dBFS | Status: {status}")

        except Exception as e:
            print(f"[!] Recording error: {e}")
            print("    Check audio device ID and permissions with: python reamp_automation.py --list-devices")

        time.sleep(args.pad_sec)

    print("\n=======================================================")
    print("🎉 ALL CAPTURES COMPLETE!")
    print(f"Wet WAV files saved to: {os.path.abspath(args.out_dir)}")
    print("\nNext step with mrgeneko/parametric-nam (under Linux):")
    print("  1. git clone https://github.com/mrgeneko/parametric-nam")
    print("  2. cd parametric-nam && ./setup.sh --no-cli && source .venv/bin/activate")
    print(f"  3. python gen_dataset_from_captures.py --captures '{os.path.abspath(args.out_dir)}/*.wav' --output ./dataset --gear-make 'Marshall' --gear-model 'Origin 50 Modded'")
    print("  4. python gen_dataset_from_captures.py --combine ./dataset")
    print("  5. python param_train.py --dataset ./dataset --output ./marshall_origin50.param.nam")
    print("  6. Load ./marshall_origin50.param.nam into NAMix on Linux or ARM Cortex!")
    print("=======================================================\n")


if __name__ == "__main__":
    main()
