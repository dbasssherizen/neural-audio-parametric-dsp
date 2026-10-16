# 🎸 Justin Muir — Universal Open-Source Parametric NAM, AXE I/O & Captor X Studio Kit

**Prepared for**: Justin Muir (`nightmareglove@gmail.com`)  
**From**: Daniel Bass-Sherizen & Max (Anima Ex Machina)  
**Target Ecosystem**: **100% Open-Source / Vendor-Neutral** (Zero Positive Grid / Closed-Ecosystem Lock-In)

---

## ⚡ Executive Summary: Built for Your Actual Digital & Hybrid Rig

When Daniel first built the **45-Titan Ear-First Guitar & Baritone Studio**, his personal copy targeted his Positive Grid Spark amp. Because you're an open-source/Linux purist running a serious hybrid studio and digital modeling pipeline, we stripped out **every single line of Positive Grid Spark code** (no BLE `0xFFC0` SysEx, no closed `.preset` files, no proprietary BIAS/Spark model names) and rebuilt the entire suite natively around **your exact digital + hardware chain**:

1. **Digital Audio & Impedance Modeling**: **IK Multimedia AXE I/O** (`Z-TONE` variable-impedance input $\rightarrow$ ASIO `Line Out 5 AMP OUT` $\rightarrow$ **Little Labs Redeye 3D Phantom** $\rightarrow$ **Marshall Origin 50** $\rightarrow$ **Two Notes Torpedo Captor X** / **Suhr Reactive Load** $\rightarrow$ Rear Line In 1/2).
2. **Open-Source Neural & Grey-Box Amp Modeling**:
   - **Neural Amp Modeler (NAM)** (`sdatkinson/neural-amp-modeler` A2 standard)
   - **NAMix VST3/CLAP** & **mrgeneko/parametric-nam** (continuous multi-knob FiLM/HyperNetwork `.param.nam` models)
   - **4+4 Grey-Box Marshall Origin 50 Hybrid (`open_capture_studio.py --grey-box-split` + `marshall_fmv_tonestack.py`)**: Shrinks an 8-knob amp capture from $5^8 = 390,625$ takes down to **20 nonlinear preamp/power-amp takes** + an exact **White-Box Bilinear-Transformed Passive FMV Tone Stack (`Bass, Mid, Treble, Presence`)**.
   - **Tone3000 20-Static-NAM Combiner (`combine_static_nams.py`)**: Lets you batch-train your 20 sweeps on Tone3000's free cloud GPUs and mathematically fuse those 20 static `.nam` files into a single continuous 8-knob parametric rig.
3. **DAW & IR Loader Integration**:
   - Native **Cockos REAPER** WebMIDI (`CC 20–27`) & ReaScript automation
   - **Two Notes Torpedo Captor X** MIDI CC control + **Ignite Amps NadIR** / **Lancaster Audio Pulse** / **ReaVerb** zero-latency IR routing
4. **RP2040 Hardware Potentiometer & Motorized CSV Servo Firmware (`rp2040_pot_controller.py`)**:
   - **Mode A (Live Manual Control)**: Reads 8 physical 10k$\Omega$ linear pots (`Gain, Boost, Tilt, Bass, Mid, Treble, Master, Presence`) and streams `MIDI CC 20–27` over USB-MIDI straight into **REAPER / NAMix / Captor X**.
   - **Mode B (Automated Motorized Potentiometer CSV Re-Amping)**: Directly implements your goal (*"End goal is motorized pots to adjust them based on csv input"*). Send any row from `marshall_origin50_params.csv` over USB Serial (or straight from the Studio WebSerial button), and the RP2040 runs a closed-loop PID H-Bridge servo (`DRV8833` / `L293D` + ALPS motorized faders/pots) to **physically turn your Marshall Origin 50 knobs to the exact CSV coordinates** before REAPER fires each sweep!

---

## 🏛️ 1. What's Inside the Retargeted Studio (`justin_muir_nam_studio.html`)

Open `justin_muir_nam_studio.html` in any browser (or at `/guitar-studio.html` on your NetOps hub):

- **49 Iconic Rigs (45 Pantheon Titans + 4 Custom Justin Signature Additions)**:
  - **Custom Justin Additions**:
    1. **Marshall Origin 50 — 4+4 Grey-Box Master Rig** (Your exact 8-knob circuit: `Gain, Pull-Boost, Tilt, Bass, Mid, Treble, Master, Presence` mapped to `CC 20–27`)
    2. **Josh Homme / QOTSA — "Architect of Desert Rock" Mid-Pushed Fuzz/Tube** (Parametric mid-Q honk + saggy power-tube saturation inspired by the Rick Beato QOTSA breakdown)
    3. **Korn — 7-String / Baritone Drop-A Sub-Lock (`26.5"–27"` Scale)** (Tight sub-bass high-pass before clipping + scooped 500 Hz + aggressive 2.5 kHz clank)
    4. **Trent Reznor & Atticus Ross — Fincher Industrial Swarm / Broken DAC** (Asymmetric wavefolder + gated industrial fuzz + dark shimmer)
  - **Plus all 45 Pantheon Guitar & Baritone Titans**: Prince, Jimi Hendrix, David Gilmour, Stevie Ray Vaughan, Eddie Van Halen, Tony Iommi, Jimmy Page, Kurt Cobain, Jerry Cantrell, Dimebag Darrell, Adam Jones, Billy Corgan, Kevin Shields, Robin Guthrie, Johnny Marr, John Frusciante, Nile Rodgers, Thurston Moore, J Mascis, Robert Smith, Jack White, St. Vincent, Allan Holdsworth, Plini, Tosin Abasi, Loathe (`27"–30" Baritone`), Sleep Token, Deftones (Stephen Carpenter), Meshuggah, Gojira, Mk.gee, Boards of Canada (Tape Drift), Khruangbin, and more.
- **5-Mode Interactive Views**:
  1. **🎸 All 49 Rigs**: Filter by Era, Baritone/7-String Drop Tunings, or Acoustic vs. Electric.
  2. **🎧 Ear-First Blind Quiz**: Hear the WebAudio DSP synthesis and guess the guitarist & open-source NAM topology before revealing the card.
  3. **🔬 Signal Chain Lab (8-Knob Parametric + Grey-Box FMV)**: Real-time interactive knobs (`Gain, Boost, Tilt, Bass, Mid, Treble, Master, Presence`) that simultaneously:
     - Drive the browser's live **WebAudio 6-stage DSP + FMV Tone Stack synthesizer**,
     - Transmit real-time **WebMIDI `CC 20–27`** into **REAPER / NAMix / Captor X**, and
     - Stream target coordinates over **WebSerial** to your **RP2040 Motorized Potentiometers**!
  4. **🎚️ Side-by-Side A/B Rig Comparator**: Compare any two rigs' Gain, Compression, Brightness, Wetness, and Sub-Weight radar profiles.
  5. **🧬 Open-Source Parametric NAM + Motorized CSV Architecture**: Interactive guide to the 4+4 Grey-Box split, Tone3000 20-Static-NAM Combiner, and RP2040 Motorized Servo wiring.

---

## 🤖 2. RP2040 Bidirectional Firmware (`rp2040_pot_controller.py`)

Your upgraded CircuitPython firmware supports **both** directions over a single USB cable:

| Pin / Bus | Component | Function |
| :--- | :--- | :--- |
| `GP26` (`A0`) – `GP28` (`A2`) + `CD74HC4067` Mux | 8x 10k$\Omega$ Linear Pots (or ALPS Motorized Wipers) | Reads real-time knob positions (`0.00–1.00`) for `Gain, Boost, Tilt, Bass, Mid, Treble, Master, Presence` |
| `USB-MIDI Ch 1` | `CC 20` – `CC 27` | Streams zero-jitter 14-bit/7-bit MIDI CC into **REAPER**, **NAMix VST3**, or **Two Notes Captor X** |
| `USB-CDC Serial` (`115200 8N1`) | CSV Command Parser | Accepts `CSV:TAKE_07,0.85,1.0,0.65,0.50,0.75,0.70,0.60,0.55` from Python or WebSerial |
| `PCA9685` 16-Ch PWM (`I2C GP4/GP5`) | 8x `DRV8833` / `L293D` H-Bridges | Drives motorized pots/faders with a proportional-integral-derivative (PID) deadband loop (`±0.008` tolerance) and replies `ACK:TAKE_07:LOCKED` when all 8 knobs reach position! |

---

## 🚀 3. Quick-Start Workflow with Your Existing Repo

1. **Audition & Tweak in Browser (`justin_muir_nam_studio.html`)**:
   - Click **🎹 Connect WebMIDI (REAPER / NAMix / Captor X)** in the top bar to link browser knob movements directly to `CC 20–27` in REAPER.
   - Or click **🤖 Connect Motorized Pots (WebSerial)** to push any rig's 8 knob settings (`CSV:...`) out to your microcontroller.
2. **Generate Your 20-Take Grey-Box Schedule**:
   ```bash
   python scripts/open_capture_studio.py --preset marshall_origin50 --grey-box-split --takes 20 --output-dir ./captures/origin50_greybox
   ```
3. **Train 20 Static `.nam` Models on Tone3000 & Fuse Them**:
   ```bash
   python scripts/combine_static_nams.py --manifest ./captures/origin50_greybox/capture_manifest.json --nam-dir ./trained_nams --export-bundle ./models/origin50_parametric_bundle.json
   ```
4. **Export Any Rig from the Studio**:
   - Every rig card has an **📥 Export `.param.nam` JSON + Motorized CSV Row** button that downloads a clean, vendor-neutral JSON/CSV patch ready for REAPER, NAMix, and your RP2040 servo controller.
