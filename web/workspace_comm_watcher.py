#!/usr/bin/env python3
"""
Sovereign AI Academy: Workspace Multi-Channel Communication Watcher & Pedagogical State Machine
Author: MAX (Anima Ex Machina) & Daniel Bass Sherizen
Target: Justin Muir (+1 630-418-9227 / nightmareglove@gmail.com)

Architecture:
    Zero-ADB Multi-Channel Ingestion Hub decoupled from physical USB/Wi-Fi phone connection.
    Monitors communications across:
      1. Google Pixel Gemini Call Notes transcripts (local drops, Drive sync, notes/*.txt)
      2. Google Meet recordings & Gemini Meeting Notes
      3. Google Messages RCS via Chrome/Workspace (REST API on port 5042 & webhook ingest)
      4. Opportunistic ADB content://sms fallback (when phone is attached)

Pedagogical State Machine:
    Stage 1: Tactical Foundations (Colab GPU, NotebookLM, Gemma 4 12B/31B, NL Daemon) [ACTIVE]
    Stage 2: Markdown & Karpathy Minimal Wikis [LOCKED -> UNLOCKS on notes/format/table signals]
    Stage 3: Structured Schemas (JSON, YAML, BAML) [LOCKED -> UNLOCKS on schemas/API/automation signals]
    Stage 4: TurboQuant Vector Memory & AutoResearch [LOCKED -> UNLOCKS on scale/overnight signals]

Usage:
    python3 scripts/workspace_comm_watcher.py --status
    python3 scripts/workspace_comm_watcher.py --ingest-file notes/call_2_transcript_20261006.txt
    python3 scripts/workspace_comm_watcher.py --ingest-text "How do I format these knob values into a clean table?"
    python3 scripts/workspace_comm_watcher.py --daemon --port 5042
    python3 scripts/workspace_comm_watcher.py --simulate-trigger 2
"""

import sys
import os
import time
import json
import hashlib
import logging
import argparse
import subprocess
import shlex
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

# Directory Anchors
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOTES_DIR = os.path.join(PROJECT_ROOT, "notes")
OUTBOX_DIR = os.path.join(NOTES_DIR, "outbox")
WEB_DIR = os.path.join(PROJECT_ROOT, "web")
STATE_FILE = os.path.join(NOTES_DIR, "pedagogical_state.json")
LOG_FILE = os.path.join(NOTES_DIR, "watcher_activity.log")
EVENTS_LOG = os.path.join(NOTES_DIR, "pedagogical_events.log")
PROCESSED_FILES_LOG = os.path.join(NOTES_DIR, "watcher_processed_files.json")
ADB_BIN = "/Users/danielbasssherizen/Library/Android/sdk/platform-tools/adb"

os.makedirs(NOTES_DIR, exist_ok=True)
os.makedirs(OUTBOX_DIR, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [COMM-WATCHER] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding="utf-8")
    ]
)
logger = logging.getLogger("WorkspaceCommWatcher")

# Target Contact Matching
JUSTIN_PHONE_FRAGMENTS = ["6304189227", "630-418-9227", "+16304189227"]
JUSTIN_NAME_FRAGMENTS = ["justin", "justin muir", "the speaker"]
JUSTIN_EMAIL_TARGETS = ["nightmareglove@gmail.com", "nightmare.glove@gmail.com"]

# Pedagogical Stage Definitions & Transition Rules
PEDAGOGICAL_STAGES = {
    1: {
        "id": 1,
        "name": "Tactical Foundations",
        "tagline": "Cloud GPUs, WaveNets & Private Gemma 4 Checkpoints",
        "status": "ACTIVE",
        "unlock_threshold": 0,
        "curriculum": [
            "Colab GPU WaveNet Training (marshall_origin50.ipynb)",
            "NotebookLM Grounded Audio Overviews (Studio Research Vault)",
            "Antigravity 2.0 TUI & Pair Programming (agy CLI)",
            "Gemma 4 12B Unified with Native Audio Tokens (Transient Analysis)",
            "Gemma 4 31B Dense Flagship with 256K Context & Thinking Modes",
            "Conversational NetOps Daemon (nl_daemon_bridge.py on port 5040)"
        ],
        "lab_anchor": "#lab-colab",
        "dispatch_template": {
            "email_subject": "Sovereign AI Academy: Tactical Foundations Live for Justin Muir",
            "headline": "Welcome to Stage 1: Autonomous AI Modeling",
            "body": "Justin, your academy is live with Colab GPU training, NotebookLM research vaults, and Gemma 4 checkpoints."
        }
    },
    2: {
        "id": 2,
        "name": "Markdown & The Karpathy Minimal Wiki",
        "tagline": "Frictionless Text Formatting & Agent Second Brains",
        "status": "STAGED",
        "unlock_threshold": 70,
        "curriculum": [
            "Why Markdown (.md) is the Native Lingua Franca of AI Agents",
            "Karpathy's Minimal Wiki Architecture: Single Folder of Markdown",
            "Structuring Amp Settings, Run Sheets & Tube Biasing Logs",
            "How Agentic RAG Scans Headers (##) and Bullet Lists Instantly",
            "Building Your Personal Studio Knowledge Vault"
        ],
        "lab_anchor": "#lab-markdown-wiki",
        "signal_rules": [
            {"keywords": ["where do i write", "where should i save", "notes", "organize", "format", "documentation", "doc", "keep track", "log", "table", "markdown", "wiki"], "weight": 25},
            {"keywords": ["messy", "confusing", "lost my settings", "amp settings list", "take notes"], "weight": 20}
        ],
        "dispatch_template": {
            "email_subject": "Stage 2 Unlocked: Markdown & The Karpathy Minimal Wiki",
            "headline": "Stage 2 Mastery: How Humans Talk to AI Agents Frictionlessly",
            "body": (
                "Hey Justin!\n\n"
                "Saw your question about organizing and keeping track of your take notes and amp settings. "
                "You just unlocked Stage 2 of the Sovereign AI Academy: Markdown & The Karpathy Minimal Wiki.\n\n"
                "In audio and AI engineering, proprietary Word docs and messy text dumps create friction for AI models. "
                "Markdown (.md) is lightweight, renders everywhere, and lets LLMs parse headers, tables, and code blocks with zero hallucination.\n\n"
                "Check out the newly unlocked Lab 7 on your hub: https://justin-netops-hub.web.app\n"
                "We've added a template studio run sheet and a guide to building a Karpathy-style single-folder knowledge wiki."
            ),
            "sms_snippet": "Hey Justin! Unlocked Stage 2 on your hub: Markdown & The Karpathy Minimal Wiki. Check it out at https://justin-netops-hub.web.app"
        }
    },
    3: {
        "id": 3,
        "name": "Structured Schemas (JSON, YAML, BAML)",
        "tagline": "Type-Safe Rig Automation & Deterministic LLM Outputs",
        "status": "LOCKED",
        "unlock_threshold": 75,
        "curriculum": [
            "JSON for Web Dashboards & Neural Sweep Manifests",
            "YAML for Clean Hardware Re-Amp Matrices & Configuration",
            "BAML: Boundary Abstract Modeling Language for 100% Type-Safe LLM Outputs",
            "Integrating Structured Outputs with REAPER ReaScript (Lua)",
            "Automated Potentiometer Extraction with Zero Markdown Hallucinations"
        ],
        "lab_anchor": "#lab-structured-schemas",
        "signal_rules": [
            {"keywords": ["json", "yaml", "baml", "schema", "database", "table", "column", "parse", "how does the web app know", "reaper script", "lua", "automate batch"], "weight": 30},
            {"keywords": ["type safe", "dataclass", "validation", "pydantic", "structured data"], "weight": 25}
        ],
        "dispatch_template": {
            "email_subject": "Stage 3 Unlocked: Type-Safe Prompt Engineering (JSON, YAML & BAML)",
            "headline": "Stage 3 Mastery: Deterministic Rig & Code Automation",
            "body": (
                "Hey Justin!\n\n"
                "You asked how our system automatically parses knob positions and feeds REAPER without breaking. "
                "Welcome to Stage 3: Structured Schemas (JSON, YAML & BAML).\n\n"
                "When you tell an AI 'give me a table', standard LLMs often output conversational filler or malformed text. "
                "BAML (Boundary Abstract Modeling Language) guarantees the AI outputs 100% type-safe JSON or YAML that drops directly "
                "into REAPER Lua scripts or Python audio pipelines.\n\n"
                "We deployed 'scripts/demo_structured_schemas.py' to your repo and unlocked Lab 8 on your portal: "
                "https://justin-netops-hub.web.app/demo_structured_schemas.py"
            ),
            "sms_snippet": "Hey Justin! Stage 3 unlocked: Structured Schemas (JSON/YAML/BAML). Check demo_structured_schemas.py on https://justin-netops-hub.web.app"
        }
    },
    4: {
        "id": 4,
        "name": "TurboQuant Vector Memory & Autonomous AutoResearch",
        "tagline": "Overnight Multi-Model Exploration & Vector Semantic Search",
        "status": "LOCKED",
        "unlock_threshold": 80,
        "curriculum": [
            "TurboQuant: Sub-Millisecond Vector Embeddings for Audio Takes",
            "AutoResearch: Autonomous Overnight Hyperparameter Sweeps",
            "Self-Evaluating Loss Curves & Automated Pruning",
            "Semantic Search Across Hundreds of Multi-Year Audio Sessions"
        ],
        "lab_anchor": "#lab-autoresearch",
        "signal_rules": [
            {"keywords": ["overnight", "run all night", "batch train 20", "compare all models", "vector", "embedding", "search old takes", "autoresearch", "autonomous loop"], "weight": 35}
        ],
        "dispatch_template": {
            "email_subject": "Stage 4 Unlocked: Autonomous AutoResearch & TurboQuant",
            "headline": "Stage 4 Mastery: Autonomous Overnight Systems",
            "body": (
                "Hey Justin!\n\n"
                "You're ready for the bleeding edge: Stage 4 AutoResearch & TurboQuant Vector Memory.\n"
                "Instead of sitting at your PC tweaking dials, your daemon runs 50 hyperparameter tests overnight, "
                "prunes bad loss curves, and delivers the best sounding NAM models by morning."
            ),
            "sms_snippet": "Hey Justin! Stage 4 unlocked: Autonomous AutoResearch & TurboQuant. Check your hub: https://justin-netops-hub.web.app"
        }
    },
    5: {
        "id": 5,
        "name": "Studio Edge Appliance (Gemma 4 E2B/E4B in the Amp Rack)",
        "tagline": "Air-Gapped Real-Time Audio Diagnostics & MIDI/OSC Rack Mount",
        "status": "LOCKED",
        "unlock_threshold": 80,
        "curriculum": [
            "Deploying Ultra-Lightweight Gemma 4 E2B (~1.6GB) on Raspberry Pi 5 / Rack Mini-PC",
            "Real-Time Tube Health & 60Hz Ground Loop Microphonic Detection via Audio Ingest",
            "Emitting Instant MIDI Program Changes (PC) & OSC Routing to REAPER",
            "Zero Cloud Dependency: 100% Air-Gapped Sovereign Hardware Appliance"
        ],
        "lab_anchor": "#lab-edge-appliance",
        "signal_rules": [
            {"keywords": ["pedalboard", "hardware rack", "raspberry pi", "mini pc", "midi", "osc", "tube microphonic", "ground loop", "stand alone", "without my pc"], "weight": 35}
        ],
        "dispatch_template": {
            "email_subject": "Stage 5 Unlocked: Studio Edge Appliance (Gemma 4 in the Amp Rack)",
            "headline": "Stage 5 Mastery: Sovereign Hardware Intelligence",
            "body": (
                "Hey Justin!\n\n"
                "You asked about running intelligence right inside your hardware rack without keeping your primary studio PC on. "
                "Welcome to Stage 5: Studio Edge Appliance.\n\n"
                "Using Google's ultra-efficient Gemma 4 E2B and E4B, we can embed a dedicated AI daemon onto a $60 single-board computer "
                "or rackmount unit that monitors tube microphonics, detects impedance mismatches, and fires MIDI/OSC commands."
            ),
            "sms_snippet": "Hey Justin! Stage 5 unlocked: Studio Edge Appliance (Gemma 4 in your hardware rack). Check your hub: https://justin-netops-hub.web.app"
        }
    },
    6: {
        "id": 6,
        "name": "Spec-Driven DSP Synthesis (Natural Language Amp Design)",
        "tagline": "Generative Filter Curves & Synthetic Sweep Training",
        "status": "LOCKED",
        "unlock_threshold": 85,
        "curriculum": [
            "Prompt-to-DSP: Describing Tone Characteristics ('68 Plexi Sag + Dumble Mid Scoop)",
            "Synthetic Waveform Generation via Python scipy.signal Sweeps",
            "Automated Parametric Transfer Function Estimation",
            "Compiling Impossible Hardware Amps Directly into NAM VST3 Plugins"
        ],
        "lab_anchor": "#lab-spec-dsp",
        "signal_rules": [
            {"keywords": ["amp that doesn't exist", "design an amp", "custom tone from scratch", "synthesize", "transfer function", "dsp filter", "create new plugin"], "weight": 40}
        ],
        "dispatch_template": {
            "email_subject": "Stage 6 Unlocked: Spec-Driven DSP Synthesis",
            "headline": "Stage 6 Mastery: Natural Language Hardware Synthesis",
            "body": (
                "Hey Justin!\n\n"
                "You're stepping into creative alchemy: Stage 6 Spec-Driven DSP Synthesis.\n"
                "Instead of capturing an existing physical box, you can describe the exact harmonic distortion, sag, and EQ curve you want in plain English, "
                "and our pipeline synthesizes the training sweeps and outputs a custom NAM model."
            ),
            "sms_snippet": "Hey Justin! Stage 6 unlocked: Spec-Driven DSP Synthesis (design custom amps from scratch). Check your hub: https://justin-netops-hub.web.app"
        }
    },
    7: {
        "id": 7,
        "name": "Sovereign Multi-Agent Studio Collective",
        "tagline": "Autonomous Swarm Orchestration (@ear, @netops, @scribe)",
        "status": "LOCKED",
        "unlock_threshold": 90,
        "curriculum": [
            "Project Opal A2A Multi-Agent Architecture for Audio Studios",
            "@ear: Autonomous Spectral Evaluator & ESR Quality Gate",
            "@netops: Live Latency, Bufferbloat & Hardware Rig Watcher",
            "@scribe: Karpathy Minimal Wiki Session Logger & Automated Git Commits",
            "Justin as Executive Studio Conductor"
        ],
        "lab_anchor": "#lab-agent-swarm",
        "signal_rules": [
            {"keywords": ["swarm", "multi agent", "doing 5 jobs at once", "assistant for mixing", "automate my whole session", "orchestration"], "weight": 40}
        ],
        "dispatch_template": {
            "email_subject": "Stage 7 Unlocked: Sovereign Multi-Agent Studio Collective",
            "headline": "Stage 7 Mastery: Executive Studio Conductor",
            "body": (
                "Hey Justin!\n\n"
                "You are now the Conductor of your own autonomous studio swarm.\n"
                "Stage 7 unlocks the Multi-Agent Collective: @ear listens to your takes and flags harmonic phase issues, "
                "@netops monitors your network and audio buffer headroom, and @scribe documents every take and commits your wiki."
            ),
            "sms_snippet": "Hey Justin! Stage 7 unlocked: Sovereign Multi-Agent Studio Collective. You are now the Conductor. Check https://justin-netops-hub.web.app"
        }
    }
}


# ==============================================================================
# DURABLE STATE MANAGEMENT
# ==============================================================================

def load_pedagogical_state() -> Dict[str, Any]:
    """Loads pedagogical state from disk, initializing default if not present."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load pedagogical state, resetting default: {e}")

    default_state = {
        "student": "Justin Muir",
        "contact": {
            "phone": "+1 630-418-9227",
            "email": "nightmareglove@gmail.com"
        },
        "current_stage": 1,
        "stages": {
            str(k): {
                "id": v["id"],
                "name": v["name"],
                "status": "ACTIVE" if k == 1 else "LOCKED",
                "readiness_score": 100 if k == 1 else 0,
                "unlocked_at": datetime.now().isoformat() if k == 1 else None,
                "triggers_matched": []
            }
            for k, v in PEDAGOGICAL_STAGES.items()
        },
        "ingested_communications": [],
        "readiness_signals_history": [],
        "last_updated": datetime.now().isoformat()
    }
    save_pedagogical_state(default_state)
    return default_state


def save_pedagogical_state(state: Dict[str, Any]):
    """Saves pedagogical state to disk atomically."""
    state["last_updated"] = datetime.now().isoformat()
    try:
        tmp_file = STATE_FILE + ".tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        os.replace(tmp_file, STATE_FILE)
    except Exception as e:
        logger.error(f"Error saving pedagogical state: {e}")


def load_processed_files() -> Dict[str, Any]:
    """Loads cache of previously ingested transcript files."""
    if os.path.exists(PROCESSED_FILES_LOG):
        try:
            with open(PROCESSED_FILES_LOG, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_processed_files(processed: Dict[str, Any]):
    """Saves cache of ingested files."""
    try:
        with open(PROCESSED_FILES_LOG, "w", encoding="utf-8") as f:
            json.dump(processed, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving processed files: {e}")


# ==============================================================================
# PEDAGOGICAL READINESS EVALUATOR
# ==============================================================================

def evaluate_readiness(text: str, source: str, state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Evaluates communication text against pedagogical stage triggers.
    Accumulates readiness scores and determines if a stage threshold has been crossed.
    """
    lower_text = text.lower()
    matched_events = []
    current_stage = state.get("current_stage", 1)

    # Check candidates for next unlockable stages
    for stage_id, stage_def in PEDAGOGICAL_STAGES.items():
        if stage_id <= current_stage:
            continue  # Already unlocked

        stage_key = str(stage_id)
        stage_state = state["stages"].setdefault(stage_key, {
            "id": stage_id,
            "name": stage_def["name"],
            "status": "LOCKED",
            "readiness_score": 0,
            "triggers_matched": []
        })

        accumulated_delta = 0
        rules = stage_def.get("signal_rules", [])

        for rule in rules:
            for kw in rule["keywords"]:
                if kw in lower_text:
                    score_weight = rule["weight"]
                    accumulated_delta += score_weight

                    signal_entry = {
                        "timestamp": datetime.now().isoformat(),
                        "stage_id": stage_id,
                        "stage_name": stage_def["name"],
                        "keyword": kw,
                        "weight": score_weight,
                        "source": source,
                        "snippet": text[:150]
                    }
                    stage_state["triggers_matched"].append(signal_entry)
                    state["readiness_signals_history"].append(signal_entry)

        if accumulated_delta > 0:
            stage_state["readiness_score"] = min(100, stage_state.get("readiness_score", 0) + accumulated_delta)
            logger.info(
                f"📈 READINESS UPDATE: Stage {stage_id} ({stage_def['name']}) +{accumulated_delta} pts "
                f"-> Total Score: {stage_state['readiness_score']}% (Threshold: {stage_def['unlock_threshold']}%)"
            )

            # Check if threshold crossed!
            if stage_state["readiness_score"] >= stage_def["unlock_threshold"]:
                logger.info(f"🎉 STAGE {stage_id} UNLOCK TRIGGERED! ({stage_def['name']})")
                unlock_event = trigger_stage_unlock(stage_id, state)
                matched_events.append(unlock_event)

    save_pedagogical_state(state)
    return matched_events


def trigger_stage_unlock(stage_id: int, state: Dict[str, Any]) -> Dict[str, Any]:
    """Promotes state to the newly unlocked stage and stages the outbox payloads."""
    stage_def = PEDAGOGICAL_STAGES[stage_id]
    stage_key = str(stage_id)

    state["current_stage"] = stage_id
    state["stages"][stage_key]["status"] = "UNLOCKED"
    state["stages"][stage_key]["unlocked_at"] = datetime.now().isoformat()

    # Create dispatch payload
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    dispatch_file_json = os.path.join(OUTBOX_DIR, f"dispatch_stage_{stage_id}_{timestamp_str}.json")
    dispatch_file_md = os.path.join(OUTBOX_DIR, f"dispatch_stage_{stage_id}_{timestamp_str}.md")

    template = stage_def["dispatch_template"]
    payload = {
        "timestamp": datetime.now().isoformat(),
        "stage_id": stage_id,
        "stage_name": stage_def["name"],
        "student": state["student"],
        "recipient_email": state["contact"]["email"],
        "recipient_phone": state["contact"]["phone"],
        "email_subject": template["email_subject"],
        "headline": template["headline"],
        "email_body": template["body"],
        "sms_body": template.get("sms_snippet", ""),
        "portal_url": f"https://justin-netops-hub.web.app{stage_def['lab_anchor']}"
    }

    # Save to outbox
    with open(dispatch_file_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    with open(dispatch_file_md, "w", encoding="utf-8") as f:
        f.write(f"# Sovereign AI Academy Dispatch — Stage {stage_id} Unlocked\n\n")
        f.write(f"**Recipient**: {payload['student']} ({payload['recipient_email']} / {payload['recipient_phone']})\n")
        f.write(f"**Subject**: {payload['email_subject']}\n")
        f.write(f"**Date**: {payload['timestamp']}\n\n")
        f.write(f"## Email Body\n\n{payload['email_body']}\n\n")
        f.write(f"## SMS / RCS Snippet\n\n`{payload['sms_body']}`\n\n")
        f.write(f"## Portal Link\n\n{payload['portal_url']}\n")

    # Record to pedagogical events log
    with open(EVENTS_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().isoformat()}] UNLOCK: Stage {stage_id} ({stage_def['name']}) -> {dispatch_file_json}\n")

    # Update web/data.json with unlocked stage information for dynamic portal sync
    web_data_file = os.path.join(WEB_DIR, "data.json")
    if os.path.exists(web_data_file):
        try:
            with open(web_data_file, "r", encoding="utf-8") as wf:
                web_data = json.load(wf)
            web_data.setdefault("academy", {})
            web_data["academy"]["current_stage"] = stage_id
            web_data["academy"]["current_stage_name"] = stage_def["name"]
            web_data["academy"]["last_unlocked_at"] = datetime.now().isoformat()
            unlocked = set(web_data["academy"].get("unlocked_stages", [1]))
            unlocked.add(stage_id)
            web_data["academy"]["unlocked_stages"] = sorted(list(unlocked))
            with open(web_data_file, "w", encoding="utf-8") as wf:
                json.dump(web_data, wf, indent=2)
            logger.info(f"🌐 Updated web/data.json: Unlocked Stage {stage_id} ({stage_def['name']})")
        except Exception as e:
            logger.warning(f"Could not update web/data.json: {e}")

    logger.info(f"📦 Staged Outbox Payload: {dispatch_file_json}")
    return payload


# ==============================================================================
# MULTI-CHANNEL INGESTION ADAPTERS (ZERO-ADB)
# ==============================================================================

def parse_transcript_text(content: str) -> List[Dict[str, str]]:
    """
    Parses Google Pixel Gemini Call Notes or Google Meet transcripts into speaker turns.
    Identifies utterances spoken by Justin Muir vs Daniel.
    """
    turns = []
    lines = content.splitlines()
    current_speaker = "Unknown"
    current_buffer = []

    for line in lines:
        line_s = line.strip()
        if not line_s:
            continue

        # Detect speaker headers in transcripts
        # Formats: "The speaker", "You", "Justin Muir", "Justin Muir • Call 2", "Daniel Bass Sherizen:"
        lower_line = line_s.lower()
        if lower_line in ["the speaker", "speaker", "justin muir", "justin"]:
            if current_buffer:
                turns.append({"speaker": current_speaker, "text": " ".join(current_buffer)})
                current_buffer = []
            current_speaker = "Justin Muir"
        elif lower_line in ["you", "daniel", "daniel bass sherizen"]:
            if current_buffer:
                turns.append({"speaker": current_speaker, "text": " ".join(current_buffer)})
                current_buffer = []
            current_speaker = "Daniel Bass Sherizen"
        elif ":" in line_s and len(line_s.split(":")[0]) < 25:
            # e.g. "Justin: I noticed the wav files..."
            prefix, text_part = line_s.split(":", 1)
            prefix_lower = prefix.strip().lower()
            if any(f in prefix_lower for f in JUSTIN_NAME_FRAGMENTS):
                if current_buffer:
                    turns.append({"speaker": current_speaker, "text": " ".join(current_buffer)})
                    current_buffer = []
                current_speaker = "Justin Muir"
                current_buffer.append(text_part.strip())
            elif "daniel" in prefix_lower or "you" in prefix_lower:
                if current_buffer:
                    turns.append({"speaker": current_speaker, "text": " ".join(current_buffer)})
                    current_buffer = []
                current_speaker = "Daniel Bass Sherizen"
                current_buffer.append(text_part.strip())
            else:
                current_buffer.append(line_s)
        else:
            current_buffer.append(line_s)

    if current_buffer:
        turns.append({"speaker": current_speaker, "text": " ".join(current_buffer)})

    return turns


def ingest_transcript_file(file_path: str, state: Dict[str, Any], processed_files: Dict[str, Any]) -> int:
    """Ingests a local transcript file (Pixel Call Note, Meet transcript, or text drop)."""
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return 0

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        file_hash = hashlib.sha256(content.encode()).hexdigest()
        file_mtime = os.path.getmtime(file_path)

        if file_path in processed_files and processed_files[file_path].get("hash") == file_hash:
            logger.debug(f"File already processed with matching hash: {os.path.basename(file_path)}")
            return 0

        logger.info(f"📥 INGESTING TRANSCRIPT: {os.path.basename(file_path)} ({len(content)} bytes)")
        turns = parse_transcript_text(content)
        justin_turns = [t for t in turns if t["speaker"] == "Justin Muir"]

        # Also search whole transcript if speaker labels were sparse
        eval_texts = [t["text"] for t in justin_turns] if justin_turns else [content]

        total_triggers = 0
        for text in eval_texts:
            triggers = evaluate_readiness(text, source=f"file:{os.path.basename(file_path)}", state=state)
            total_triggers += len(triggers)

        processed_files[file_path] = {
            "hash": file_hash,
            "mtime": file_mtime,
            "ingested_at": datetime.now().isoformat(),
            "turns_count": len(turns),
            "justin_turns_count": len(justin_turns)
        }
        save_processed_files(processed_files)

        state.setdefault("ingested_communications", []).append({
            "timestamp": datetime.now().isoformat(),
            "source_type": "transcript_file",
            "file_name": os.path.basename(file_path),
            "justin_utterances": len(justin_turns)
        })
        save_pedagogical_state(state)

        return total_triggers
    except Exception as e:
        logger.error(f"Error ingesting transcript file {file_path}: {e}")
        return 0


def scan_notes_directory(state: Dict[str, Any], processed_files: Dict[str, Any]) -> int:
    """Scans notes/ directory for new or updated transcript files."""
    new_triggers = 0
    candidate_files = []

    for fname in os.listdir(NOTES_DIR):
        if fname.endswith(".txt") or fname.endswith(".md"):
            if "transcript" in fname.lower() or "call" in fname.lower() or "meet" in fname.lower():
                candidate_files.append(os.path.join(NOTES_DIR, fname))

    # Also check notes/incoming if exists
    incoming_dir = os.path.join(NOTES_DIR, "incoming")
    if os.path.exists(incoming_dir):
        for fname in os.listdir(incoming_dir):
            if fname.endswith((".txt", ".md", ".json")):
                candidate_files.append(os.path.join(incoming_dir, fname))

    for fpath in sorted(candidate_files):
        new_triggers += ingest_transcript_file(fpath, state, processed_files)

    return new_triggers


# ==============================================================================
# REST API INGESTION SERVER (PORT 5042)
# ==============================================================================

class CommWatcherHTTPHandler(BaseHTTPRequestHandler):
    """HTTP endpoint to receive incoming communications from webhooks or browser sessions."""
    state_ref: Dict[str, Any] = {}
    processed_files_ref: Dict[str, Any] = {}

    def log_message(self, format, *args):
        # Quiet standard HTTP access logs
        return

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ["/", "/status", "/api/comm/status"]:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            summary = {
                "service": "Sovereign AI Communication Watcher",
                "status": "ONLINE",
                "current_stage": self.state_ref.get("current_stage", 1),
                "active_stage_name": PEDAGOGICAL_STAGES[self.state_ref.get("current_stage", 1)]["name"],
                "stages": self.state_ref.get("stages", {}),
                "ingested_count": len(self.state_ref.get("ingested_communications", [])),
                "signals_detected_count": len(self.state_ref.get("readiness_signals_history", []))
            }
            self.wfile.write(json.dumps(summary, indent=2).encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path in ["/api/comm/ingest", "/ingest"]:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                data = json.loads(body)
            except Exception:
                data = {"text": body, "sender": "Justin Muir", "channel": "raw_post"}

            text = data.get("text", "")
            sender = data.get("sender", "Justin Muir")
            channel = data.get("channel", "http_api")

            if not text:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Empty text"}).encode())
                return

            logger.info(f"📥 INGESTED VIA {channel.upper()}: '{text[:70]}...'")
            triggers = evaluate_readiness(text, source=channel, state=self.state_ref)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "PROCESSED",
                "triggers_fired": len(triggers),
                "current_stage": self.state_ref.get("current_stage", 1),
                "triggers": triggers
            }, indent=2).encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")


def start_http_ingestion_server(port: int, state: Dict[str, Any], processed_files: Dict[str, Any]):
    """Runs the REST ingestion server on a background daemon thread."""
    CommWatcherHTTPHandler.state_ref = state
    CommWatcherHTTPHandler.processed_files_ref = processed_files
    server = HTTPServer(("0.0.0.0", port), CommWatcherHTTPHandler)
    logger.info(f"🌐 Ingestion REST API listening on http://0.0.0.0:{port}/api/comm/ingest")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


# ==============================================================================
# OPPORTUNISTIC ADB ADAPTER (FALLBACK)
# ==============================================================================

def check_adb_connected() -> bool:
    """Checks if an Android device is attached via ADB."""
    if not os.path.exists(ADB_BIN):
        return False
    try:
        res = subprocess.run([ADB_BIN, "get-state"], capture_output=True, text=True, timeout=2)
        return "device" in res.stdout
    except Exception:
        return False


def query_opportunistic_adb_sms(state: Dict[str, Any]) -> int:
    """Queries SMS via ADB if device happens to be connected."""
    if not check_adb_connected():
        return 0

    try:
        cmd = [
            ADB_BIN, "shell",
            "content", "query", "--uri", "content://sms",
            "--projection", "_id:address:body:date:type:read",
            "--sort", "date DESC",
            "--limit", "5"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        if res.returncode != 0:
            return 0

        # Parse messages
        messages = []
        raw_rows = res.stdout.strip().split("\n")
        current_msg = {}
        for row in raw_rows:
            row = row.strip()
            if row.startswith("Row:"):
                if current_msg:
                    messages.append(current_msg)
                current_msg = {}
            for part in row.split(", "):
                if "=" in part:
                    k, v = part.split("=", 1)
                    k = k.strip().replace("Row: ", "")
                    current_msg[k] = v.strip()
        if current_msg:
            messages.append(current_msg)

        new_triggers = 0
        last_id = state.get("last_processed_sms_id", 0)

        for m in messages:
            addr = m.get("address", "")
            if any(f in addr for f in JUSTIN_PHONE_FRAGMENTS):
                msg_id = int(m.get("_id", 0))
                msg_type = int(m.get("type", 1))
                body = m.get("body", "")

                if msg_id > last_id and msg_type == 1 and body:
                    logger.info(f"📱 Ingested SMS via ADB (ID {msg_id}): '{body}'")
                    triggers = evaluate_readiness(body, source="adb:sms", state=state)
                    new_triggers += len(triggers)
                    if msg_id > state.get("last_processed_sms_id", 0):
                        state["last_processed_sms_id"] = msg_id

        return new_triggers
    except Exception as e:
        logger.debug(f"ADB check skipped: {e}")
        return 0


# ==============================================================================
# STATUS DASHBOARD & CLI REPORTING
# ==============================================================================

def print_status_dashboard(state: Dict[str, Any]):
    """Renders a comprehensive terminal dashboard of the pedagogical state."""
    current_stage_id = state.get("current_stage", 1)
    current_stage = PEDAGOGICAL_STAGES[current_stage_id]
    adb_online = check_adb_connected()

    print("=" * 80)
    print(" 📡 SOVEREIGN AI ACADEMY: MULTI-CHANNEL PEDAGOGICAL WATCHER")
    print("=" * 80)
    print(f"• Student:                  {state.get('student')} ({state['contact']['phone']} / {state['contact']['email']})")
    print(f"• Active Learning Stage:    Stage {current_stage_id}: {current_stage['name']}")
    print(f"• Active Tagline:           {current_stage['tagline']}")
    print(f"• Opportunistic ADB:        {'🟢 Connected' if adb_online else '⚪ Offline (Zero-ADB Mode Active)'}")
    print(f"• Ingested Comms:           {len(state.get('ingested_communications', []))} sessions/transcripts")
    print(f"• Signals Detected:         {len(state.get('readiness_signals_history', []))} pedagogical triggers")
    print("-" * 80)
    print("STAGE READINESS PROGRESSION MATRIX:")
    for s_id, s_def in PEDAGOGICAL_STAGES.items():
        s_data = state["stages"].get(str(s_id), {})
        status = s_data.get("status", "LOCKED")
        score = s_data.get("readiness_score", 0)
        threshold = s_def["unlock_threshold"]

        badge = "🟢 ACTIVE" if status in ["ACTIVE", "UNLOCKED"] else f"⚪ LOCKED ({score}% / {threshold}%)"
        print(f"  Stage {s_id}: {s_def['name']:<38} | {badge}")

    print("-" * 80)
    signals = state.get("readiness_signals_history", [])[-3:]
    if signals:
        print("RECENT PEDAGOGICAL SIGNALS DETECTED:")
        for sig in signals:
            print(f"  • [{sig['timestamp']}] Matched '{sig['keyword']}' (+{sig['weight']} pts) for Stage {sig['stage_id']}")
            print(f"    Source: {sig['source']}")
            print(f"    Excerpt: \"{sig['snippet']}...\"")
    else:
        print("No signals detected yet. Ingest transcripts or messages to evaluate.")

    outbox_files = os.listdir(OUTBOX_DIR) if os.path.exists(OUTBOX_DIR) else []
    dispatches = [f for f in outbox_files if f.endswith(".json")]
    print("-" * 80)
    print(f"STAGED OUTBOX DISPATCHES ({len(dispatches)} ready):")
    for d in dispatches[-3:]:
        print(f"  • notes/outbox/{d}")
    print("=" * 80)


# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(description="Multi-Channel Communication Watcher & Pedagogical State Machine")
    parser.add_argument("--status", action="store_true", help="Display pedagogical state dashboard")
    parser.add_argument("--daemon", action="store_true", help="Run continuous background watcher daemon")
    parser.add_argument("--port", type=int, default=5042, help="HTTP REST ingestion port (default: 5042)")
    parser.add_argument("--interval", type=int, default=10, help="Directory polling interval in seconds (default: 10)")
    parser.add_argument("--ingest-file", type=str, help="Ingest a specific transcript or note file")
    parser.add_argument("--ingest-text", type=str, help="Ingest a raw text message from Justin")
    parser.add_argument("--simulate-trigger", type=int, choices=[2, 3, 4], help="Simulate unlocking a specific stage")
    args = parser.parse_args()

    state = load_pedagogical_state()
    processed_files = load_processed_files()

    if args.simulate_trigger:
        logger.info(f"🧪 SIMULATING STAGE {args.simulate_trigger} UNLOCK TRIGGER...")
        payload = trigger_stage_unlock(args.simulate_trigger, state)
        save_pedagogical_state(state)
        print("\n✅ Simulation Complete. Generated Outbox Payload:")
        print(json.dumps(payload, indent=2))
        return

    if args.ingest_file:
        triggers = ingest_transcript_file(args.ingest_file, state, processed_files)
        logger.info(f"Ingestion complete for {args.ingest_file}. New unlocks triggered: {triggers}")
        return

    if args.ingest_text:
        triggers = evaluate_readiness(args.ingest_text, source="cli:manual", state=state)
        logger.info(f"Ingestion complete for text. New unlocks triggered: {len(triggers)}")
        return

    if args.status:
        # Also do a quick scan of notes directory before printing status
        scan_notes_directory(state, processed_files)
        print_status_dashboard(state)
        return

    if args.daemon:
        logger.info("🚀 Starting Multi-Channel Pedagogical Watcher Daemon...")
        logger.info(f"Decoupled from physical ADB. Ingesting from notes/, REST API (port {args.port}), and opportunistic ADB.")

        # Start REST server
        start_http_ingestion_server(args.port, state, processed_files)

        try:
            while True:
                # 1. Scan notes/ directory for newly dropped call transcripts or Gemini notes
                scan_notes_directory(state, processed_files)

                # 2. Opportunistic ADB check if phone happens to be attached
                query_opportunistic_adb_sms(state)

                time.sleep(args.interval)
        except KeyboardInterrupt:
            logger.info("Watcher daemon stopped cleanly by user.")
    else:
        scan_notes_directory(state, processed_files)
        print_status_dashboard(state)


if __name__ == "__main__":
    main()
