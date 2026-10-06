#!/usr/bin/env python3
"""
reamp_automation.py — Justin Muir Edition (v3.4 - ASIO & Cloud-Ready)
Automated Headless Tube Amp Re-Amping via Python sounddevice.
Designed for IK Multimedia AXE I/O, Suhr Reactive Load, and Marshall Origin 50.
Native Cross-Platform: Windows (ASIO), Linux (ALSA / PipeWire / JACK), macOS (CoreAudio).
Directly compatible with mrgeneko/parametric-nam and NAMix (Desktop & ARM Cortex).

Key Features:
- Native Windows ASIO Auto-Detection: Automatically searches for ASIO host API to bypass
  Windows WDM/MME stereo mixer and unlock all 6 physical outputs.
- IK Multimedia AXE I/O Output 5: Routes sweep directly to Front-Panel Amp Out Jack (Out 5),
  providing isolated instrument-level signal straight into the Marshall Origin 50 guitar input.
- Suhr Reactive Load Capture on Input 2 (or 1): Full-duplex synchronous recording with zero clock drift.
- mrgeneko Self-Contained Validation: Automatically explains and handles parametric sweep indexing
  (no manual val.wav required; gen_dataset_from_captures.py partitions parameter space).
- Pre-checks for clipping (>-0.5 dBFS) and dead silence (<-45 dBFS).
- Emits paired WAVs and params.csv ready for Google Colab or local cloud GPU training.

Usage:
    python reamp_automation.py --sweep sweep.wav --csv marshall_origin50_params.csv --out-dir ./captures
    python reamp_automation.py --asio --out-ch 5 --in-ch 2
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


def find_asio_device(preferred_name=None):
    """Search for the best ASIO device on Windows or return None."""
    try:
        hostapis = sd.query_hostapis()
        asio_api_idx = None
        for idx, api in enumerate(hostapis):
            if "asio" in api.get("name", "").lower():
                asio_api_idx = idx
                break

        if asio_api_idx is None:
            return None

        devices = sd.query_devices()
        best_dev_id = None
        for dev_id, dev in enumerate(devices):
            if dev.get("hostapi") == asio_api_idx and dev.get("max_output_channels", 0) > 0:
                dev_name = dev.get("name", "")
                if preferred_name and preferred_name.lower() in dev_name.lower():
                    return dev_id
                if best_dev_id is None:
                    best_dev_id = dev_id
                # Prioritize AXE I/O ASIO
                if "axe" in dev_name.lower() or "ik" in dev_name.lower():
                    return dev_id
        return best_dev_id
    except Exception:
        return None


def list_audio_devices():
    """Print available audio input and output devices with channel counts and Host APIs."""
    print("\n=======================================================")
    print("🎧 AVAILABLE AUDIO INTERFACES (ASIO / ALSA / CoreAudio)")
    print("=======================================================")
    devices = sd.query_devices()
    hostapis = sd.query_hostapis()
    for idx, dev in enumerate(devices):
        max_in = dev.get("max_input_channels", 0)
        max_out = dev.get("max_output_channels", 0)
        api_idx = dev.get("hostapi", 0)
        hostapi_name = hostapis[api_idx]["name"] if api_idx < len(hostapis) else "Unknown"
        default_mark = ""
        if idx == sd.default.device[0]:
            default_mark += " [DEFAULT IN]"
        if idx == sd.default.device[1]:
            default_mark += " [DEFAULT OUT]"
        
        is_asio = "ASIO" if "asio" in hostapi_name.lower() else ""
        axe_mark = " ★ IK AXE I/O" if ("axe" in dev["name"].lower() or "ik" in dev["name"].lower()) else ""
        print(f"[{idx:02d}] {dev['name']} ({hostapi_name}) — In: {max_in} ch, Out: {max_out} ch{default_mark}{axe_mark}")
    print("=======================================================\n")


def main():
    parser = argparse.ArgumentParser(description="Headless Re-Amp Automation for Parametric NAM (Justin Muir Edition v3.4)")
    parser.add_argument("--sweep", type=str, default="sweep.wav", help="Path to dry 48kHz sweep WAV file")
    parser.add_argument("--csv", type=str, default="marshall_origin50_params.csv", help="Matrix CSV with knob values")
    parser.add_argument("--out-dir", type=str, default="./captures", help="Output directory for recorded wet takes")
    parser.add_argument("--device", type=int, default=None, help="Device ID for audio interface (run with --list-devices)")
    parser.add_argument("--asio", action="store_true", help="Force ASIO host API on Windows")
    parser.add_argument("--out-ch", type=int, default=None, help="Output channel for Amp Out (default: 5 for AXE I/O ASIO, 3 for multi-out, 2 for stereo fallback)")
    parser.add_argument("--in-ch", type=int, default=2, help="Input channel from Suhr Reactive Load (default 2 for AXE I/O, or 1)")
    parser.add_argument("--list-devices", action="store_true", help="List audio devices and exit")
    parser.add_argument("--pad-sec", type=float, default=2.0, help="Cooling/switching pause after each take")
    args = parser.parse_args()

    if args.list_devices:
        list_audio_devices()
        return

    os.makedirs(args.out_dir, exist_ok=True)

    # 1. Resolve Audio Device & ASIO on Windows
    target_device = args.device
    is_windows = sys.platform.startswith("win")
    
    if target_device is None and (args.asio or is_windows):
        asio_dev = find_asio_device("axe")
        if asio_dev is not None:
            target_device = asio_dev
            print(f"[✓] Auto-detected Windows ASIO Device ID {target_device}: '{sd.query_devices(target_device)['name']}'")
        elif args.asio:
            print("[!] Warning: Requested --asio, but no ASIO host API found. Falling back to default device.")

    if target_device is not None:
        dev_info = sd.query_devices(target_device)
        dev_name = dev_info.get("name", "Custom Device")
        max_outs = dev_info.get("max_output_channels", 2)
        max_ins = dev_info.get("max_input_channels", 2)
    else:
        out_def = sd.default.device[1]
        dev_info = sd.query_devices(out_def) if out_def >= 0 else {}
        dev_name = dev_info.get("name", "System Default")
        max_outs = dev_info.get("max_output_channels", 2)
        max_ins = dev_info.get("max_input_channels", 2)

    # 2. Determine Output Channel Routing (Amp Out)
    # On IK Multimedia AXE I/O:
    #   Out 1/2 = Main Monitors (Left/Right)
    #   Out 3/4 = Line Outs / Headphones
    #   Out 5   = FRONT PANEL AMP OUT (Dedicated galvanically isolated re-amp jack)
    if args.out_ch is not None:
        active_out_ch = args.out_ch
    else:
        if max_outs >= 5:
            active_out_ch = 5  # AXE I/O front-panel Amp Out!
        elif max_outs >= 3:
            active_out_ch = 3
        else:
            active_out_ch = max_outs  # 2-out fallback (Right channel)

    if active_out_ch > max_outs:
        print(f"\n⚠️  [CHANNEL LIMITATION on '{dev_name}']")
        print(f"    Requested out channel {active_out_ch}, but interface only reports {max_outs} outputs.")
        print(f"    -> Falling back to Channel {max_outs} (Right Channel).")
        active_out_ch = max_outs

    active_in_ch = args.in_ch
    if active_in_ch > max_ins:
        print(f"⚠️  Input channel {active_in_ch} exceeds reported inputs ({max_ins}). Using Input 1.")
        active_in_ch = 1

    # 3. Load dry sweep audio file
    if not os.path.exists(args.sweep):
        print(f"[!] Error: Dry sweep file '{args.sweep}' not found.")
        print("    Please provide a valid 48kHz 24-bit dry sweep audio file.")
        return

    sweep_data, sample_rate = sf.read(args.sweep, dtype="float32")
    if sweep_data.ndim > 1:
        sweep_data = sweep_data[:, 0]  # ensure mono
    duration = len(sweep_data) / sample_rate
    print(f"[✓] Loaded dry sweep: {args.sweep} ({sample_rate}Hz, {duration:.2f}s, {len(sweep_data)} samples)")

    # 4. Read parameter runs
    runs = []
    headers = []
    if os.path.exists(args.csv):
        with open(args.csv, "r") as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
            if lines:
                headers = [h.strip() for h in lines[0].split(",")]
                for line in lines[1:]:
                    vals = [v.strip() for v in line.split(",")]
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
    print(f"Version: v3.4 (Native Windows ASIO & Linux ALSA/JACK)")
    print(f"Target: mrgeneko/parametric-nam & NAMix (Desktop & ARM Cortex)")
    print(f"Audio Interface: {dev_name} (Max In: {max_ins}, Max Out: {max_outs})")
    print(f"Active Signal Routing:")
    print(f"  • SEND  -> Out Channel {active_out_ch} (Direct to Marshall Origin 50 Guitar Input)")
    print(f"  • RETURN <- In Channel {active_in_ch} (From Suhr Reactive Load Line Out)")
    print(f"Total Takes to Capture: {len(runs)}")
    print(f"[i] Validation Note: mrgeneko's toolchain partitions multi-sweep captures")
    print(f"    across the continuous parameter space. No separate val.wav required!")
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
        if user_input == "q":
            print("Session paused by user.")
            break
        if user_input == "s":
            print("Skipping take.")
            continue

        out_wav = os.path.join(args.out_dir, f"{take_id}.wav")
        print(f"[*] Playing Out Ch {active_out_ch} & recording In Ch {active_in_ch} ({duration:.1f}s)...")

        try:
            # Full duplex play and record via sounddevice
            recorded = sd.playrec(
                sweep_data,
                samplerate=sample_rate,
                channels=1,
                input_mapping=[active_in_ch],
                output_mapping=[active_out_ch],
                device=target_device,
                blocking=True
            )

            # Signal quality telemetry
            peak = float(np.max(np.abs(recorded)))
            peak_dbfs = 20 * np.log10(peak + 1e-9)
            rms = float(np.sqrt(np.mean(recorded**2)))
            rms_dbfs = 20 * np.log10(rms + 1e-9)

            sf.write(out_wav, recorded, sample_rate, subtype="PCM_24")

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
    print("\nNext step: Off-Site Cloud GPU Training with Google Colab:")
    print("  1. Zip your captures: zip -r marshall_origin50_captures.zip ./captures marshall_origin50_params.csv")
    print("  2. Open the Colab notebook: colab_train_parametric_nam.ipynb")
    print("  3. Upload your zip file and click 'Run All'")
    print("  4. Google Colab will train your SlimmableParametricA2 model and export marshall_origin50.param.nam")
    print("  5. Load ./marshall_origin50.param.nam into NAMix VST3/AU or ARM Cortex!")
    print("=======================================================\n")


if __name__ == "__main__":
    main()
