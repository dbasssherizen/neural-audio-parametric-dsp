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

## Pillar 4: The Gemma 4 Architecture: 12B Unified, 31B Flagship & QAT Checkpoints
### 1. Why Gemma 4 12B is CRITICAL for Audio & Studio Engineering
Released in mid-2026, **Gemma 4 12B Unified** is one of the most critical open-weights models ever released for audio engineers.
- **Native Audio Input Processing**: Unlike previous models that required a separate speech-to-text pipeline (like Whisper), **12B natively ingests audio waveforms and acoustic tokens directly**. It can "hear" audio transients, evaluate distortion harmonics, and analyze frequency spectra alongside text and code!
- **Encoder-Free Multimodal**: A unified transformer architecture processing Audio, Vision (circuit schematics, oscilloscope screenshots, front panel knobs), and Text simultaneously.
- **The Workstation Sweet Spot**: Quantized with 4-bit QAT (`Q4_K_M`), Gemma 4 12B runs in **~7.2 GB of VRAM**. It fits comfortably on standard consumer GPUs (NVIDIA RTX 3060/4060 with 8GB–12GB) and 16GB Apple Silicon Macs.

### 2. Why Gemma 4 31B is the Flagship Sovereign Architect
Google's flagship dense open model is **Gemma 4 31B** (30.7B parameters):
- **Configurable Thinking Modes**: Supports extended chain-of-thought test-time compute, allowing the model to deliberate deeply on complex circuit routing, multi-stage gain structures, and kernel-level audio buffer tuning.
- **256K Context Window**: Large enough to ingest entire software repositories, multiple hardware service manuals, and days of raw pfSense firewall logs in a single prompt.
- **VRAM Footprint**: With 4-bit QAT (`Q4_K_M`), 31B runs in **~18.5 GB VRAM**, accessible on 24GB GPUs (RTX 3090/4090) or unified-memory Mac Studios (24GB–32GB).

### 3. Complete Gemma 4 & Specialized Checkpoint Catalog

| Model Tier | Ollama Tag | Params | Quantization (QAT) | Min VRAM | Modalities | Primary Studio / NetOps Use Case |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Gemma 4 12B Unified** 🏆 *(Critical Audio)* | `gemma4:12b` | 12.2B | 4-bit QAT (`Q4_K_M`) | **~7.2 GB** | **Audio + Vision + Code** | **Direct waveform & audio transient evaluation**, Marshall Origin 50 tone analysis, circuit schematics, NetOps reasoning |
| **Gemma 4 31B Flagship** 👑 *(Frontier Dense)* | `gemma4:31b` | 30.7B | 4-bit QAT (`Q4_K_M`) | **~18.5 GB** | **Vision + Code (256K Context)** | **Frontier thinking modes**, full multi-file autonomous repo refactoring, complete pfSense syslog forensic synthesis |
| **Gemma 4 26B A4B MoE** ⚡ *(Sparse Speed)* | `gemma4:26b-a4b` | 26B (4B act) | 4-bit QAT (`Q4_K_M`) | **~15.0 GB** | **Text + Code (128K Context)** | High-speed routing, concurrent daemon processing at 4B latency with 26B reasoning depth |
| **Gemma 4 E4B Studio Edge** | `gemma4:e4b` | 8.0B | 4-bit QAT (`Q4_K_M`) | **~4.8 GB** | **Audio + Vision + Text** | Lightweight edge audio/video monitoring on Proxmox VMs or mini studio PCs |
| **Gemma 4 E2B Mobile Edge** | `gemma4:e2b` | 5.1B (2.3B act)| 4-bit QAT (`Q4_K_M`) | **~1.6 GB** | **Audio + Text** | Real-time audio buffer underrun watcher, Raspberry Pi / pfSense gateway sidecar |
| **CodeGemma Engineer** | `codegemma:7b` | 8.5B | 4-bit QAT (`Q4_K_M`) | **~5.2 GB** | **Code + Text** | Full autonomous script synthesis: Python daemons, automated sweep orchestrators, REAPER ReaScripts |
| **PaliGemma Visual Scope** | `paligemma:3b` | 2.9B | 4-bit / FP16 | **~3.4 GB** | **Vision + Text** | Dedicated hardware schematic PDF inspector, oscilloscope screenshots, and physical amp faceplate reading |

### 4. Running Any Gemma Checkpoint Locally
1. Install Ollama:
   ```bash
   curl -fsSL https://ollama.ai/install.sh | sh
   ```
2. Pull and run the model matching your hardware:
   ```bash
   # Studio Workstation (Premier Choice - Native Audio Input):
   ollama run gemma4:12b

   # Heavyweight Dense Architect (256K Context + Thinking Modes):
   ollama run gemma4:31b

   # Sparse MoE (26B Knowledge at 4B Speed):
   ollama run gemma4:26b-a4b

   # Edge Audio & Telemetry Daemon (<2GB VRAM):
   ollama run gemma4:e2b

   # Autonomous REAPER ReaScript & Python Coder:
   ollama run codegemma:7b

   # Multimodal Hardware & Scope Vision:
   ollama run paligemma:3b
   ```

---

## Pillar 5: Imbuing Network Architecture & Daemons with Natural Language
### 1. The Paradigm Shift
Your pfSense router, Proxmox hypervisor, and audio capture daemons produce thousands of lines of logs every day. Right now, you only read them when something breaks.
By attaching a lightweight **Natural Language Daemon Bridge**, your infrastructure becomes conversational.

### 2. The Multi-Model Daemon Architecture
```
[pfSense / REAPER / AXE I/O Rig]
             │ (syslog, pings, audio waveforms & xruns)
             ▼
[Telemetry Collector & Ring Buffer]
             │ (JSON snapshot + audio buffer)
             ▼
[Local Gemma 4: 12B Unified (Audio) / 31B (256K Thinking) / 26B (MoE)]
             ▲
             │ ("How did jitter & audio transients behave during take 24?")
             ▼
[Justin's Terminal / Web Interface / curl]
```

### 3. Running the Included Multi-Model Starter Daemon
The included script [`scripts/nl_daemon_bridge.py`](scripts/nl_daemon_bridge.py) supports dynamic model switching right from the CLI or REST API:

```bash
# 1. Interactive Terminal REPL with 12B Unified (Native Audio Enabled):
python3 scripts/nl_daemon_bridge.py --cli --model gemma4:12b

# 2. Or Run with 31B Dense Flagship for deep architectural thinking:
python3 scripts/nl_daemon_bridge.py --cli --model gemma4:31b

# 3. Or Run with 26B A4B MoE for high-speed concurrent processing:
python3 scripts/nl_daemon_bridge.py --cli --model gemma4:26b-a4b

# 4. In the REPL, type :models to see the full catalog or :use <model> to switch on the fly!
```

To run it as a continuous background daemon with a REST API:
```bash
python3 scripts/nl_daemon_bridge.py --server --port 5040 --model gemma4:12b
```
Endpoints:
- Query: `curl "http://localhost:5040/ask?q=Is+network+jitter+clean?"`
- Query with specific model: `curl "http://localhost:5040/ask?q=Analyze+transients&model=gemma4:12b"`
- Model Catalog: `curl "http://localhost:5040/models"`
- System Status: `curl "http://localhost:5040/status"`

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
3. Pull **Gemma 4 12B Unified** locally (`ollama run gemma4:12b`) to test native audio and technical reasoning.
4. Launch `python3 scripts/nl_daemon_bridge.py --cli --model gemma4:12b` and chat with your live network and audio telemetry.

You've got the rig. You've got the ears. Now you've got the keys to the engine room.
🎣 **Tight lines, Justin.**


---

## 🔒 Advanced Track (Unlock When Ready): Structured Schemas (JSON, YAML, BAML)
*Note: Do not worry about this section on Day 1. Focus on your first Colab run and NotebookLM Audio Overview first! When you find yourself wanting to automate your session logs, feed data between scripts, or configure Proxmox daemons, come back to this section.*

### 1. JSON (The Universal Machine Wire)
* **What It Is**: The universal format machines use to exchange live state. In your studio, every `.nam` model contains a `config.json` listing knob names, sample rates, and training loss.
* **Why You Care**: When our Python daemon or web app reports `xruns: 0`, it speaks JSON. Any script in Python, C++, or JavaScript can parse it with one line.
* **Inspect It**: Open `web/data.json` to see how your 42 takes are stored.

### 2. YAML (Declarative NetOps Configuration)
* **What It Is**: Human-readable data formatting that relies on clean indentation instead of curly braces.
* **Why You Care**: All modern NetOps tools (Proxmox cloud-init, Docker Compose, pfSense automation, GitHub Actions) use YAML. It reads like a clean studio patch sheet.

### 3. BAML (Type-Safe AI Prompt Schemas)
* **What It Is**: *Boundary's Almost Markdown Language*.
* **The Superpower**: Standard LLMs give messy paragraph responses when you just want numbers. BAML forces local models (like Gemma 4 12B) to return **100% typed, valid data** with zero formatting hallucinations.
* **Runnable Demonstration Script**:
  ```bash
  python3 scripts/demo_structured_schemas.py
  ```
  Run this anytime to see side-by-side examples of JSON, YAML, and BAML generated from your Marshall Origin 50 knob data.
