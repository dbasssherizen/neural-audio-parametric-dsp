#!/usr/bin/env python3
"""
esp32_ble_midi.py - ESP32 / ESP32-S3 Wireless BLE MIDI Controller for Parametric NAM
Justin Muir - Parametric Neural Amp Modeler Studio Hardware Bridge

Broadcasts standard Bluetooth Low Energy MIDI (Apple/MMA MIDI over BLE specification).
Allows wireless knob control over iPad, macOS, Windows, and Linux audio hosts.

PINOUT (ESP32-S3 / ESP32 Standard):
-----------------------------------
- 3V3          -> VCC rail for 5 potentiometers
- GND          -> Ground rail for 5 potentiometers
- GPIO 32 (ADC1_CH4) -> Gain Pot Wiper
- GPIO 33 (ADC1_CH5) -> Bass Pot Wiper
- GPIO 34 (ADC1_CH6) -> Mid Pot Wiper
- GPIO 35 (ADC1_CH7) -> Treble Pot Wiper
- GPIO 36 (ADC1_CH0) -> Master Pot Wiper

BLE MIDI SPECIFICATION:
-----------------------
- Service UUID: 03b80e5a-ede8-4b33-a028-d17a7430783c
- Characteristic UUID: 7772e5db-3868-4112-a1a9-f2669d106bf3 (Read/Write/Notify)
- Control Change (CC) #20 (Gain), #21 (Bass), #22 (Mid), #23 (Treble), #24 (Master)
"""

import time
import struct

try:
    import machine
    from machine import ADC, Pin
    import ubluetooth as bluetooth
    IS_MICROPYTHON = True
except ImportError:
    IS_MICROPYTHON = False

# BLE MIDI UUIDs (Standard MIDI over Bluetooth LE Specification)
_MIDI_SERVICE_UUID = bluetooth.UUID("03b80e5a-ede8-4b33-a028-d17a7430783c") if IS_MICROPYTHON else None
_MIDI_CHAR_UUID    = bluetooth.UUID("7772e5db-3868-4112-a1a9-f2669d106bf3") if IS_MICROPYTHON else None

class BLEMIDIServer:
    def __init__(self, name="Justin-Parametric-NAM"):
        self.name = name
        self.conn_handle = None
        if not IS_MICROPYTHON:
            print(f"💻 Simulated BLE MIDI Server '{name}' running (Host mode)")
            return

        self.ble = bluetooth.BLE()
        self.ble.active(True)
        self.ble.irq(self._irq)

        # Register MIDI Service & Characteristic (Notify & Write Without Response)
        service = (_MIDI_SERVICE_UUID, ((_MIDI_CHAR_UUID, bluetooth.FLAG_READ | bluetooth.FLAG_NOTIFY | bluetooth.FLAG_WRITE_NO_RESP),))
        ((self.char_handle,),) = self.ble.gatts_register_services((service,))
        self._start_advertising()

    def _irq(self, event, data):
        if event == 1: # _IRQ_CENTRAL_CONNECT
            self.conn_handle, _, _ = data
            print(f"📶 Central Connected: {self.conn_handle}")
        elif event == 2: # _IRQ_CENTRAL_DISCONNECT
            print(f"📴 Central Disconnected: {self.conn_handle}")
            self.conn_handle = None
            self._start_advertising()

    def _start_advertising(self):
        print(f"📡 Broadcasting BLE MIDI as '{self.name}'...")
        payload = bytearray()
        # Flags
        payload.extend(b"\x02\x01\x06")
        # Complete Name
        name_bytes = self.name.encode()
        payload.extend(bytes([len(name_bytes) + 1, 0x09]) + name_bytes)
        self.ble.gap_advertise(100_000, adv_data=payload)

    def send_midi_cc(self, cc_num, value, channel=1):
        if not IS_MICROPYTHON or self.conn_handle is None:
            if not IS_MICROPYTHON:
                print(f"[BLE-MIDI] Ch:{channel} CC#{cc_num} = {value} ({value*10.0/127.0:.1f}/10)")
            return

        # BLE-MIDI packet format:
        # [Header (0x80 | timestamp_high), Timestamp (0x80 | timestamp_low), Status, CC_Num, Value]
        timestamp_low = (time.ticks_ms() & 0x7F) | 0x80
        header = 0x80 | ((time.ticks_ms() >> 7) & 0x3F)
        status = 0xB0 | (channel - 1)

        packet = bytes([header, timestamp_low, status, cc_num & 0x7F, value & 0x7F])
        try:
            self.ble.gatts_notify(self.conn_handle, self.char_handle, packet)
        except Exception as e:
            pass

class EMAPotFilter:
    def __init__(self, alpha=0.15, deadband=1):
        self.alpha = alpha
        self.deadband = deadband
        self.current_value = None
        self.last_emitted_cc = -1

    def update(self, raw_12bit):
        # Scale 12-bit (0-4095) to 7-bit MIDI (0-127)
        raw_midi = raw_12bit >> 5 # 4096 / 32 = 128
        if raw_midi > 127:
            raw_midi = 127

        if self.current_value is None:
            self.current_value = float(raw_midi)
            return int(self.current_value)

        self.current_value = (self.alpha * raw_midi) + ((1.0 - self.alpha) * self.current_value)
        smoothed_int = int(round(self.current_value))

        if abs(smoothed_int - self.last_emitted_cc) >= self.deadband:
            self.last_emitted_cc = smoothed_int
            return smoothed_int

        return self.last_emitted_cc

def run_esp32_ble_bridge():
    server = BLEMIDIServer()

    adc_channels = []
    if IS_MICROPYTHON:
        pins = [32, 33, 34, 35, 36]
        for p in pins:
            adc = ADC(Pin(p))
            adc.atten(ADC.ATTN_11DB) # 0V - 3.3V range
            adc.width(ADC.WIDTH_12BIT)
            adc_channels.append(adc)

    filters = [EMAPotFilter(alpha=0.18, deadband=1) for _ in range(5)]
    cc_map = [20, 21, 22, 23, 24] # Gain, Bass, Mid, Treble, Master
    last_vals = [-1] * 5

    print("🚀 ESP32 BLE MIDI Potentiometer scanner running...")
    while True:
        for idx in range(5):
            if IS_MICROPYTHON and idx < len(adc_channels):
                raw = adc_channels[idx].read()
            else:
                raw = 2048

            val = filters[idx].update(raw)
            if val != last_vals[idx]:
                last_vals[idx] = val
                server.send_midi_cc(cc_map[idx], val)

        time.sleep(0.002) # 500Hz polling rate

if __name__ == "__main__":
    run_esp32_ble_bridge()
