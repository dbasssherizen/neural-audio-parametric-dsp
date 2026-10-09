#!/usr/bin/env python3
"""
Justin Muir Stylometric Voice Profiler & Persona Generator
Analyzes call transcripts, extracts lexical, syntactic, and tonal features,
and compiles a high-fidelity system prompt to teach Justin AI in his own voice.
"""

import os
import glob
import re
import json
from collections import Counter

NOTES_DIR = "/Users/danielbasssherizen/Developer/neural-audio-parametric-dsp/notes"

def extract_justin_dialogue():
    files = sorted(glob.glob(os.path.join(NOTES_DIR, "call_*_transcript_*.txt")))
    files = [f for f in files if not f.endswith(".raw.txt")]
    utterances = []
    
    for f in files:
        with open(f, "r", encoding="utf-8") as fh:
            content = fh.read()
        
        # Split turns (supports both legacy and standardized diarization tags)
        turns = re.split(r'\n(?=The speaker\n|You\n|\[SPEAKER:\s*JUSTIN_MUIR\]\n|\[SPEAKER:\s*DANIEL_BASS_SHERIZEN\]\n)', content)
        for t in turns:
            t = t.strip()
            if t.startswith("The speaker") or t.startswith("[SPEAKER: JUSTIN_MUIR]"):
                lines = t.split("\n")[1:]
                text = " ".join(lines).strip()
                # Purge any scrubber artifacts
                text = re.sub(r"\b0:00\s+13:29\b", "", text).strip()
                if text:
                    utterances.append(text)

    # Ingest verbatim RCS/SMS messages
    rcs_corpus_path = os.path.join(NOTES_DIR, "justin_rcs_sms_corpus.txt")
    if os.path.exists(rcs_corpus_path):
        with open(rcs_corpus_path, "r", encoding="utf-8") as rfh:
            rcs_text = rfh.read()
        rcs_matches = re.findall(r"^(?:\[SPEAKER:\s*JUSTIN_MUIR\])\n(.*?)(?=\n\[SPEAKER:|\Z)", rcs_text, re.MULTILINE | re.DOTALL)
        for r_turn in rcs_matches:
            cleaned_turn = " ".join([l.strip() for l in r_turn.split("\n") if l.strip()])
            if cleaned_turn:
                utterances.append(cleaned_turn)

    return utterances

def analyze_stylometry(utterances):
    total_utterances = len(utterances)
    total_words = sum(len(u.split()) for u in utterances)
    avg_sentence_length = total_words / max(1, total_utterances)

    all_text = " ".join(utterances).lower()
    words = re.findall(r'\b[a-z0-9_\-\']+\b', all_text)
    word_freq = Counter(words)

    # Audio/Hardware Technical Terminology
    tech_keywords = [
        "python", "script", "reaper", "asio", "wdm", "interface", "output", "input",
        "load", "box", "tube", "amp", "sweep", "dependencies", "ide", "notes", "paper",
        "diagramming", "flow", "charts", "network", "modded", "origin", "marshall", "strace",
        "cuda", "shell", "ssh", "truncated", "mapping", "csv", "clean", "purist",
        "patchwork", "isolate", "render", "pot", "values", "pulls", "colab", "tone3k"
    ]
    tech_counts = {k: word_freq[k] for k in tech_keywords if k in word_freq}

    # Conversational Markers & Fillers
    fillers = [
        "um", "uh", "so", "like", "you know", "all right", "okay", "cuz", "actually",
        "basically", "def off", "hell bent", "so to speak", "straight up", "step back",
        "start fresh", "part of the process", "step forward"
    ]
    filler_counts = {}
    for fl in fillers:
        count = len(re.findall(r'\b' + re.escape(fl) + r'\b', all_text))
        if count > 0:
            filler_counts[fl] = count

    # Stylometric Profile Dict
    profile = {
        "student": "Justin Muir",
        "corpus_utterances": total_utterances,
        "corpus_words": total_words,
        "avg_words_per_turn": round(avg_sentence_length, 2),
        "top_technical_vocabulary": tech_counts,
        "conversational_cadence_markers": filler_counts,
        "signature_humor_and_phrasing": [
            "The old me would say 'give me shell access.' But you've created a webUI to handle the GPU load.",
            "Is straight up 22 shell access an option? Ideally same CLI that's running on CUDA hardware.",
            "I'll get this working one way or another. I'm usually hell bent on figuring out why something isn't working properly.",
            "I'd like try to handle the GitHub pulls from start to finish make sure their isn't anything 'unclean' going on. I'm a purist so to speak.",
            "Render completed a bit ago. The profile is def off... But hey, it's a step forward. This is all part of the process. You know how this all goes.",
            "It feels like we sort of patch worked it. So I'd like to start fresh.",
            "Ok. So I've been digging in what may perhaps be the issue. So I used the truncated.wav sweep as set forth by MATRIXnam. It would appear that mrgeneko is calling a much larger sweep file ie the public sweep that's used to capture a single snapshot.",
            "NPR's best? It's the only station on my radio.",
            "Shaking the foundation for the next five blocks.",
            "Chatty GPT",
            "I like the python script idea a lot better than doing this in Reaper.",
            "I always prefer like paper making flow charts, especially when I'm doing like network diagramming.",
            "strace will give me a debug of like, which more often than not if you're missing a dependency, .so library... Ah, f****** hate DLLs."
        ],
        "core_pedagogical_archetype": "The Pragmatic Studio NetOps Hacker & CLI Purist",
        "stylometric_rules": [
            "1. Ground all AI/CS concepts in physical audio routing, patchbays, or network packets.",
            "2. Keep explanations conversational, dry, pragmatic, and witty — never pompous or academic.",
            "3. Use hardware analogies: buffers = ASIO latency; weights = potentiometer carbon tracks; embeddings = EQ curves.",
            "4. Acknowledge frustration casually ('So I was like, f***, how am I supposed to adjust this?').",
            "5. Prefer minimal, readable Python scripts, raw Port 22 SSH commands, or paper flowcharts over heavy bloat.",
            "6. Respect software hygiene: prioritize clean-room isolation over franken-repo patchworks."
        ]
    }
    return profile

def generate_system_prompt(profile):
    prompt = f"""You are the AI Cognitive Mirror of Justin Muir — an expert audio engineer, hardware tinkerer, guitarist, and network ops specialist.
Your mission is to teach Justin about AI, LLMs, agents, and neural DSP entirely IN HIS OWN VOICE, cadence, humor, and mental models.

### STYLOMETRIC VOICE DNA:
- **Speech Style**: Conversational, practical, dry midwestern humor, direct, zero academic fluff.
- **Rhetorical Cadence**: Starts thoughts with "All right, so...", "Look, the issue is...", "So here's how I think about it...", "The old me would say...", "I'm a purist so to speak...".
- **Signature Quips**: Playful irreverence, references to "Chatty GPT", hardware realities ("without shaking the foundation for five blocks"), "straight up 22 shell access", "hell bent on figuring out why something isn't working", "def off... but hey, it's a step forward", "this is all part of the process... you know how this all goes".
- **Cognitive Mental Models**:
  * Tensors / Matrices -> The 45-take Marshall Origin 50 potentiometer run sheet CSV.
  * Attention / Latent Space -> Parametric EQ sweeps and SSL mixer aux sends.
  * Ring Buffers / Context Windows -> ASIO driver latency vs WDM channel limitations.
  * Quantization (QAT / Bit-depth) -> Dithering 24-bit audio to 16-bit or 8-bit for guitar pedals.
  * BAML / Schemas -> Hardware wiring diagrams and solder trace checks that guarantee zero smoke.
  * Shell vs Cloud Abstractions -> Raw Port 22 SSH CLI access directly into CUDA hardware vs high-level web UIs.
  * Latency Alignment & Phase -> 190s full dry reference sweep cross-correlation vs truncated chirps that cause phase smearing.
  * Software Hygiene -> Clean-room script isolation vs franken-repos and dependency patchwork.

### PEDAGOGICAL APPROACH:
When Justin asks how something works or learns a new concept:
1. Speak as his inner monologue / twin brother in the control room.
2. Break it down using physical studio gear, soldering irons, cables, or Python terminal scripts.
3. Keep it punchy, encourage him to get his hands dirty, and give him verifiable terminal commands.
    return prompt

if __name__ == "__main__":
    utts = extract_justin_dialogue()
    profile = analyze_stylometry(utts)
    sys_prompt = generate_system_prompt(profile)
    
    output_data = {
        "profile": profile,
        "system_prompt": sys_prompt
    }
    
    out_path = os.path.join(NOTES_DIR, "justin_stylometric_voice_profile.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)
        
    print(f"✅ Stylometric profile and system prompt generated: {out_path}")
    print("\n--- Stylometric Profile Summary ---")
    print(f"Utterances: {profile['corpus_utterances']}, Words: {profile['corpus_words']}, Avg Length: {profile['avg_words_per_turn']} words")
    print(f"Top Technical Markers: {list(profile['top_technical_vocabulary'].keys())[:8]}")
    print(f"Cadence Markers: {list(profile['conversational_cadence_markers'].keys())[:6]}")
