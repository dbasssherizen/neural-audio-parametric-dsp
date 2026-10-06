# Justin Muir • Parametric NAM & NAMix Workflow Guide
### Featuring `mrgeneko/parametric-nam` & NAMix for Linux / ARM Cortex
### Hardware: IK Multimedia AXE I/O, Suhr Reactive Load, and Marshall Origin 50 (Modded)

## 1. Overview
This guide provides the complete end-to-end toolchain for turning physical tube amp re-amp sweeps into a fully continuous, parametric Neural Amp Modeler model (`.param.nam`), runnable with interactive live knobs in **NAMix** on macOS, Windows, Linux, and ARM Cortex (Raspberry Pi / Mod Dwarf / Elk Audio OS).

---

## 2. Hardware Signal Chain & Linux Audio Configuration

### Why Linux is Ideal for Parametric NAM:
- Windows often fails when building certain scientific Python C-extensions (like `spicelib`, `torch` custom ops, or audio drivers) without a full Visual Studio MSVC environment.
- Linux provides native, rock-solid ALSA and PipeWire audio subsystems with low-latency kernel scheduling.

### Hardware Wiring:
```
[Linux PC / Mac]
       │
       ▼ (Line Out: Ch 3 Dedicated Amp Out, OR Ch 2 Right if 2-Out mode)
[IK Multimedia AXE I/O] ───(AMP OUT / OUT 2)───[Mogami Platinum]──▶ [Marshall Origin 50 Input]
                                                                                │
                                                                                ▼ (Speaker Out: 16-AWG)
[IK Multimedia AXE I/O] ◀──────(Line In 1: 1/4" TRS)────────────────── [Suhr Reactive Load]
```

### Addressing the 2-Output vs 6-Output Limitation on Linux:
If your Linux kernel's standard USB Audio Class driver exposes the AXE I/O as a **2-output stereo interface** (`hw:CARD,0` with Channels 1 & 2):
1. **Channel 1 (Left)**: Your studio monitors or headphones (to monitor the sweep and system audio).
2. **Channel 2 (Right)**: Dedicated **Amp Send**. Connect a balanced/unbalanced cable from **Output 2 (Right)** directly into the **Marshall Origin 50 Input**.
3. **If Multi-Channel is enabled**: The front-panel **AMP OUT** jack corresponds to **Output Channel 3**.
4. In `reamp_automation.py`, the script automatically detects your interface:
   - If 6 channels are found, it uses **Channel 3 (Amp Out)**.
   - If only 2 channels are found, it gracefully switches to **Channel 2 (Right Out)** and alerts you on screen!

---

## 3. Capturing the 45 Takes

### Option A: Headless Python DAW-less Re-Amper (Recommended on Linux)
Run:
```bash
python reamp_automation.py --sweep sweep.wav --csv marshall_origin50_params.csv --out-dir ./captures
```
- List available audio devices:
  ```bash
  python reamp_automation.py --list-devices
  ```
- Override specific device or output channel:
  ```bash
  python reamp_automation.py --device 2 --out-ch 2 --in-ch 1
  ```
- The script displays the exact knob positions for the Marshall Origin 50, waits for you to turn the physical knobs, verifies levels, and saves `amp_run_001.wav` ... `amp_run_040.wav` (Training) and `amp_val_001.wav` ... `amp_val_005.wav` (Holdout Validation).

### Option B: REAPER ReaScript v3.2 (With Auto-Sweep Tiling)
1. Open REAPER.
2. Track 1 = `SWEEP_PLAYBACK` (Insert `input_trunc.wav` at `0.0s`).
3. Track 2 = `AMP_RECORD` (Input: AXE I/O Ch 1 from Suhr Load. Arm track).
4. Run `Reaper_AutoReamp_NAM.lua` (bind to `F1`).
5. **Auto-Tile Feature**: The script will automatically clone the dry sweep across all 45 take positions on Track 1—no manual dragging or copy/pasting required!

---

## 4. Training with `mrgeneko/parametric-nam`

The `mrgeneko/parametric-nam` repo is the premier toolchain for training parametric models:
- Repository: https://github.com/mrgeneko/parametric-nam

### Setup on Linux:
```bash
git clone https://github.com/mrgeneko/parametric-nam
cd parametric-nam
./setup.sh --no-cli
source .venv/bin/activate
```

### Dataset Building (from real WAV captures):
```bash
python gen_dataset_from_captures.py \
    --captures "./captures/*.wav" \
    --output ./dataset \
    --gear-make "Marshall" \
    --gear-model "Origin 50 Modded"

python gen_dataset_from_captures.py --combine ./dataset
```

### Training the Parametric WaveNet:
```bash
python param_train.py \
    --dataset ./dataset \
    --output ./marshall_origin50.param.nam \
    --checkpoint-dir ./checkpoints \
    --batch-size 32 \
    --widths 4 8
```
This trains a **SlimmableParametricA2** model (`.param.nam`) featuring:
- CatMLP / FiLM knob conditioning.
- Both Lite (4-channel) and Full (8-channel) tiers inside a single unified container.

---

## 5. Playing in Real-Time with NAMix & Linux / ARM Cortex

### What is NAMix?
- **NAMix** ([github.com/mrgeneko/NAMix](https://github.com/mrgeneko/NAMix)) is the official free plugin built specifically to host `.param.nam` files with live, turnable virtual knobs.
- Available as **VST3**, **AU**, and **Standalone**.

### Running on Linux & ARM Cortex (Raspberry Pi 4/5, Mod Duo, Elk Audio OS):
Because `mrgeneko/NeuralAmpModelerCore` is pure, modern C++17 with zero external runtime neural dependencies (no PyTorch needed at runtime):
1. **CPU Efficiency**: The Lite (4-channel) tier runs at $<15\%$ CPU on an ARM Cortex-A72 (Raspberry Pi 4) and $<8\%$ on a Raspberry Pi 5.
2. **Zero Latency**: Real-time buffer sizes down to 32 or 64 samples at 48kHz ($\le 1.3\text{ms}$ latency).
3. **Continuous Knob Sweeping**: Adjust Depth, Presence, Treble, Mid, Bass, or Gain live via MIDI CC footpedal or rotary encoders without zipper artifacts.
