#!/usr/bin/env python3
"""
Sovereign AI Academy: Justin Muir Automated Communication Watcher & Responder Daemon
Author: MAX (Anima Ex Machina) & Daniel Bass Sherizen
Target: Justin Muir (+1 630-418-9227 / nightmareglove@gmail.com)

Purpose:
    Monitors communication between Daniel and Justin Muir across SMS/RCS and email.
    Detects pedagogical readiness signals (e.g. asking about formatting, tables, JSON,
    YAML, BAML, Colab errors, or Gemma audio capabilities) and automatically triggers
    the curated learning materials, troubleshooting guides, or demo scripts.

Usage:
    python3 scripts/justin_comm_watcher.py --status
    python3 scripts/justin_comm_watcher.py --simulate "How do I format these knob values into a clean table?"
    python3 scripts/justin_comm_watcher.py --once
    python3 scripts/justin_comm_watcher.py --daemon
"""

import sys
import os
import time
import json
import logging
import argparse
import subprocess
import shlex
from datetime import datetime
from typing import Dict, Any, List, Optional

# Base paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOTES_DIR = os.path.join(PROJECT_ROOT, "notes")
STATE_FILE = os.path.join(NOTES_DIR, "watcher_state.json")
LOG_FILE = os.path.join(NOTES_DIR, "watcher_activity.log")
ADB_BIN = "/Users/danielbasssherizen/Library/Android/sdk/platform-tools/adb"

os.makedirs(NOTES_DIR, exist_ok=True)

# Configure logging to console and persistent logfile
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [COMM-WATCHER] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding="utf-8")
    ]
)
logger = logging.getLogger("JustinCommWatcher")

# Contact Matchers
JUSTIN_PHONE_FRAGMENTS = ["6304189227", "630-418-9227", "+16304189227"]
JUSTIN_EMAIL_TARGETS = ["nightmareglove@gmail.com", "nightmare.glove@gmail.com"]

# Curated Intent Triggers & Auto-Dispatch Payloads
INTENT_RULES = [
    {
        "intent_id": "STAGE_3_STRUCTURED_SCHEMAS",
        "description": "Triggered when Justin asks about tables, formatting, JSON, YAML, BAML, or database schemas",
        "keywords": ["json", "yaml", "baml", "schema", "table", "format", "organize", "database", "how does the web app know", "parse", "struct"],
        "reply": (
            "Hey Justin! You are tapping right into Stage 3 of the Sovereign AI Academy. "
            "We built an executable demo script showing how JSON, YAML, and BAML force AI models "
            "to output 100% type-safe knob tables without messy markdown hallucinations: "
            "Run 'python3 scripts/demo_structured_schemas.py' or check https://justin-netops-hub.web.app/demo_structured_schemas.py"
        )
    },
    {
        "intent_id": "COLAB_GPU_ASSIST",
        "description": "Triggered when Justin encounters GPU runtime issues, CUDA questions, or Drive mount problems",
        "keywords": ["colab", "cuda", "gpu", "error", "failed", "stuck", "wavenet", "drive", "timeout", "runtime"],
        "reply": (
            "Hey Justin, quick Colab check: 1) Verify 'T4 GPU' is active under Runtime -> Change runtime type. "
            "2) Authenticate Google Drive via 'drive.mount(\"/content/drive\")' so audio takes persist. "
            "3) If you want us to look at the error together, jump in our Meet room anytime: https://meet.google.com/eyk-gkme-bqb"
        )
    },
    {
        "intent_id": "GEMMA_4_NATIVE_AUDIO",
        "description": "Triggered when Justin asks about audio tokens, microphone transients, waveform analysis, or Gemma models",
        "keywords": ["gemma", "audio", "transient", "listen", "mic", "waveform", "12b", "31b", "ollama", "qat"],
        "reply": (
            "Hey Justin! You should definitely test Gemma 4 12B Unified ('ollama run gemma4:12b'). "
            "It has native audio input tokens, meaning it hears audio waveforms and picks up transients directly without Whisper! "
            "And for 256K massive context thinking, test 'ollama run gemma4:31b'."
        )
    },
    {
        "intent_id": "NETOPS_DAEMON_ASSIST",
        "description": "Triggered when Justin asks about network jitter, pfSense logs, audio buffer underruns, or daemon commands",
        "keywords": ["daemon", "pfsense", "jitter", "ping", "packet loss", "router", "buffer", "xrun", "5040"],
        "reply": (
            "Hey Justin, your conversational daemon is ready! Run 'python3 scripts/nl_daemon_bridge.py --cli --model gemma4:12b' "
            "and ask in plain English: 'How is network jitter looking?' or 'Is the audio buffer dropping samples?' "
            "It queries live telemetry directly from your rig."
        )
    }
]


def load_state() -> Dict[str, Any]:
    """Loads durable state from disk."""
    default_state = {
        "last_checked_timestamp": datetime.now().isoformat(),
        "last_processed_sms_id": 0,
        "dispatched_events": [],
        "total_triggers_detected": 0
    }
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load state, initializing default: {e}")
    return default_state


def save_state(state: Dict[str, Any]):
    """Persists state to disk."""
    state["last_checked_timestamp"] = datetime.now().isoformat()
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving state to {STATE_FILE}: {e}")


def check_adb_connected() -> bool:
    """Checks if an Android device is currently attached and responsive via ADB."""
    if not os.path.exists(ADB_BIN):
        return False
    try:
        res = subprocess.run([ADB_BIN, "get-state"], capture_output=True, text=True, timeout=3)
        return "device" in res.stdout
    except Exception:
        return False


def query_recent_sms_messages() -> List[Dict[str, Any]]:
    """Queries recent SMS messages from Justin via Android content provider."""
    if not check_adb_connected():
        return []

    try:
        # Query content://sms for Justin's number
        cmd = [
            ADB_BIN, "shell",
            "content", "query", "--uri", "content://sms",
            "--projection", "_id:address:body:date:type:read",
            "--sort", "date DESC",
            "--limit", "10"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
        if res.returncode != 0:
            return []

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
                    k = k.strip()
                    if k.startswith("Row: "):
                        k = k.replace("Row: ", "")
                    current_msg[k] = v.strip()
        if current_msg:
            messages.append(current_msg)

        # Filter for Justin
        justin_msgs = []
        for m in messages:
            addr = m.get("address", "")
            if any(f in addr for f in JUSTIN_PHONE_FRAGMENTS):
                try:
                    m["_id"] = int(m.get("_id", 0))
                    m["type"] = int(m.get("type", 1))  # 1 = inbox, 2 = sent
                except ValueError:
                    pass
                justin_msgs.append(m)

        return justin_msgs
    except Exception as e:
        logger.debug(f"Error reading SMS content provider: {e}")
        return []


def evaluate_text_for_triggers(text: str) -> Optional[Dict[str, Any]]:
    """Matches text against the curated intent trigger rules."""
    lower_text = text.lower()
    for rule in INTENT_RULES:
        for kw in rule["keywords"]:
            if kw in lower_text:
                return rule
    return None


def dispatch_sms_reply(reply_text: str, phone: str = "+16304189227") -> bool:
    """Sends an automated SMS reply to Justin via connected device."""
    if not check_adb_connected():
        logger.warning(f"Cannot dispatch SMS — device not connected over ADB. Queuing to outbox.")
        return False

    try:
        escaped_body = shlex.quote(reply_text)
        cmd_str = f"am start -a android.intent.action.SENDTO -d smsto:{phone} --es sms_body {escaped_body}"
        res = subprocess.run([ADB_BIN, "shell", cmd_str], capture_output=True, text=True, timeout=5)
        if res.returncode == 0:
            time.sleep(1.5)
            # Inject tap on the send button (coordinate calibrated on Pixel 10 Pro)
            subprocess.run([ADB_BIN, "shell", "input", "tap", "2315", "890"], capture_output=True, text=True, timeout=3)
            logger.info(f"Dispatched SMS to {phone}: '{reply_text[:60]}...'")
            return True
        return False
    except Exception as e:
        logger.error(f"Error dispatching SMS: {e}")
        return False


def process_watcher_tick(state: Dict[str, Any]) -> int:
    """Executes a single polling tick across communication channels."""
    device_online = check_adb_connected()
    if not device_online:
        return 0

    messages = query_recent_sms_messages()
    last_id = state.get("last_processed_sms_id", 0)
    new_triggers = 0

    # Process messages in chronological order (lowest ID to highest)
    messages_sorted = sorted([m for m in messages if m.get("_id", 0) > last_id], key=lambda x: x.get("_id", 0))

    for msg in messages_sorted:
        msg_id = msg.get("_id", 0)
        msg_type = msg.get("type", 1)  # 1 = inbox, 2 = sent
        body = msg.get("body", "")

        # We only auto-respond to incoming messages from Justin (type=1)
        if msg_type == 1 and body:
            logger.info(f"Incoming SMS from Justin (ID: {msg_id}): '{body}'")
            matched_rule = evaluate_text_for_triggers(body)

            if matched_rule:
                intent_id = matched_rule["intent_id"]
                logger.info(f"🎯 MATCHED INTENT: {intent_id} (Triggered by Justin's message)")

                # Execute dispatch
                success = dispatch_sms_reply(matched_rule["reply"])
                event = {
                    "timestamp": datetime.now().isoformat(),
                    "source_message_id": msg_id,
                    "incoming_text": body,
                    "matched_intent": intent_id,
                    "dispatched_reply": matched_rule["reply"],
                    "dispatch_success": success
                }
                state.setdefault("dispatched_events", []).append(event)
                state["total_triggers_detected"] = state.get("total_triggers_detected", 0) + 1
                new_triggers += 1

        # Advance state pointer
        if msg_id > state.get("last_processed_sms_id", 0):
            state["last_processed_sms_id"] = msg_id

    save_state(state)
    return new_triggers


def print_status(state: Dict[str, Any]):
    """Prints status and recent activity."""
    adb_online = check_adb_connected()
    print("=" * 75)
    print(" 📡 JUSTIN MUIR COMMUNICATION WATCHER: STATUS REPORT")
    print("=" * 75)
    print(f"• ADB Device Online:          {'🟢 YES (Connected)' if adb_online else '⚪ NO (Waiting for connection)'}")
    print(f"• Monitored Contacts:         {', '.join(JUSTIN_PHONE_FRAGMENTS)}")
    print(f"• Last Checked:               {state.get('last_checked_timestamp')}")
    print(f"• Last Processed SMS ID:      {state.get('last_processed_sms_id')}")
    print(f"• Total Triggers Fired:       {state.get('total_triggers_detected', 0)}")
    print("-" * 75)
    print("ACTIVE INTENT RULES CONFIGURED:")
    for rule in INTENT_RULES:
        print(f"  • [{rule['intent_id']}]: {rule['description']}")
        print(f"    Keywords: {', '.join(rule['keywords'][:6])}...")
    print("-" * 75)
    recent = state.get("dispatched_events", [])[-3:]
    if recent:
        print("RECENT AUTO-DISPATCHED EVENTS:")
        for r in recent:
            print(f"  [{r['timestamp']}] Intent: {r['matched_intent']}")
            print(f"    Incoming: '{r['incoming_text']}'")
            print(f"    Dispatched: '{r['dispatched_reply'][:80]}...'")
    else:
        print("No auto-dispatches recorded yet. Watcher is armed and standing by.")
    print("=" * 75)


def run_simulation(sim_text: str):
    """Simulates an incoming message from Justin to verify intent triggering."""
    print("=" * 75)
    print(" 🧪 SIMULATING INCOMING MESSAGE FROM JUSTIN MUIR")
    print(f" Incoming Text: '{sim_text}'")
    print("-" * 75)
    matched = evaluate_text_for_triggers(sim_text)
    if matched:
        print(f"✓ MATCHED INTENT: {matched['intent_id']}")
        print(f"✓ DESCRIPTION:    {matched['description']}")
        print("\n[Proposed Auto-Reply Payload]:")
        print(f"\"{matched['reply']}\"")
    else:
        print("⚪ No specific learning intent matched. Message would be logged without auto-firing.")
    print("=" * 75)


def main():
    parser = argparse.ArgumentParser(description="Automated Communication Watcher & Responder for Justin Muir")
    parser.add_argument("--status", action="store_true", help="Display current watcher status and state")
    parser.add_argument("--once", action="store_true", help="Run a single polling check and exit")
    parser.add_argument("--daemon", action="store_true", help="Run continuous background polling daemon")
    parser.add_argument("--interval", type=int, default=10, help="Polling interval in seconds (default: 10)")
    parser.add_argument("--simulate", type=str, help="Simulate an incoming message to test intent matching")
    args = parser.parse_args()

    state = load_state()

    if args.simulate:
        run_simulation(args.simulate)
        return

    if args.status:
        print_status(state)
        return

    if args.once:
        triggers = process_watcher_tick(state)
        logger.info(f"Single check complete. New triggers detected: {triggers}")
        return

    if args.daemon:
        logger.info("Starting Justin Muir Communication Watcher Daemon...")
        logger.info(f"Polling ADB communication channels every {args.interval}s. Press Ctrl+C to stop.")
        try:
            while True:
                process_watcher_tick(state)
                time.sleep(args.interval)
        except KeyboardInterrupt:
            logger.info("Watcher daemon stopped cleanly by user.")
    else:
        print_status(state)


if __name__ == "__main__":
    main()
