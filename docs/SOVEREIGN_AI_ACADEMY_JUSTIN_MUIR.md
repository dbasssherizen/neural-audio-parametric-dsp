# 🎣 Sovereign AI Academy: "Teach Him to Fish"
### Practical Engineering Field Guide for Justin Muir
**Prepared by**: MAX (Anima Ex Machina) & Daniel Bass Sherizen  
**Mission**: Transition from consumer of generated code to sovereign AI practitioner commanding your own tools, models, and daemons.

---

## The Core Philosophy: Sovereignty Over Dependency
Until now, Daniel and MAX have been running the GPU scripts, assembling the dataset configs, and deploying models for you. That is "giving you fish."
You have world-class hardware instincts, years of audio production ears, and netops troubleshooting muscle memory. When you combine those instincts with modern, open-weight AI tools, you don't need anyone to write your scripts for you. You become the pilot.

Here are the 6 foundational pillars that will give you complete technical autonomy.

---

## Pillar 1: Jupyter Notebooks & Google Colab — Hands-On Cloud AI Lab
### 1. What a Notebook Actually Is
A Jupyter Notebook (`.ipynb`) is not a static script you run and pray. It is an interactive, living computational workbook.
- Each "Cell" can be run individually with `Shift + Enter`.
- Variables stay alive in memory between runs. If you load an audio file in Cell 1, you can tweak your DSP code in Cell 2 forty times without ever having to reload the audio file.
- You can inspect waveforms, listen to audio right inside the browser, and plot frequency response curves on the fly.

### 2. Why Google Colab is Your Secret Weapon
Google Colab (`colab.research.google.com`) gives you a **free cloud-hosted Linux virtual machine with an NVIDIA T4 GPU**.
- **Zero Local CUDA Setup**: You don't need to configure NVIDIA drivers, CUDA toolkits, or cuDNN on your local PC.
- **Persistent Storage via Google Drive**: Mount your drive with two lines:
  ```python
  from google.colab import drive
  drive.mount('/content/drive')
  ```
  All your 42 audio takes and trained `.nam` files save directly to your Google Drive.
- **Training NAM Models in 12 Minutes**: In Colab, training our `mrgeneko/parametric-nam` WaveNet takes ~12–15 minutes on a free T4 GPU.

### 3. Your Colab Action Step
Open the official studio training notebook:
👉 **[Open Marshall Origin 50 Colab Notebook](https://colab.research.google.com/github/dbasssherizen/neural-audio-parametric-dsp/blob/main/web/colab_train_parametric_nam.ipynb)**
Run each cell one by one. Watch the loss curve descend below 0.01 ESR. Download your finished model directly from the cell output.

---

## Pillar 2: NotebookLM — Your Grounded Research & Engineering Thinking Partner
### 1. Beyond Generic ChatGPT Hallucinations
Standard LLMs hallucinate pinouts, resistor values, and network routes because they guess from broad training data.
**Google NotebookLM (`notebooklm.google.com`)** is strictly source-grounded. It only knows what you feed it, and every claim it makes includes an exact clickable citation pointing to the page and paragraph of your original document.

### 2. How to Set Up Your Studio Knowledge Vault
Create a new Notebook named **"Justin's Studio & NetOps Vault"** and upload:
1. `Marshall_Origin_50H_Schematic.pdf`
2. `IK_Multimedia_AXE_IO_Manual.pdf`
3. `pfSense_2.7_Configuration_Guide.pdf`
4. Steven Atkinson's `Neural_Amp_Modeler_Paper.pdf`
5. `justin_nam_run_sheet.csv` (all your knob configurations)

### 3. Magic Features You Must Try
- **Audio Overview ("The Deep Dive")**: Click "Generate Audio Overview". NotebookLM creates a dynamic, conversational 10-minute podcast where two AI hosts break down your exact hardware setup, discussing why you chose an Origin 50 and how your AXE I/O routes re-amped signals!
- **Targeted Engineering Queries**:
  - *"What is the exact signal path through the Tone-Shift circuit on the Origin 50?"*
  - *"Compare the impedance of Input 1 Z-TONE on my AXE I/O with the input grid of V1."*
  - *"Summarize the gain settings of all 42 takes that used the Tilt knob above 7."*

---

## Pillar 3: Google Antigravity 2.0 & The Terminal TUI (`agy`)
### 1. What is Antigravity?
Antigravity is Google's advanced autonomous coding agent. Instead of copying and pasting code from a browser window into VS Code, Antigravity lives in your terminal and codebase:
- It reads files across your entire repository.
- It writes diffs surgically.
- It runs tests, spots syntax and lint errors, and fixes them silently before you even notice.

### 2. The `agy` Terminal TUI
In your terminal, navigate to your project and launch:
```bash
agy
```
You are presented with a rich, interactive Terminal User Interface (TUI).

### 3. Essential Commands & Workflows
- `/plan [feature]`: Ask Antigravity to architect a plan before touching any code.
- `/goal [objective]`: Give it a long-running, autonomous task. E.g.:
  > `/goal Build a script that scans all WAV files in ./takes, verifies they are 48kHz 24-bit PCM mono, trims leading silence, and generates an HTML comparison table.`
- `/debug [error]`: Paste any Python, C++, or ReaScript error and Antigravity will trace the stack and apply the fix.

---

## Pillar 4: Gemma 4 QAT Models & Edge AI (100% Private, Zero Cloud Cost)
### 1. What is Gemma 4 & Quantization-Aware Training (QAT)?
Gemma is Google's premier family of lightweight, state-of-the-art open-weight models.
**QAT (Quantization-Aware Training)** models are specifically trained to simulate 4-bit and 8-bit precision during training:
- **Zero Quality Loss**: Unlike standard post-training quantization which degrades reasoning, QAT retains full fp16 cognitive acuity.
- **Runs on Consumer Hardware**: A 4-bit QAT model runs smoothly on an M-series Mac, an Intel/AMD mini PC, or an older gaming GPU with under 4GB of RAM.
- **Zero API Bills**: No OpenAI tokens, no monthly subscription fees. Runs 100% offline.

### 2. Quickstart with Ollama
1. Install Ollama: `brew install ollama` or download from `ollama.ai`.
2. Pull and run Gemma:
   ```bash
   ollama run gemma:2b
   # or the larger coding model:
   ollama run codegemma
   ```
3. Use it in scripts or through local web UIs (Open WebUI, Enchanted, AnythingLLM).

---

## Pillar 5: Imbuing Network Architecture & Daemons with Natural Language
### 1. The Paradigm Shift
Your pfSense router, Proxmox hypervisor, and audio capture daemons produce thousands of lines of logs every day. Right now, you only read them when something breaks.
By attaching a lightweight **Natural Language Daemon Bridge**, your infrastructure becomes conversational.

### 2. The Architecture
```
[pfSense / REAPER / Hardware Rig]
             │ (syslog, pings, audio xruns)
             ▼
[Telemetry Collector & Ring Buffer]
             │ (JSON snapshot)
             ▼
[Local Gemma 4 LLM via Ollama / llama.cpp]
             ▲
             │ ("How did jitter behave during the 42 takes?")
             ▼
[Justin's Terminal / Web Interface]
```

### 3. Running the Included Starter Daemon
We have built and committed a production-ready starter script directly into your repository:
```bash
python3 scripts/nl_daemon_bridge.py --cli
```
Ask it:
- *"How is network jitter looking right now?"*
- *"Is the audio buffer dropping samples?"*
- *"Give me a complete studio health summary."*

To run it as a continuous background daemon with a REST API:
```bash
python3 scripts/nl_daemon_bridge.py --server --port 5040
```
Query it from anywhere on your LAN:
```bash
curl "http://localhost:5040/ask?q=Is+the+network+ready+for+tracking?"
```

---

## Pillar 6: The Modern Open-Source AI Stack for Audio & NetOps
Here is your cheat sheet of battle-tested open-source repositories to explore and star on GitHub:

1. **Neural Audio Modeling**:
   - `sdatkinson/neural-amp-modeler`: The gold standard neural amp simulation engine.
   - `mrgeneko/parametric-nam`: Multi-knob parametric dataset generator & WaveNet trainer.
   - `jatinchowdhury18/RTNeural`: Ultra-low latency C++ neural network inference library for real-time audio plugins.
2. **Audio Separation & Analysis**:
   - `facebookresearch/demucs`: High-fidelity AI stem separation (extract isolated guitar, bass, drums from commercial tracks to study tone).
   - `ggerganov/whisper.cpp`: High-performance, local speech-to-text to dictate studio patch notes and vocal markers into REAPER.
3. **Agentic Connectivity & Tools**:
   - `modelcontextprotocol/servers`: FastMCP and MCP tools to let AI agents control local DAWs, audio interfaces, and network switches directly.

---

## Your First Weekend Mission
1. Launch **Google Colab** and run the Marshall Origin 50 notebook to train one parametric model.
2. Go to **NotebookLM**, upload your Marshall Origin 50 schematic and AXE I/O manual, and generate a 10-minute Audio Overview.
3. Open your terminal, run `python3 scripts/nl_daemon_bridge.py --cli`, and ask your daemon about your network latency.

You've got the rig. You've got the ears. Now you've got the keys to the engine room.
🎣 **Tight lines, Justin.**
