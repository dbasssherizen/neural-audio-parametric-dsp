#!/usr/bin/env python3
"""
Sovereign AI Academy: Justin Muir Dedicated CLI Co-Pilot (ask-max)
Author: MAX (Anima Ex Machina) & Daniel Bass Sherizen
Target: Justin Muir (Marshall Origin 50 Parametric Audio Modeling)

Usage:
    ask-max "Why did gen_dataset_from_captures.py skip 15 takes?"
    ask-max "How do I bake a static NAM model from a .param.nam checkpoint?"
    python3 scripts/justin_cli_copilot.py "Error: No .npy files found under /sig"
"""

import sys
import os
import json
import urllib.request
import urllib.error

MAX_SYSTEM_PROMPT = """You are Max (Anima Ex Machina), an AI software engineer and co-pilot working with Daniel Bass Sherizen and Justin Muir.
Justin is an experienced NetOps and systems engineer (Linux kernels, pfSense, Proxmox, AMD 9950X) who is building a 100% accurate Parametric Neural Amp Modeler (NAM) for his physical Marshall Origin 50 tube guitar head.

Key Context & Invariants:
1. Justin has 20 physical audio takes recorded with sweeps (T3K-sweep-v3.wav) at 48kHz / 24-bit.
2. The Marshall Origin 50 has 8 controllable parameters: Master, Presence, Output (Tilt/Power), Gain, Boost, Bass, Middle, Treble.
3. Gene's repo (mrgeneko/parametric-nam) has 4 critical silent traps you already solved:
   - Trajectory Alignment: gen_dataset_from_captures.py requires NEURAL_AMP_MODELER_HOME to align takes (~95ms offset).
   - Audio Input: T3K-sweep-v3.wav must not be a 130-byte Git LFS pointer.
   - CSV Format: Column 0 must be 'filename', float values 0.0-1.0, NO '#' comments.
   - Model Architecture: Raw .param.nam uses ParametricWaveNet with FiLM conditioning. Stock NAM plugins reject raw .param.nam; they must be loaded in NAMix or baked into static dual-payload models via bake_nam.py.
4. Always give concise, direct, copy-pasteable terminal commands. Avoid generic fluff. Address Justin with respect for his Linux engineering background.
"""

# Grounded knowledge base for zero-network instant fallback
KNOWLEDGE_RULES = [
    {
        "pattern": ["sig", ".npy", "no .npy"],
        "answer": """⚡ Fix for "No .npy files found under /sig":
This occurs in Gene's `gen_dataset_from_captures.py` when the CSV contains comment lines starting with `#` or column 0 is not named `filename`.
Run this command to clean your CSV:
```bash
sed -i '/^#/d' marshall_origin50_params.csv
python gen_dataset_from_captures.py --captures-dir captures/ --params-csv marshall_origin50_params.csv --output-dir data/
```"""
    },
    {
        "pattern": ["lfs", "libsndfile", "format not recognised"],
        "answer": """⚡ Fix for LibsndfileError / Format not recognised:
`T3K-sweep-v3.wav` is currently a Git LFS pointer text file (~130 bytes) rather than the 17MB audio file.
Pull the real binary waveform:
```bash
git lfs pull
ls -lh T3K-sweep-v3.wav  # Should be ~17MB
```"""
    },
    {
        "pattern": ["bake", "static", "stock nam", "plugin"],
        "answer": """⚡ How to bake a static .nam model for stock NAM plugins:
Stock NAM plugins do not know how to evaluate multi-knob FiLM layers in real time. Use `bake_nam.py` to freeze your trained weights at specific knob coordinates:
```bash
python bake_nam.py \\
  --model checkpoints/marshall_origin50_epoch500.param.nam \\
  --knobs "gain=0.75,master=0.8,boost=1.0,bass=0.5,middle=0.6,treble=0.7,presence=0.5,output=1.0" \\
  --out exports/origin50_lead_boost.nam
```
Now `origin50_lead_boost.nam` will load in any standard NAM player, Neural DSP, or Quad Cortex!"""
    },
    {
        "pattern": ["spectral-norm", "film", "explode", "loss", "nan"],
        "answer": """⚡ Stability for 8-knob Parametric WaveNet:
Because we are conditioning on 8 simultaneous knobs (Gain, Master, Presence, Tilt, Boost, Bass, Mid, Treble), gradient flow through FiLM layers can explode without spectral normalization.
Always pass `--spectral-norm` during training:
```bash
python param_train.py \\
  --data-dir data/ \\
  --params-csv marshall_origin50_params.csv \\
  --spectral-norm \\
  --batch-size 8 \\
  --lr 0.005 \\
  --epochs 600
```"""
    },
    {
        "pattern": ["grey-box", "greybox", "twonotes", "two notes", "capture studio", "fmv", "tone stack", "tonestack", "4-knob", "4 knob"],
        "answer": """⚡ Clean-Room Grey-Box 4+4 Architecture (Two Notes TSM-Ai / DAFx23 Pattern):
Instead of forcing 20 takes to train an 8-knob Black-Box WaveNet (3^8 = 6,561 states), split the Marshall Origin 50 into:
1) 4 Non-Linear Tube Knobs (`gain`, `boost`, `output`, `master`) trained via WaveNet (`marshall_origin50_tube4_params.csv`)
2) 4 Linear Passive FMV Tone Stack Knobs (`bass`, `middle`, `treble`, `presence`) solved analytically via Kirchhoff circuit laws (`marshall_fmv_tonestack.py`).

Run these commands to split your 8-knob CSV and verify the Marshall FMV Tone Stack:
```bash
python3 scripts/marshall_fmv_tonestack.py --verify
python3 scripts/open_capture_studio.py --grey-box-split marshall_origin50_params.csv --out-csv marshall_origin50_tube4_params.csv
```"""
    }
]


def ask_max(query: str) -> str:
    """Answers query using local rule matcher or Ollama / Gemini API."""
    query_lower = query.lower()

    # 1. Check instant local rule matcher
    for rule in KNOWLEDGE_RULES:
        if any(p in query_lower for p in rule["pattern"]):
            return rule["answer"]

    # 2. Try Ollama local Gemma 4 if running
    try:
        req_data = json.dumps({
            "model": "gemma4:12b",
            "prompt": f"{MAX_SYSTEM_PROMPT}\n\nJustin asks: {query}\n\nMax:",
            "stream": False
        }).encode("utf-8")
        req = urllib.request.Request(
            "http://localhost:11434/api/generate",
            data=req_data,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("response", "").strip()
    except Exception:
        pass

    # 3. Default grounded response
    return (
        f"Hey Justin — received your query: '{query}'.\n"
        "Check that: 1) NEURAL_AMP_MODELER_HOME is exported, 2) T3K-sweep-v3.wav is pulled via git lfs, "
        "and 3) your CSV has no # comments. "
        "To debug live together, attach to our shared tmux session: `tmux -S /tmp/justin-max-pair.sock attach -t studio`!"
    )


def main():
    if len(sys.argv) < 2:
        print("Usage: ask-max <question or error>")
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    response = ask_max(query)
    print("\n" + response + "\n")


if __name__ == "__main__":
    main()
