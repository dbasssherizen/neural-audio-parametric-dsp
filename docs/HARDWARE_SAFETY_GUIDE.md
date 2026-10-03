# 🔌 Justin Muir • Parametric Tube Amp Re-Amping Safety & Hardware Guide
### Dedicated Ground-Truth Audio Engineering Standards for Neural Amp Modeler

This guide establishes the mandatory physical setup, electrical protection protocols, gain staging calibration, and troubleshooting procedures for re-amping high-voltage vacuum tube amplifiers into 48kHz 24-bit parametric neural datasets.

---

## 1. ⚠️ The Non-Negotiable Output Transformer Safety Axiom

> [!CAUTION]
> **NEVER OPERATE A TUBE AMPLIFIER WITHOUT AN ACTIVE LOAD CONNECTED TO THE SPEAKER JACK.**
> Tube amplifiers require a continuous secondary load impedance (8Ω or 16Ω). If a tube amplifier is powered on or taken off standby into an open circuit (no load or disconnected cable), inductive flyback voltage spikes will exceed **2,000 to 3,000 Volts**. This arcs through the output transformer's paper insulation, incinerates the primary windings, and destroys your amplifier!

### The Speaker Cable Mandate
- **Always use a heavy unshielded 14AWG or 16AWG SPEAKER CABLE** between the tube amp's Speaker Output jack and the Two Notes Torpedo Captor or Suhr Reactive Loadbox input.
- **NEVER use a thin shielded guitar instrument cable** for the speaker connection. The thin center conductor of a guitar cable cannot dissipate the high electrical current of a 50W–100W power section. It will heat up, melt, and sever the connection under load—instantly subjecting your output transformer to an open circuit blowout!

---

## 2. Complete Physical Signal Flow & Wiring

```
[Mac / PC DAW: Cockos REAPER or Python reamp_automation.py]
  │ (USB-C / Thunderbolt)
  ▼
[Audio Interface: Focusrite Scarlett / Apollo Twin]
  │ Line Out 3 (+4dBu Balanced 1/4" TRS Cable)
  ▼
[Radial Re-Amp Box (ProRmp or X-Amp)]
  ├─ Custom Isolation Transformer
  ├─ Ground Lift Switch: ENGAGED (pressed IN)
  ├─ Level Trim Pot: Set to ~65-75% (~ -14dBu Instrument Level)
  │ High-Z Shielded Guitar Instrument Cable (Unbalanced 1/4" TS)
  ▼
[Physical Tube Guitar Amp Head (e.g. 50W 6L6/EL34)]
  ├─ Front Guitar Input (1MΩ High-Z)
  ├─ Preamp & EQ Tone Stack (Gain, Bass, Mid, Treble, Master)
  │ Power Tubes & Output Transformer
  │ !!! 14AWG / 16AWG UNSHIELDED SPEAKER CABLE ONLY !!!
  ▼
[Two Notes Torpedo Captor / Suhr Reactive Load (8Ω or 16Ω In)]
  ├─ Reactive Voice Coil RLC Network (Dissipates up to 100W RMS heat)
  │ Balanced Line Out (1/4" TRS or XLR Cable)
  ▼
[Audio Interface: Line In 1 (Balanced Line Level, Preamp Pad as needed)]
  │ 48kHz 24-bit A/D Conversion (Peaking strictly at -12dBFS to -6dBFS)
  ▼
[DAW Storage: Recorded 48kHz 24-bit Take]
```

---

## 3. Power-On & Standby Sequence (Preventing Cathode Stripping)

Vacuum tube cathodes are coated with a fragile barium-strontium oxide emitter that requires thermionic heat (~1,000°C) before electrons can flow safely to the anode plate. Applying high voltage (350V–500V DC) to a cold cathode rips the coating off (cathode stripping), rapidly destroying your tubes.

### Golden Power-Up Routine:
1. Verify the **Speaker Output** is connected to the **Two Notes Captor** with an unshielded speaker cable.
2. Confirm the **Standby Switch** is set to **STANDBY** (OFF).
3. Flip the **Power Switch** to **ON**.
4. Wait at least **60 to 90 seconds**. Look at the tubes through the chassis grille to confirm the filament heaters are glowing a steady warm orange.
5. Flip the **Standby Switch** to **ON** (Play mode).
6. **The 5-Minute Thermal Stabilization Rule**: Let the amplifier idle under active plate current for **at least 5 to 10 minutes** before firing Take 0. This ensures tube bias, plate resistance, and transformer temperature stabilize, preventing thermal drift from contaminating your first 10 takes!

### Power-Down Routine:
1. Flip the **Standby Switch** to **STANDBY** (OFF).
2. Wait 15 seconds for capacitors to bleed residual transient voltage.
3. Flip the **Power Switch** to **OFF**.

---

## 4. Pristine Gain Staging & dBFS Targets

| Stage | Target Level | Notes |
|---|---|---|
| **DAW Playback (Out 3)** | `0.0 dBFS True Peak` | Unity digital D/A conversion. Do not lower DAW faders (preserves full 24-bit resolution). |
| **Radial Re-Amp Level Trim** | `65% to 75% rotation` | Produces ~300mV–500mV RMS, accurately matching passive guitar humbucker pickups. |
| **Two Notes Captor Line Out** | Direct balanced line level | Connects via balanced 1/4" TRS to audio interface Line In 1. |
| **Interface Line In Preamp** | `-12.0 dBFS to -6.0 dBFS Peak` | Calibrated on the loudest, highest-gain transient chirp. Leaves a **6dB safety cushion**. |

### Why the 6dB Headroom Cushion Matters
Analog tube saturation is smooth, musical, and soft-knee. However, if an unexpected resonant spike hits 0.0dBFS at the audio interface's A/D converter, the converter will clip with a harsh, flat-topped square wave. The neural network will attempt to learn this catastrophic converter distortion, corrupting the entire model!

---

## 5. Ground Loop Hum Triage Protocol

If you hear a 60Hz hum or electromagnetic buzz when you connect the re-amp box:
1. **Engage Ground Lift**: Press the **LIFT** button on the Radial Re-Amp box. This severs the chassis copper path between computer and amp while passing pure audio magnetically through the transformer core.
2. **Star-Ground AC Power**: Plug your audio interface, Mac/PC, and tube amplifier into the **same heavy-duty surge-protected outlet strip**. This eliminates any voltage differential between separate wall outlets.
3. **Physical Distance**: Place the Radial Re-Amp box and audio cables at least **2 feet away** from the amplifier's heavy power transformer. Large power transformers emit stray 60Hz magnetic fields that induce noise directly into passive inductors.
4. **180° Polarity Check**: If combining re-amped audio with a dry DI or acoustic mic, toggle the 180° polarity switch on the re-amp box to test for low-frequency phase cancellation.

---

## 6. Quick Studio Reference Card

```
REAPER Action List Shortcut:  F1 (Reaper_AutoReamp_NAM.lua)
Python Automated Terminal:    python scripts/reamp_automation.py --device <id> --out-ch 3 --in-ch 1
Latin Hypercube Matrix:       data/justin_nam_run_sheet.csv (45 takes)
RFC 8259 Training Manifest:   data/data.json
Google Colab Notebook:        notebooks/colab_train_parametric_nam.ipynb (T4 GPU runtime)
NAM Plugin Recommended:       Steven Atkinson Official NAM VST3/AU + Celestion 4x12 IR loader
```
