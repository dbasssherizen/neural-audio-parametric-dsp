#!/usr/bin/env python3
"""
Sovereign AI Academy: Advanced Module — Structured Schemas (JSON, YAML, BAML)
Author: MAX (Anima Ex Machina) & Daniel Bass Sherizen
Target: Justin Muir (NetOps & Neural Audio Architecture)

Purpose:
    Reference demonstration of how data evolves from free-form natural language
    into universal machine wire formats (JSON), declarative NetOps configs (YAML),
    and type-safe AI prompting schemas (BAML).

    [UNLOCK WHEN READY]: Run this script when you want to understand how our web
    portal, REAPER scripts, and local Gemma models exchange structured data.

Usage:
    python3 scripts/demo_structured_schemas.py
"""

import json
from typing import Dict, Any, List

def demo_json():
    print("=" * 70)
    print(" 1. JSON (JavaScript Object Notation): The Universal Machine Wire")
    print("=" * 70)
    print("In your audio world, every .nam neural model and web API speaks JSON.")
    print("It uses strict key-value pairs, quotes, brackets, and curly braces.\n")

    # Real-world NAM knob configuration represented as JSON
    nam_take_config = {
        "model_name": "Marshall_Origin50_EdgeOfBreakup",
        "sample_rate": 48000,
        "bit_depth": 24,
        "knobs": {
            "gain": 6.5,
            "bass": 5.0,
            "middle": 6.0,
            "treble": 7.0,
            "master": 7.5,
            "presence": 6.0,
            "tilt": 7.2,
            "boost": True
        },
        "takes_analyzed": [12, 18, 24, 32],
        "measured_esr_loss": 0.0078
    }

    json_str = json.dumps(nam_take_config, indent=2)
    print(json_str)
    print("\n✓ Notice: Computers love this because any language (Python, C++, JS) can parse it instantly.")


def demo_yaml():
    print("\n" + "=" * 70)
    print(" 2. YAML (YAML Ain't Markup Language): Declarative NetOps Configs")
    print("=" * 70)
    print("In your NetOps world (Proxmox, Docker, pfSense, GitHub Actions), YAML replaces")
    print("messy JSON braces with clean, human-readable indentation.\n")

    yaml_example = """# Studio Re-Amp Automation Matrix Configuration
version: "3.3"
device: "IK Multimedia AXE I/O"
audio:
  driver: "ALSA / ASIO"
  sample_rate: 48000
  buffer_size: 64
  routing:
    direct_in: "Input 1 (Z-TONE PASSIVE)"
    reamp_out: "Line Out 5 (AMP JACK)"
    return_mic: "Input 2 (XLR SM57)"

netops_monitoring:
  gateway_ip: "1.1.1.1"
  alert_jitter_threshold_ms: 5.0
  auto_pause_reamp_on_jitter: true
"""
    print(yaml_example)
    print("✓ Notice: No curly braces, no trailing comma errors. Clean and readable like a sound check sheet.")


def demo_baml():
    print("\n" + "=" * 70)
    print(" 3. BAML (Boundary's Almost Markdown Language): Type-Safe AI Prompts")
    print("=" * 70)
    print("The biggest flaw with standard ChatGPT / LLMs is that they return messy conversational")
    print("text when you just want raw, clean data.")
    print("BAML solves this by enforcing a strict schema contract with the AI model.\n")

    baml_schema_example = """// BAML Schema for Studio Re-Amp Audio Ingestion
class ReampTakeMetadata {
  take_number int @description("Take sequence number 1 to 42")
  gain_setting float @description("Gain knob 0.0 to 10.0")
  tilt_setting float @description("Tilt knob 0.0 to 10.0")
  boost_engaged bool @description("Whether pull-boost switch was active")
  tone_notes string @description("Brief description of pickup dynamics")
}

function ExtractAudioNotes(unstructured_email: string) -> ReampTakeMetadata {
  client Gemma4_12B
  prompt #"
    Extract the exact studio hardware settings from Justin's session notes:
    {{ unstructured_email }}
  "#
}
"""
    print(baml_schema_example)
    print("✓ Why BAML is magic:")
    print("  1. The LLM is mathematically constrained to return ONLY valid fields.")
    print("  2. If the LLM generates an invalid string for a float, BAML automatically self-corrects.")
    print("  3. Your Python or C++ plugin receives a native, type-safe class with zero regex code.")


def main():
    print("🎣 SOVEREIGN AI ACADEMY: ADVANCED STRUCTURED DATA SUITE")
    print("   Prepared for Justin Muir | When You Are Ready To Level Up")
    demo_json()
    demo_yaml()
    demo_baml()
    print("\n" + "=" * 70)
    print("Summary:")
    print("• Markdown (.md) is how you think and write.")
    print("• YAML (.yaml) is how you configure networks, daemons, and servers.")
    print("• JSON (.json) is how software packages exchange live state.")
    print("• BAML (.baml) is how you force AI models to output flawless structured data.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
