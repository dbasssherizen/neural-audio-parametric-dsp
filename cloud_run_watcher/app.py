#!/usr/bin/env python3
"""
Sovereign AI Academy: Autonomous Cloud Run Communication Watcher & Pedagogical State Machine
Author: MAX (Anima Ex Machina) & Daniel Bass Sherizen
Target: Justin Muir (+1 630-418-9227 / nightmareglove@gmail.com)
Project: anima-sovereign-ai (Google Cloud Run / Firestore)
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from flask import Flask, request, jsonify

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [CLOUD-WATCHER] %(message)s"
)
logger = logging.getLogger("CloudRunWatcher")

app = Flask(__name__)

# Try to initialize Google Cloud Firestore
FIRESTORE_AVAILABLE = False
db = None
try:
    from google.cloud import firestore
    project_id = os.environ.get("GCP_PROJECT", os.environ.get("GOOGLE_CLOUD_PROJECT", "anima-sovereign-ai"))
    db = firestore.Client(project=project_id)
    FIRESTORE_AVAILABLE = True
    logger.info(f"Connected to Google Cloud Firestore in project: {project_id}")
except Exception as e:
    logger.warning(f"Firestore initialization notice (falling back to memory): {e}")

# Target Contact Matching
JUSTIN_PHONE_FRAGMENTS = ["6304189227", "630-418-9227", "+16304189227"]
JUSTIN_NAME_FRAGMENTS = ["justin", "justin muir", "the speaker"]
JUSTIN_EMAIL_TARGETS = ["nightmareglove@gmail.com", "nightmare.glove@gmail.com"]

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
            "Gemma 4 12B Unified with Native Audio Tokens",
            "Gemma 4 31B Dense Flagship with 256K Context",
            "Conversational NetOps Daemon (nl_daemon_bridge.py)"
        ],
        "lab_anchor": "#lab-colab"
    },
    2: {
        "id": 2,
        "name": "Markdown & The Karpathy Minimal Wiki",
        "tagline": "Frictionless Text Formatting & Agent Second Brains",
        "status": "UNLOCKED",
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
        ]
    },
    3: {
        "id": 3,
        "name": "Structured Schemas (JSON, YAML, BAML)",
        "tagline": "Type-Safe Rig Automation & Deterministic LLM Outputs",
        "status": "UNLOCKED",
        "unlock_threshold": 75,
        "curriculum": [
            "JSON for Web Dashboards & Neural Sweep Manifests",
            "YAML for Clean Hardware Re-Amp Matrices & Configuration",
            "BAML: Boundary Abstract Modeling Language for 100% Type-Safe LLM Outputs",
            "Eliminating Schema Drift in Continuous Potentiometer Conditioning",
            "Compiling Strict Rust Deserializers for Streaming REAPER Enums"
        ],
        "lab_anchor": "#lab-structured-schemas",
        "signal_rules": [
            {"keywords": ["baml", "schema", "json", "yaml", "type safe", "parser", "syntax", "crash", "missing bracket", "format output"], "weight": 30},
            {"keywords": ["potentiometer table", "parameter csv", "automated sweep settings", "table"], "weight": 30}
        ]
    },
    4: {
        "id": 4,
        "name": "TurboQuant Vector Memory & Autonomous AutoResearch",
        "tagline": "Long-Term Knowledge Retrieval & Automated Architecture Search",
        "status": "LOCKED",
        "unlock_threshold": 70,
        "curriculum": [
            "Vector Embeddings for Audio Timbre & Frequency Representations",
            "TurboQuant Polar Quantization: Zero-Loss Memory Compression",
            "Self-Directed Hypothesizing & Overnight Neural Sweep Discovery",
            "Automated Hyperparameter Tuning on Proxmox RTX 4090",
            "Continuous Retrieval-Augmented Generation for Audio Engineering"
        ],
        "lab_anchor": "#lab-turboquant",
        "signal_rules": [
            {"keywords": ["vector", "embedding", "retrieval", "rag", "search my past sessions", "how does it remember", "semantic search"], "weight": 35},
            {"keywords": ["overnight", "while i sleep", "let it run", "auto tune", "find best settings automatically"], "weight": 35}
        ]
    },
    5: {
        "id": 5,
        "name": "Studio Edge Appliance (Gemma 4 E2B/E4B in the Amp Rack)",
        "tagline": "Physical Airgapped Rack Hardware with Sub-5ms Local Inference",
        "status": "LOCKED",
        "unlock_threshold": 70,
        "curriculum": [
            "Deploying Quantized Gemma 4 E2B/E4B on Local Intel/Linux NUC",
            "Zero-Egress Studio Airgapping: 0.0 Egress Invariant",
            "Low-Latency Physical Dial Feedback (<5ms Interaction Ceiling)",
            "Direct MIDI / OSC Ingestion into Local Model Context",
            "Physical Tube Amp Health Telemetry & Cathode Current Sensing"
        ],
        "lab_anchor": "#lab-edge-appliance",
        "signal_rules": [
            {"keywords": ["hardware", "rackmount", "edge", "offline", "without internet", "private", "no cloud", "airgap"], "weight": 35},
            {"keywords": ["midi", "osc", "footswitch", "expression pedal", "knob readout", "bias meter"], "weight": 35}
        ]
    },
    6: {
        "id": 6,
        "name": "Spec-Driven DSP Synthesis (Natural Language Amp Design)",
        "tagline": "From English Prompts to Causal WaveNet Audio Kernels",
        "status": "LOCKED",
        "unlock_threshold": 75,
        "curriculum": [
            "Writing High-Level DSP Specs: Natural Language to WaveNet Graph",
            "Automatic Layer Topology Synthesis via LLM Transpiler",
            "Validating Causal Dilated Convolution Schedules Before Training",
            "Continuous Neural Potentiometer Morphing (CatMLP Fusion)",
            "Exporting Directly to NAM (.nam) and AIDA DSP Formats"
        ],
        "lab_anchor": "#lab-spec-dsp",
        "signal_rules": [
            {"keywords": ["design an amp", "custom circuit", "blend marshall and fender", "make a tone that", "new architecture"], "weight": 40},
            {"keywords": ["export to nam", "aida dsp", "play live on quad cortex", "hardware pedal export"], "weight": 35}
        ]
    },
    7: {
        "id": 7,
        "name": "Sovereign Multi-Agent Studio Collective",
        "tagline": "Multi-Agent Pair Programming & Autonomous Audio Pipeline Swarms",
        "status": "LOCKED",
        "unlock_threshold": 80,
        "curriculum": [
            "Conductor-Worker Architecture for Studio Engineering Tasks",
            "Decoupling Tone Design, Re-Amp Execution, and Verification",
            "A2A (Agent-to-Agent) Handoff Protocols in REAPER Workflows",
            "Self-Healing Re-Amp Pipelines with Automated Gain Staging Recovery",
            "Autonomous Studio Engineering at Sovereign Scale"
        ],
        "lab_anchor": "#lab-collective",
        "signal_rules": [
            {"keywords": ["swarm", "multi agent", "team of agents", "delegation", "let agents talk to each other"], "weight": 40},
            {"keywords": ["automatic recovery", "pipeline crashed", "self healing", "verify without me"], "weight": 40}
        ]
    }
}

# Initial in-memory state
current_state = {
    "student": "Justin Muir",
    "contact": {
        "phone": "+1 630-418-9227",
        "email": "nightmareglove@gmail.com"
    },
    "current_stage": 3,
    "stages": {
        "1": {"id": 1, "name": "Tactical Foundations", "status": "ACTIVE", "readiness_score": 100, "unlocked_at": "2026-10-06T22:33:55"},
        "2": {"id": 2, "name": "Markdown & The Karpathy Minimal Wiki", "status": "UNLOCKED", "readiness_score": 75, "unlocked_at": "2026-10-07T09:10:16"},
        "3": {"id": 3, "name": "Structured Schemas (JSON, YAML, BAML)", "status": "UNLOCKED", "readiness_score": 90, "unlocked_at": "2026-10-07T09:10:16"},
        "4": {"id": 4, "name": "TurboQuant Vector Memory & Autonomous AutoResearch", "status": "LOCKED", "readiness_score": 35, "unlocked_at": None},
        "5": {"id": 5, "name": "Studio Edge Appliance (Gemma 4 E2B/E4B in the Amp Rack)", "status": "LOCKED", "readiness_score": 70, "unlocked_at": None},
        "6": {"id": 6, "name": "Spec-Driven DSP Synthesis (Natural Language Amp Design)", "status": "LOCKED", "readiness_score": 0, "unlocked_at": None},
        "7": {"id": 7, "name": "Sovereign Multi-Agent Studio Collective", "status": "LOCKED", "readiness_score": 0, "unlocked_at": None}
    },
    "ingested_communications": [],
    "readiness_signals_history": [],
    "last_updated": datetime.now().isoformat()
}

def load_state_from_firestore():
    global current_state
    if not FIRESTORE_AVAILABLE or not db:
        return
    try:
        doc_ref = db.collection("pedagogical_state").document("justin_muir")
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            current_state.update(data)
            logger.info("Loaded state successfully from Cloud Firestore.")
        else:
            # Seed initial state
            doc_ref.set(current_state)
            logger.info("Initialized Cloud Firestore with initial pedagogical state.")
    except Exception as e:
        logger.error(f"Error accessing Cloud Firestore: {e}")

def save_state_to_firestore():
    if not FIRESTORE_AVAILABLE or not db:
        return
    try:
        current_state["last_updated"] = datetime.now().isoformat()
        doc_ref = db.collection("pedagogical_state").document("justin_muir")
        doc_ref.set(current_state, merge=True)
        logger.info("Persisted updated pedagogical state to Cloud Firestore.")
    except Exception as e:
        logger.error(f"Error saving to Cloud Firestore: {e}")

# Load initial state
load_state_from_firestore()

def evaluate_signals_in_text(text: str, source_label: str = "text") -> List[Dict[str, Any]]:
    matched_signals = []
    text_lower = text.lower()

    for stage_id in range(2, 8):
        stage_cfg = PEDAGOGICAL_STAGES.get(stage_id)
        if not stage_cfg:
            continue
        signal_rules = stage_cfg.get("signal_rules", [])

        for rule in signal_rules:
            keywords = rule.get("keywords", [])
            weight = rule.get("weight", 20)

            for kw in keywords:
                if kw in text_lower:
                    signal = {
                        "timestamp": datetime.now().isoformat(),
                        "stage_id": stage_id,
                        "stage_name": stage_cfg["name"],
                        "keyword": kw,
                        "weight": weight,
                        "source": source_label,
                        "snippet": text[:140]
                    }
                    matched_signals.append(signal)
                    
                    # Update stage score
                    s_str = str(stage_id)
                    stage_entry = current_state["stages"].get(s_str, {
                        "id": stage_id,
                        "name": stage_cfg["name"],
                        "status": "LOCKED",
                        "readiness_score": 0,
                        "unlocked_at": None,
                        "triggers_matched": []
                    })
                    
                    stage_entry["readiness_score"] = min(100, stage_entry["readiness_score"] + weight)
                    if "triggers_matched" not in stage_entry:
                        stage_entry["triggers_matched"] = []
                    stage_entry["triggers_matched"].append(signal)

                    # Check unlock
                    if stage_entry["readiness_score"] >= stage_cfg["unlock_threshold"] and stage_entry["status"] == "LOCKED":
                        stage_entry["status"] = "UNLOCKED"
                        stage_entry["unlocked_at"] = datetime.now().isoformat()
                        if stage_id > current_state.get("current_stage", 1):
                            current_state["current_stage"] = stage_id
                        logger.info(f"🎉 UNLOCKED STAGE {stage_id}: {stage_cfg['name']}!")

                    current_state["stages"][s_str] = stage_entry
                    break

    if matched_signals:
        current_state["readiness_signals_history"].extend(matched_signals)
        save_state_to_firestore()

    return matched_signals

@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "service": "justin-comm-watcher",
        "description": "Sovereign AI Academy Multi-Channel Communication Watcher & Pedagogical State Machine",
        "target": "Justin Muir (+1 630-418-9227)",
        "current_stage": current_state.get("current_stage", 3),
        "firestore_connected": FIRESTORE_AVAILABLE,
        "status": "HEALTHY",
        "timestamp": datetime.now().isoformat()
    })

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "OK", "timestamp": datetime.now().isoformat()}), 200

@app.route("/status", methods=["GET"])
def get_status():
    return jsonify({
        "success": True,
        "state": current_state
    })

@app.route("/ingest", methods=["POST"])
def ingest_communication():
    """
    Webhook endpoint to ingest messages, transcripts, SMS, or RCS from Justin Muir.
    Payload: { "text": "...", "source": "wireless_adb" | "rcs" | "meet", "author": "..." }
    """
    payload = request.get_json(silent=True) or {}
    text = payload.get("text", "").strip()
    source = payload.get("source", "webhook")
    author = payload.get("author", "Justin Muir")

    if not text:
        return jsonify({"error": "Missing 'text' parameter in JSON payload"}), 400

    logger.info(f"Ingesting message from [{author}] via [{source}]: {text[:80]}...")
    
    # Record communication
    comm_record = {
        "timestamp": datetime.now().isoformat(),
        "source": source,
        "author": author,
        "length": len(text),
        "preview": text[:120]
    }
    current_state["ingested_communications"].append(comm_record)

    # Evaluate pedagogical signals
    signals = evaluate_signals_in_text(text, source_label=f"{source}:{author}")

    return jsonify({
        "success": True,
        "message": "Communication ingested successfully",
        "signals_matched": len(signals),
        "current_stage": current_state.get("current_stage", 3),
        "timestamp": datetime.now().isoformat()
    })

@app.route("/cron", methods=["POST", "GET"])
def run_cron_cycle():
    """
    Invoked every 10 minutes by Cloud Scheduler.
    Checks pending queues, refreshes telemetry, and ensures state persistence.
    """
    logger.info("Executing Cloud Scheduler heartbeat cycle...")
    current_state["last_heartbeat"] = datetime.now().isoformat()
    save_state_to_firestore()

    return jsonify({
        "success": True,
        "action": "heartbeat_completed",
        "current_stage": current_state.get("current_stage", 3),
        "total_communications": len(current_state.get("ingested_communications", [])),
        "timestamp": datetime.now().isoformat()
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
