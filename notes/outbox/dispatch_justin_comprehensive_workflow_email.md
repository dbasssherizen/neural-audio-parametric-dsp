# Sovereign AI Academy Dispatch — Comprehensive Workflow & Architecture Update

**Recipient**: Justin Muir (nightmareglove@gmail.com / +1 630-418-9227)  
**From**: Daniel Bass Sherizen (daniel.bass.sherizen@gmail.com) & MAX (Anima Ex Machina)  
**Subject**: Marshall Origin 50 Parametric NAM: Fixed Colab Link, --mapping-csv Guide & Hub Update  
**Date**: 2026-10-08T19:19:00-05:00  

---

### Email Body

Hey Justin,

Dan and Max here. We wanted to send over a complete, permanent reference guide so you have all the exact links, commands, and architecture in one place on your desktop/laptop:

#### 1. Why the Portal / Colab Link Seemed Dated or 404'd
- The GitHub repo was previously set to Private, which caused Google Colab to reject the 1-click launcher with a 404.
- In addition, the root URL on Firebase was pointing to an older redirect stub.
- **Both are now completely fixed**:
  - The repo is Public: https://github.com/dbasssherizen/neural-audio-parametric-dsp
  - The live portal is updated and live across all three domains:
    👉 **https://justin-netops-hub.web.app** (also mirrored at `justin-muir-netops.web.app` and `justin-netops.web.app`)
  - The 1-click Colab GPU launcher opens directly with zero friction:
    👉 **[Open Colab GPU Trainer](https://colab.research.google.com/github/dbasssherizen/neural-audio-parametric-dsp/blob/main/notebooks/colab_train_parametric_nam.ipynb)**

---

#### 2. The Filename Tokens vs. CSV Mystery (Gene's Source Code)
You were wondering if you had to rename every WAV file into comma-separated tokens like `g2.0,t5,5`.

We inspected Gene’s (`mrgeneko`) actual repository code (`gen_dataset_from_captures.py` and `capture_common.py`), and found the native escape hatch:
**Gene built in a `--mapping-csv` flag that completely bypasses filename token parsing!**

```python
# From mrgeneko/parametric-nam/capture_common.py
def load_mapping_csv(path: Path) -> dict:
    """filename,<Knob1>,<Knob2>,... escape hatch -- bypasses regex/token parsing entirely."""
```

This means:
- You **do NOT need to rename your WAV files** to `g2.0,t5,5`.
- Your files can stay cleanly named `amp_run_001.wav`, `amp_run_002.wav`, etc.
- As long as you pass `--mapping-csv clean_mapping.csv`, Gene's script reads the knob columns directly from the CSV!

---

#### 3. How to Run Locally on Your Ubuntu Server (Zero Code Adjustments)
If you are running on your local Ubuntu box, here is the exact 3-step command chain without modifying any of Gene's Python files:

```bash
# 1. Activate your virtualenv
source .venv/bin/activate

# 2. Build and combine the dataset using your clean mapping CSV
python gen_dataset_from_captures.py \
    --captures "./captures/*.wav" \
    --input "./reference_sweeps/input.wav" \
    --mapping-csv "./captures/clean_mapping.csv" \
    --output ./dataset \
    --gear-make "Marshall" \
    --gear-model "Origin 50 Modded"

python gen_dataset_from_captures.py --combine ./dataset

# 3. Train the SlimmableParametricA2 WaveNet
python param_train.py \
    --dataset ./dataset \
    --output ./marshall_origin50.param.nam \
    --checkpoint-dir ./checkpoints \
    --batch-size 32 \
    --widths 4 8
```

*Note on Latency Alignment*: Make sure `--input` points to the pristine 190.00s dry reference sweep (`input.wav` from the hub), so NAM's blip-detection aligns phase perfectly with your physical AXE I/O + Suhr Reactive Load latency.

---

#### 4. Automated Colab Pipeline
If your local Ubuntu box is occupied or if you want free cloud GPU acceleration:
1. Open the [Colab Notebook](https://colab.research.google.com/github/dbasssherizen/neural-audio-parametric-dsp/blob/main/notebooks/colab_train_parametric_nam.ipynb).
2. Set Runtime to **T4 GPU** (free).
3. Upload your zip file when prompted in Cell 6.
4. Cell 8 automatically strips any non-knob columns (`val`, `split`), normalizes dial positions (0.0–1.0), downloads `input.wav` from our CDN, and trains the model in ~35–45 minutes.

Once your Ubuntu training pass finishes in a few hours, let's compare notes! If you'd like to hop on a quick Google Meet to review the loss curves or verify the `.param.nam` in NAMix together, just say the word.

Best,  
Dan & Max
