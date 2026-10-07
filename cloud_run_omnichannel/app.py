#!/usr/bin/env python3
"""
Sovereign AI: Omnichannel Telegram Voice Gateway & Triage Synchronizer
Author: MAX (Anima Ex Machina) & Daniel Bass Sherizen
Project: anima-sovereign-ai (Google Cloud Run / Firestore)

Features:
1. 24/7 Telegram Webhook Receiver (@AnimaMaxBot)
2. Gemini Multimodal Audio Transcription & ADHD Micro-Step Decomposition
3. Interactive Slash Commands: /sprint, /triage, /capture, /outbox, /status
4. Cloud Firestore Stream & Tuesday Outbox Synchronization
5. Scale-to-Zero Cloud Run Deployment (0-3 instances, 512MiB RAM)
"""

import os
import sys
import json
import time
import base64
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from flask import Flask, request, jsonify
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [OMNICHANNEL-GATEWAY] %(message)s"
)
logger = logging.getLogger("OmnichannelGateway")

app = Flask(__name__)

# Environment Configuration
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", os.environ.get("GOOGLE_API_KEY", ""))
PROJECT_ID = os.environ.get("GCP_PROJECT", os.environ.get("GOOGLE_CLOUD_PROJECT", "anima-sovereign-ai"))
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")

# Initialize Firestore
FIRESTORE_CONNECTED = False
db = None
try:
    from google.cloud import firestore
    db = firestore.Client(project=PROJECT_ID)
    FIRESTORE_CONNECTED = True
    logger.info(f"Connected to Google Cloud Firestore in project: {PROJECT_ID}")
except Exception as e:
    logger.warning(f"Firestore initialization notice (operating in in-memory fallback): {e}")

# In-memory fallbacks if Firestore is unreachable
_MEMORY_STREAM = []
_MEMORY_OUTBOX = []


# ==============================================================================
# TELEGRAM BOT CLIENT HELPERS
# ==============================================================================

def send_telegram_message(chat_id: int, text: str, parse_mode: str = "Markdown", reply_markup: Optional[Dict] = None) -> bool:
    """Sends a message back to the user via Telegram Bot API."""
    if not TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN not configured; skipping Telegram reply")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload: Dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        res = requests.post(url, json=payload, timeout=10)
        return res.status_code == 200
    except Exception as e:
        logger.error(f"Error sending Telegram message: {e}")
        return False


def get_telegram_file_bytes(file_id: str) -> Optional[bytes]:
    """Downloads audio/voice bytes from Telegram Bot API."""
    if not TELEGRAM_BOT_TOKEN:
        return None
    try:
        # Step 1: getFile path
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile?file_id={file_id}"
        res = requests.get(url, timeout=10)
        if res.status_code != 200:
            logger.error(f"Failed to getFile info: {res.text}")
            return None
        file_path = res.json().get("result", {}).get("file_path")
        if not file_path:
            return None

        # Step 2: Download the raw bytes
        download_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
        dl_res = requests.get(download_url, timeout=30)
        if dl_res.status_code == 200:
            return dl_res.content
        return None
    except Exception as e:
        logger.error(f"Error downloading file from Telegram: {e}")
        return None


# ==============================================================================
# GEMINI MULTIMODAL AUDIO TRANSCRIPTION & MICRO-STEP ENGINE
# ==============================================================================

def transcribe_and_decompose_audio(audio_bytes: bytes, mime_type: str = "audio/ogg") -> Dict[str, Any]:
    """
    Transcribes audio bytes using Gemini Flash native audio understanding,
    generating an executive summary and ADHD micro-step decomposition.
    """
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not configured; returning mock transcription")
        return {
            "transcript": "[Audio recorded - Gemini API key required for full cloud transcription]",
            "title": "Voice Note Capture",
            "summary": "Voice memo received via Telegram gateway.",
            "category": "voice_memo",
            "microsteps": [
                "Review recorded audio note on local workstation",
                "Extract immediate single-threaded task into Tuesday Outbox"
            ]
        }

    try:
        # Using Google GenAI SDK or direct REST endpoint
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=GEMINI_API_KEY)
            
            prompt = (
                "You are MAX (Anima-ex-Machina), the Sovereign AI Executive Assistant. "
                "The user has sent a spontaneous mobile voice note.\n"
                "1. Transcribe the audio verbatim.\n"
                "2. Provide a concise Title and 2-sentence Executive Summary.\n"
                "3. Extract any specific tasks, goals, or follow-ups, and decompose them into 2-4 "
                "concrete, ADHD-adapted micro-steps (single-threaded, frictionless starting actions).\n"
                "4. Assign a category: 'work', 'academy', 'dsp_audio', 'family_mae', 'idea', or 'triage'.\n\n"
                "Output strictly valid JSON with keys: transcript, title, summary, category, microsteps (list of strings)."
            )

            part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[part, prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            parsed = json.loads(response.text)
            return parsed
        except ImportError:
            # Fallback to direct Gemini REST API
            b64_audio = base64.b64encode(audio_bytes).decode("utf-8")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
            payload = {
                "contents": [{
                    "parts": [
                        {"inline_data": {"mime_type": mime_type, "data": b64_audio}},
                        {"text": (
                            "Transcribe this voice note verbatim and extract ADHD micro-steps. "
                            "Output JSON: {\"transcript\": str, \"title\": str, \"summary\": str, \"category\": str, \"microsteps\": [str]}"
                        )}
                    ]
                }],
                "generationConfig": {
                    "responseMimeType": "application/json"
                }
            }
            res = requests.post(url, json=payload, timeout=25)
            if res.status_code == 200:
                data = res.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text)
            else:
                logger.error(f"Gemini REST API error {res.status_code}: {res.text}")
                return {"transcript": "[Gemini API error during audio decode]", "summary": "Error during decode", "microsteps": []}
    except Exception as e:
        logger.error(f"Transcription failure: {e}")
        return {
            "transcript": f"[Transcription error: {str(e)}]",
            "title": "Voice Note Capture",
            "summary": "Voice note saved; manual review needed.",
            "category": "voice_memo",
            "microsteps": ["Check audio file in Firestore"]
        }


# ==============================================================================
# FIRESTORE DATA ADAPTERS
# ==============================================================================

def record_to_stream(entry: Dict[str, Any]) -> str:
    """Records an incoming omnichannel message to Firestore."""
    entry["timestamp"] = entry.get("timestamp", datetime.now().isoformat())
    doc_id = f"msg_{int(time.time())}_{os.urandom(4).hex()}"
    entry["id"] = doc_id

    if FIRESTORE_CONNECTED and db:
        try:
            db.collection("omnichannel_stream").document(doc_id).set(entry)
            logger.info(f"💾 Stored message in Firestore omnichannel_stream: {doc_id}")
            return doc_id
        except Exception as e:
            logger.error(f"Firestore save error: {e}")

    _MEMORY_STREAM.append(entry)
    return doc_id


def stage_to_outbox(item: Dict[str, Any]) -> str:
    """Stages an action item into Tuesday Outbox for 1-tap signoff."""
    item["timestamp"] = item.get("timestamp", datetime.now().isoformat())
    item["status"] = item.get("status", "pending")
    outbox_id = f"outbox_{int(time.time())}_{os.urandom(4).hex()}"
    item["id"] = outbox_id

    if FIRESTORE_CONNECTED and db:
        try:
            db.collection("triage_outbox").document(outbox_id).set(item)
            logger.info(f"📦 Staged action item in Firestore triage_outbox: {outbox_id}")
            return outbox_id
        except Exception as e:
            logger.error(f"Firestore outbox save error: {e}")

    _MEMORY_OUTBOX.append(item)
    return outbox_id


# ==============================================================================
# SLASH COMMAND HANDLERS
# ==============================================================================

def handle_sprint_command(params: str, chat_id: int):
    """Handles /sprint [minutes] to initiate a focus block."""
    duration = 25
    if params.strip().isdigit():
        duration = int(params.strip())

    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=duration)

    msg = (
        f"⚡ *FOCUS SPRINT INITIATED ({duration}m)*\n\n"
        f"• *Start Time*: {start_time.strftime('%I:%M %p')}\n"
        f"• *Anchor End Time*: {end_time.strftime('%I:%M %p')}\n"
        f"• *Posture*: MAX Sovereign Blue (#3b82f6) / Zero Distraction\n\n"
        f"_Single-task flow locked. Notifications muffled. What is the single step in front of you?_"
    )
    send_telegram_message(chat_id, msg)
    record_to_stream({
        "channel": "telegram",
        "type": "command",
        "command": "/sprint",
        "duration_minutes": duration,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat()
    })


def handle_triage_command(chat_id: int):
    """Handles /triage to display the immediate single-step task."""
    pending_tasks = []
    if FIRESTORE_CONNECTED and db:
        try:
            docs = db.collection("triage_outbox").where("status", "==", "pending").limit(5).stream()
            pending_tasks = [d.to_dict() for d in docs]
        except Exception as e:
            logger.warning(f"Error reading triage outbox: {e}")

    if not pending_tasks and _MEMORY_OUTBOX:
        pending_tasks = [t for t in _MEMORY_OUTBOX if t.get("status") == "pending"][:5]

    if not pending_tasks:
        msg = (
            "🎯 *CALM RADAR: Outbox Clear*\n\n"
            "You have 0 urgent blocking tasks awaiting executive signoff.\n"
            "Enjoy the uninterrupted flow state or type `/capture <thought>` to store a new note."
        )
    else:
        now_task = pending_tasks[0]
        msg = (
            f"🎯 *ADHD EXECUTIVE TRIAGE: SINGLE-STEP NOW*\n\n"
            f"**Current Priority**: {now_task.get('title', 'Action Item')}\n"
            f"• *Category*: `{now_task.get('category', 'triage')}`\n"
            f"• *Staged*: {now_task.get('timestamp', '')[:16]}\n\n"
            f"**Concrete Next Micro-Step**:\n"
        )
        microsteps = now_task.get("microsteps", [])
        if microsteps:
            for i, step in enumerate(microsteps[:3], 1):
                msg += f"  {i}. {step}\n"
        else:
            msg += f"  1. Review {now_task.get('summary', 'task details')}\n"

        if len(pending_tasks) > 1:
            msg += f"\n_({len(pending_tasks) - 1} other items resting calmly in queue)_"

    send_telegram_message(chat_id, msg)


def handle_capture_command(text: str, chat_id: int):
    """Handles /capture <thought> to record a quick note into Firestore."""
    if not text.strip():
        send_telegram_message(chat_id, "⚠️ Please provide text to capture: `/capture [Quick note or idea]`")
        return

    doc_id = record_to_stream({
        "channel": "telegram",
        "type": "text_capture",
        "text": text,
        "sender": "Daniel Bass Sherizen"
    })
    outbox_id = stage_to_outbox({
        "title": f"Captured Thought: {text[:40]}...",
        "summary": text,
        "category": "quick_capture",
        "microsteps": ["Review and file into appropriate repo or Monday board"]
    })

    msg = (
        f"📥 *THOUGHT CAPTURED & STAGED*\n\n"
        f"\"{text}\"\n\n"
        f"• *Stream ID*: `{doc_id}`\n"
        f"• *Tuesday Outbox*: Staged for weekly review (`{outbox_id}`)"
    )
    send_telegram_message(chat_id, msg)


def handle_status_command(chat_id: int):
    """Handles /status to return ecosystem health."""
    current_time = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
    msg = (
        f"🛡️ *MAX OMNICHANNEL GATEWAY STATUS*\n\n"
        f"• *Status*: ONLINE (Google Cloud Run)\n"
        f"• *Project*: `{PROJECT_ID}`\n"
        f"• *Firestore*: {'✅ CONNECTED' if FIRESTORE_CONNECTED else '⚠️ FALLBACK'}\n"
        f"• *Gemini Audio Engine*: {'✅ ACTIVE' if GEMINI_API_KEY else '⚠️ NO KEY'}\n"
        f"• *Server Time*: {current_time}\n"
        f"• *Scale*: Scale-to-Zero (0-3 instances)"
    )
    send_telegram_message(chat_id, msg)


# ==============================================================================
# FLASK WEB ENDPOINTS
# ==============================================================================

@app.route("/", methods=["GET"])
def root():
    return jsonify({
        "service": "omnichannel-gateway",
        "description": "MAX Sovereign AI Omnichannel Telegram Voice Gateway & Triage Synchronizer",
        "status": "HEALTHY",
        "project": PROJECT_ID,
        "firestore_connected": FIRESTORE_CONNECTED,
        "gemini_active": bool(GEMINI_API_KEY),
        "timestamp": datetime.now().isoformat()
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "OK", "timestamp": datetime.now().isoformat()}), 200


@app.route("/webhook/telegram", methods=["POST"])
def telegram_webhook():
    """Primary webhook endpoint invoked by Telegram Bot API."""
    data = request.get_json(force=True, silent=True) or {}
    message = data.get("message") or data.get("edited_message")

    if not message:
        return jsonify({"status": "NO_MESSAGE_PAYLOAD"}), 200

    chat = message.get("chat", {})
    chat_id = chat.get("id")
    sender = message.get("from", {}).get("first_name", "User")
    msg_id = message.get("message_id")

    # 1. Handle Voice Note / Audio Attachment
    if "voice" in message or "audio" in message:
        audio_info = message.get("voice") or message.get("audio", {})
        file_id = audio_info.get("file_id")
        duration = audio_info.get("duration", 0)
        mime_type = audio_info.get("mime_type", "audio/ogg")

        logger.info(f"🎙️ Received voice note from {sender} (Duration: {duration}s, FileID: {file_id})")
        send_telegram_message(chat_id, f"🎙️ _Processing voice memo ({duration}s) with Gemini Flash audio reasoning..._")

        # Download audio from Telegram
        audio_bytes = get_telegram_file_bytes(file_id)
        if not audio_bytes:
            send_telegram_message(chat_id, "⚠️ Could not download voice note from Telegram. Please try again.")
            return jsonify({"status": "DOWNLOAD_FAILED"}), 200

        # Transcribe & extract ADHD micro-steps
        analysis = transcribe_and_decompose_audio(audio_bytes, mime_type=mime_type)

        # Store in Firestore
        record_id = record_to_stream({
            "channel": "telegram",
            "type": "voice_note",
            "sender": sender,
            "duration": duration,
            "analysis": analysis,
            "chat_id": chat_id,
            "message_id": msg_id
        })

        outbox_id = stage_to_outbox({
            "title": analysis.get("title", f"Voice Note from {sender}"),
            "summary": analysis.get("summary", analysis.get("transcript", "")),
            "transcript": analysis.get("transcript", ""),
            "category": analysis.get("category", "voice_memo"),
            "microsteps": analysis.get("microsteps", []),
            "source": "telegram_voice"
        })

        # Send rich confirmation card
        reply_msg = (
            f"✅ *VOICE NOTE PROCESSED* ({duration}s)\n\n"
            f"**Title**: {analysis.get('title', 'Voice Note')}\n"
            f"**Summary**: {analysis.get('summary', '')}\n\n"
            f"**Transcript**:\n_{analysis.get('transcript', '')}_\n\n"
            f"📋 **ADHD Micro-Steps**:\n"
        )
        for i, step in enumerate(analysis.get("microsteps", []), 1):
            reply_msg += f"  {i}. {step}\n"

        reply_msg += f"\n_Staged in Tuesday Outbox (`{outbox_id}`) for 1-tap signoff._"
        send_telegram_message(chat_id, reply_msg)
        return jsonify({"status": "VOICE_PROCESSED", "record_id": record_id, "outbox_id": outbox_id}), 200

    # 2. Handle Text Messages & Slash Commands
    text = message.get("text", "").strip()
    if text:
        logger.info(f"💬 Received text from {sender}: '{text}'")
        if text.startswith("/sprint") or text.startswith("/focus"):
            params = text.split(" ", 1)[1] if " " in text else ""
            handle_sprint_command(params, chat_id)
        elif text.startswith("/triage"):
            handle_triage_command(chat_id)
        elif text.startswith("/capture"):
            note = text.split(" ", 1)[1] if " " in text else ""
            handle_capture_command(note, chat_id)
        elif text.startswith("/status"):
            handle_status_command(chat_id)
        else:
            # Treat plain message as a quick capture
            handle_capture_command(text, chat_id)

    return jsonify({"status": "OK"}), 200


@app.route("/ingest", methods=["POST"])
def generic_ingest():
    """REST ingestion endpoint for local Signal, SMS, and webhook bridges."""
    data = request.get_json(force=True, silent=True) or {}
    text = data.get("text", "")
    sender = data.get("sender", "External")
    channel = data.get("channel", "rest_api")

    if not text:
        return jsonify({"error": "Empty text payload"}), 400

    doc_id = record_to_stream({
        "channel": channel,
        "sender": sender,
        "text": text,
        "type": "external_ingest"
    })
    return jsonify({"status": "INGESTED", "id": doc_id}), 200


@app.route("/api/stream", methods=["GET"])
def get_stream():
    """Returns the latest 20 items from the omnichannel stream."""
    limit = int(request.args.get("limit", 20))
    items = []
    if FIRESTORE_CONNECTED and db:
        try:
            docs = db.collection("omnichannel_stream").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(limit).stream()
            items = [d.to_dict() for d in docs]
        except Exception as e:
            logger.warning(f"Error querying stream: {e}")

    if not items:
        items = list(reversed(_MEMORY_STREAM))[:limit]

    return jsonify({"count": len(items), "items": items}), 200


@app.route("/api/outbox", methods=["GET"])
def get_outbox():
    """Returns pending outbox items awaiting executive signoff."""
    items = []
    if FIRESTORE_CONNECTED and db:
        try:
            docs = db.collection("triage_outbox").where("status", "==", "pending").stream()
            items = [d.to_dict() for d in docs]
        except Exception as e:
            logger.warning(f"Error querying outbox: {e}")

    if not items:
        items = [t for t in _MEMORY_OUTBOX if t.get("status") == "pending"]

    return jsonify({"count": len(items), "items": items}), 200


@app.route("/api/outbox/approve", methods=["POST"])
def approve_outbox_item():
    """1-tap approval endpoint for outbox tasks."""
    data = request.get_json(force=True, silent=True) or {}
    outbox_id = data.get("id")
    if not outbox_id:
        return jsonify({"error": "Missing outbox id"}), 400

    if FIRESTORE_CONNECTED and db:
        try:
            db.collection("triage_outbox").document(outbox_id).update({
                "status": "APPROVED",
                "approved_at": datetime.now().isoformat()
            })
            return jsonify({"status": "APPROVED", "id": outbox_id}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    for item in _MEMORY_OUTBOX:
        if item.get("id") == outbox_id:
            item["status"] = "APPROVED"
            return jsonify({"status": "APPROVED", "id": outbox_id}), 200

    return jsonify({"error": "Item not found"}), 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
