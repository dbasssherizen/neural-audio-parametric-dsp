# Marshall Origin 50 — Sovereign Studio Session Wiki
**Engineer**: Justin Muir (`+1 630-418-9227` / `nightmareglove@gmail.com`)  
**Methodology**: Karpathy Minimal Knowledge Wiki (Frictionless Single-Folder Markdown)  
**Hardware Rig**: Marshall Origin 50H (Head) | Marshall 4x12 Cab (Celestion G12M Greenbacks)  
**Interface**: Universal Audio Apollo x8 | Radial ProRMP Re-Amp Box | Mogami 2524 Cabling  

---

## 1. Why a Minimal Markdown Wiki? (LearnLM Architecture)
In modern audio engineering and sovereign AI modeling, proprietary formats (`.docx`, messy spreadsheets) create high cognitive friction. 
An AI pair-coder (like Gemma 4 or Antigravity) cannot grep a `.docx` natively. 
**Markdown (`.md`) is the agent's native memory layer**:
- Clean `##` headers define semantic sections.
- Markdown tables render cleanly in browsers and parse into JSON/dataclasses with zero hallucination.
- Files live in Git version control with atomic commit diffs.

---

## 2. Tube Complement & Plate Voltage Calibration
| Stage / Tube Position | Valve Type | Brand / Batch | Measured Bias (mA) | Plate Voltage ($V_p$) | Sonic Character |
|---|---|---|---|---|---|
| **V1 (Input Gain Stage)** | 12AX7 / ECC83 | Mullard Reissue | Cathode Biased | 245V | Warm pick attack, low microphonics |
| **V2 (Tone Stack Buffer)** | 12AX7 / ECC83 | JJ Electronics | Cathode Biased | 260V | Extended high-frequency clarity |
| **V3 (Phase Inverter)** | 12AX7 / ECC83 | Sovtek 12AX7LPS | Cathode Biased | 275V | Balanced output drive to power tubes |
| **V4 & V5 (Power Section)** | EL34 (Matched Pair)| Svetlana "Winged C" | 38.5 mA (idle) | 465V | Rich power amp sag, musical compression |

> **Tech Note**: Measured using bias probe at 120V AC wall line voltage (Furman power conditioning).

---

## 3. Microphone Placements & Phase Alignment
| Mic # | Model | Capsule Angle | Distance to Grille | Cone Placement | Preamp Channel |
|---|---|---|---|---|---|
| **Mic A (Core Punch)** | Shure SM57 | $0^\circ$ (On-Axis) | 0.75" (19mm) | Cap-edge seam (Speaker Top-Left) | Apollo Ch 1 (Unison API 512c) |
| **Mic B (Warmth & Body)**| Royer R-121 | $0^\circ$ (On-Axis) | 2.50" (63mm) | Halfway between center cap and cone edge | Apollo Ch 2 (Unison Neve 1073) |
| **Mic C (Room Depth)** | AKG C414 XLS | Blumlein $45^\circ$ | 4.0 ft (1.2m) | Centered at ear-height in tracking room | Apollo Ch 3 & 4 (Stereo Pair) |

> **Phase Alignment Protocol**: Phase inverted on Royer R-121 during soundcheck. Mics nudged until pink noise null test drops below **-42 dBFS**, then flipped back into phase.

---

## 4. Parametric Potentiometer Run Sheet (Takes 00 – 07)
| Take ID | Gain (0–10) | Bass (0–10) | Middle (0–10) | Treble (0–10) | Master (0–10) | Output File Name | Target Tone Goal |
|---|---|---|---|---|---|---|---|
| `Take 00` | 5.0 | 5.0 | 5.0 | 5.0 | 7.0 | `take_00_anchor_G5.0_B5.0_M5.0_T5.0_M7.0.wav` | Flat baseline anchor |
| `Take 01` | 6.5 | 5.0 | 8.5 | 7.0 | 3.5 | `take_01_G6.5_B5.0_M8.5_T7.0_M3.5.wav` | Modern high-mid bite |
| `Take 02` | 5.5 | 3.5 | 6.5 | 9.0 | 6.0 | `take_02_G5.5_B3.5_M6.5_T9.0_M6.0.wav` | Plexi chime & presence |
| `Take 03` | 3.0 | 9.0 | 7.5 | 4.0 | 3.5 | `take_03_G3.0_B9.0_M7.5_T4.0_M3.5.wav` | Thick fuzz-pedal pedal platform |
| `Take 04` | 5.5 | 7.0 | 6.5 | 1.0 | 6.0 | `take_04_G5.5_B7.0_M6.5_T1.0_M6.0.wav` | Dark jazz-rock overdrive |
| `Take 05` | 8.5 | 1.5 | 6.5 | 1.5 | 4.0 | `take_05_G8.5_B1.5_M6.5_T1.5_M4.0.wav` | Tight djent / modern metal cut |
| `Take 06` | 1.5 | 2.5 | 8.0 | 6.0 | 2.0 | `take_06_G1.5_B2.5_M8.0_T6.0_M2.0.wav` | Clean funk percussive snap |
| `Take 07` | 2.5 | 8.5 | 5.5 | 8.5 | 4.5 | `take_07_G2.5_B8.5_M5.5_T8.5_M4.5.wav` | Dynamic blues edge-of-breakup |

---

## 5. WaveNet Modeling Loss & Quality Checklist
- [x] Sweeps recorded at 48kHz / 24-bit PCM.
- [x] Input trunc alignment verified with cross-correlation spike.
- [x] Validation ESR (Error-to-Signal Ratio) $< 0.035$ across 100 epochs.
- [x] Tested in REAPER with Neural Amp Modeler VST3 at 64-sample buffer. Zero crackles or phase anomalies.
