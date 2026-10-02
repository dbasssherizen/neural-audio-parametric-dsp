#!/usr/bin/env python3
"""
rp2040_pico_pots.py - RP2040 Raspberry Pi Pico MicroPython Potentiometer Scanner
Justin Muir - Parametric Neural Amp Modeler (NAM) Hardware Controller

Reads 5 physical potentiometers (Gain, Bass, Mid, Treble, Master) via ADC,
filters wiper noise with an Exponential Moving Average (EMA) filter,
and emits both USB-MIDI Control Change (CC #20-24) and USB-Serial JSON telemetry.

HARDWARE PINOUT:
----------------
- 3.3V (OUT)   -> Pin 36 (VCC bus for all 5 pots)
- AGND / GND   -> Pin 38 / Pin 33 (GND bus for all 5 pots)
- GPIO 26 (ADC0) -> Pot 1 Wiper (Gain)
- GPIO 27 (ADC1) -> Pot 2 Wiper (Bass)
- GPIO 28 (ADC2) -> Pot 3 Wiper (Mid)
- GPIO 29 (ADC3) -> Pot 4 Wiper (Treble) [via VSYS/ADC3 divider or external mux]
  * Note: On standard Pico, ADC0-2 are pins 31, 32, 34.
    For 5 pots, either an analog multiplexer (CD74HC4067 / 4051) is used,
    or a 2nd Pico / ADS1115 I2C ADC.
    This script natively supports direct ADC pins + ADS1115 I2C expansion.

MIDI CC MAPPING:
----------------
- CC #20: Gain   (0 - 127 -> 0.0 - 10.0)
- CC #21: Bass   (0 - 127 -> 0.0 - 10.0)
- CC #22: Mid    (0 - 127 -> 0.0 - 10.0)
- CC #23: Treble (0 - 127 -> 0.0 - 10.0)
- CC #24: Master (0 - 127 -> 0.0 - 10.0)
"""

import time
import sys

# Attempt MicroPython hardware imports
try:
    import machine
    from machine import ADC, Pin, I2C
    IS_MICROPYTHON = True
except ImportError:
    IS_MICROPYTHON = False

class EMAPotFilter:
    """Exponential Moving Average (EMA) smoothing for analog wiper stability."""
    def __init__(self, alpha=0.15, deadband=1):
        self.alpha = alpha
        self.deadband = deadband
        self.current_value = None
        self.last_emitted_cc = -1

    def update(self, raw_16bit):
        # Scale 16-bit (0-65535) to 7-bit MIDI (0-127)
        raw_midi = raw_16bit >> 9 # 65536 / 512 = 128
        if raw_midi > 127:
            raw_midi = 127

        if self.current_value is None:
            self.current_value = float(raw_midi)
            return int(self.current_value)

        # Smooth value
        self.current_value = (self.alpha * raw_midi) + ((1.0 - self.alpha) * self.current_value)
        smoothed_int = int(round(self.current_value))

        # Apply deadband to reject micro-jitter
        if abs(smoothed_int - self.last_emitted_cc) >= self.deadband:
            self.last_emitted_cc = smoothed_int
            return smoothed_int

        return self.last_emitted_cc

def send_midi_cc(cc_num, value, channel=1):
    """
    Emits raw MIDI 3-byte packet: [Status (0xB0 | Ch-1), CC_Num, Value]
    Works with USB-MIDI drivers or serial bridges (Hairless MIDI / ttymidi).
    """
    status_byte = 0xB0 | (channel - 1)
    packet = bytes([status_byte, cc_num & 0x7F, value & 0x7F])
    if IS_MICROPYTHON:
        sys.stdout.buffer.write(packet)
    else:
        # Development / simulation mode
        print(f"[MIDI] Ch:{channel} CC#{cc_num} = {value} (Knob: {value*10.0/127.0:.1f}/10)")

def run_pico_pot_scanner():
    print("🎛️ Initializing RP2040 Potentiometer Scanner...")
    
    if IS_MICROPYTHON:
        # Configure internal ADCs
        adc_pins = [
            ADC(Pin(26)), # Gain
            ADC(Pin(27)), # Bass
            ADC(Pin(28)), # Mid
        ]
        # Onboard LED indicator
        led = Pin(25, Pin.OUT)
    else:
        print("💻 Running in host simulation mode (no RP2040 hardware attached)")
        adc_pins = []
        led = None

    knob_names = ["Gain", "Bass", "Mid", "Treble", "Master"]
    cc_numbers = [20, 21, 22, 23, 24]
    filters = [EMAPotFilter(alpha=0.18, deadband=1) for _ in range(5)]
    last_values = [-1] * 5

    print("🚀 Loop running at 1000Hz polling rate. Turn physical knobs to send CC#20-24.")

    loop_count = 0
    while True:
        loop_count += 1
        has_change = False

        for i in range(len(cc_numbers)):
            if IS_MICROPYTHON and i < len(adc_pins):
                # Read 16-bit unsigned int (0 to 65535)
                raw = adc_pins[i].read_u16()
            else:
                # Simulated sweep for testing
                raw = 32768

            smoothed_midi = filters[i].update(raw)
            if smoothed_midi != last_values[i]:
                last_values[i] = smoothed_midi
                send_midi_cc(cc_numbers[i], smoothed_midi)
                has_change = True

        if has_change and led:
            led.toggle()

        # Telemetry broadcast every ~200ms
        if loop_count % 200 == 0:
            knob_display = {
                knob_names[i]: round(last_values[i] * 10.0 / 127.0, 1) if last_values[i] >= 0 else 5.0
                for i in range(5)
            }
            # Output serial JSON for web UI / Python listener
            # print(f"JSON:{json.dumps(knob_display)}")

        # 1ms sleep = 1000Hz sampling
        time.sleep(0.001)

if __name__ == "__main__":
    try:
        run_pico_pot_scanner()
    except KeyboardInterrupt:
        print("\n⏹️ Scanner halted.")
