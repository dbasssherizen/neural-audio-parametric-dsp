#!/usr/bin/env python3
"""
Sovereign AI Academy: Opportunistic Android Wireless Debugging Ingestion Vector
Author: MAX (Anima Ex Machina) & Daniel Bass Sherizen
Target: Justin Muir (+1 630-418-9227 / nightmareglove@gmail.com)

Overview:
    Opportunistically connects to Daniel's Google Pixel over trusted Wi-Fi SSIDs
    (e.g., home networks) when Wireless Debugging is enabled. Ingests SMS/RCS messages,
    call recordings, and Gemini Call Notes, forwarding them seamlessly to both
    the local workspace state and the Cloud Run 24/7 autonomous watcher.

Usage:
    python3 scripts/wireless_adb_ingest.py --status
    python3 scripts/wireless_adb_ingest.py --scan
    python3 scripts/wireless_adb_ingest.py --connect 192.168.1.50:5555
    python3 scripts/wireless_adb_ingest.py --daemon --interval 60
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
import urllib.request
import urllib.error

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOTES_DIR = os.path.join(PROJECT_ROOT, "notes")
PROCESSED_LOG = os.path.join(NOTES_DIR, "wireless_adb_processed.json")
LOG_FILE = os.path.join(NOTES_DIR, "wireless_adb.log")

CLOUD_RUN_INGEST_URL = os.environ.get(
    "CLOUD_RUN_INGEST_URL",
    "https://justin-comm-watcher-75904656792.us-central1.run.app/ingest"
)

# Standard ADB paths on macOS
DEFAULT_ADB_PATHS = [
    "/Users/danielbasssherizen/Library/Android/sdk/platform-tools/adb",
    "/usr/local/bin/adb",
    "/opt/homebrew/bin/adb",
    "adb"
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [WIRELESS-ADB] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding="utf-8")
    ]
)
logger = logging.getLogger("WirelessADBIngest")

JUSTIN_PHONE_PATTERNS = ["6304189227", "630-418-9227", "+16304189227"]

def find_adb_binary() -> Optional[str]:
    for p in DEFAULT_ADB_PATHS:
        if os.path.exists(p) and os.access(p, os.X_OK):
            return p
    # Try which
    try:
        res = subprocess.run(["which", "adb"], capture_output=True, text=True)
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    except Exception:
        pass
    return None

ADB_BIN = find_adb_binary()

def load_processed_hashes() -> set:
    if os.path.exists(PROCESSED_LOG):
        try:
            with open(PROCESSED_LOG, "r", encoding="utf-8") as f:
                data = json.load(f)
                return set(data.get("processed_ids", []))
        except Exception as e:
            logger.warning(f"Error loading processed hashes: {e}")
    return set()

def save_processed_hashes(hashes: set):
    os.makedirs(NOTES_DIR, exist_ok=True)
    try:
        with open(PROCESSED_LOG, "w", encoding="utf-8") as f:
            json.dump({"processed_ids": list(hashes), "last_updated": datetime.now().isoformat()}, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving processed hashes: {e}")

def run_adb_command(args: List[str], timeout: int = 15) -> Tuple[int, str, str]:
    if not ADB_BIN:
        return 127, "", "adb binary not found in standard paths"
    cmd = [ADB_BIN] + args
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return res.returncode, res.stdout, res.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return 1, "", str(e)

def get_connected_devices() -> List[str]:
    code, stdout, stderr = run_adb_command(["devices"])
    if code != 0:
        return []
    devices = []
    for line in stdout.splitlines()[1:]:
        parts = line.strip().split()
        if len(parts) >= 2 and parts[1] == "device":
            devices.append(parts[0])
    return devices

def push_to_cloud_run(payload: Dict[str, Any]) -> bool:
    try:
        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            CLOUD_RUN_INGEST_URL,
            data=req_data,
            headers={"Content-Type": "application/json", "User-Agent": "WirelessADBIngest/1.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                logger.info(f"✅ Forwarded entry to Cloud Run endpoint: {CLOUD_RUN_INGEST_URL}")
                return True
    except Exception as e:
        logger.warning(f"Notice: Cloud Run forward failed or offline: {e}")
    return False

def scan_wireless_sms(device_serial: str, processed_set: set) -> int:
    """
    Safely queries read-only content provider for SMS from Justin.
    """
    logger.info(f"Querying SMS content provider on device {device_serial}...")
    where_clause = "address LIKE '%6304189227%' OR address LIKE '%630-418-9227%'"
    query_cmd = [
        "-s", device_serial,
        "shell", "content", "query",
        "--uri", "content://sms",
        "--projection", "_id,address,body,date,type",
        "--where", f'"{where_clause}"'
    ]
    code, stdout, stderr = run_adb_command(query_cmd)
    if code != 0:
        logger.warning(f"Notice: unable to query content://sms on {device_serial} (permissions or lock): {stderr.strip() or stdout.strip()}")
        return 0

    new_count = 0
    # Content query output format: Row: 0 _id=123, address=..., body=...
    rows = stdout.split("Row: ")
    for row in rows:
        if not row.strip():
            continue
        try:
            row_dict = {}
            for token in row.split(", "):
                if "=" in token:
                    k, v = token.split("=", 1)
                    row_dict[k.strip()] = v.strip()

            msg_id = row_dict.get("_id")
            body = row_dict.get("body", "")
            date_ms = row_dict.get("date", "0")
            msg_type = row_dict.get("type", "1")  # 1 = inbox (from Justin), 2 = sent

            if not msg_id or not body:
                continue

            unique_hash = hashlib.sha256(f"{msg_id}_{date_ms}_{body}".encode("utf-8")).hexdigest()
            if unique_hash in processed_set:
                continue

            processed_set.add(unique_hash)
            new_count += 1

            author = "Justin Muir" if msg_type == "1" else "Daniel Bass Sherizen"
            logger.info(f"📥 New SMS captured via Wireless ADB [{author}]: {body[:60]}...")

            # Push to Cloud Run
            push_to_cloud_run({
                "text": body,
                "source": "wireless_adb_sms",
                "author": author,
                "device": device_serial,
                "timestamp": datetime.now().isoformat()
            })

            # Save locally in notes/
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            local_drop = os.path.join(NOTES_DIR, f"adb_sms_{timestamp_str}_{msg_id}.json")
            with open(local_drop, "w", encoding="utf-8") as f:
                json.dump({
                    "id": msg_id,
                    "author": author,
                    "body": body,
                    "date": date_ms,
                    "source": "wireless_adb"
                }, f, indent=2)

        except Exception as err:
            logger.debug(f"Error parsing row: {err}")

    if new_count > 0:
        save_processed_hashes(processed_set)
        logger.info(f"Processed {new_count} new messages from Justin via Wireless ADB.")

    return new_count

def scan_wireless_recordings(device_serial: str, processed_set: set) -> int:
    """
    Checks /sdcard/Recordings or Google Recorder transcripts on device.
    """
    recordings_path = "/sdcard/Recordings"
    code, stdout, stderr = run_adb_command(["-s", device_serial, "shell", "ls", "-la", recordings_path])
    if code != 0:
        return 0

    new_count = 0
    for line in stdout.splitlines():
        parts = line.strip().split()
        if len(parts) >= 8:
            fname = parts[-1]
            if fname.endswith(".txt") or fname.endswith(".m4a") or fname.endswith(".wav"):
                unique_key = f"rec_{fname}_{parts[4]}" # name + size
                if unique_key in processed_set:
                    continue
                processed_set.add(unique_key)
                new_count += 1
                logger.info(f"🎙️ Found new recording file on Pixel: {fname}")
                if fname.endswith(".txt"):
                    # Pull and ingest text
                    pull_code, p_out, _ = run_adb_command(["-s", device_serial, "shell", "cat", f"{recordings_path}/{fname}"])
                    if pull_code == 0 and p_out.strip():
                        push_to_cloud_run({
                            "text": p_out.strip(),
                            "source": "wireless_adb_recorder",
                            "author": "Justin Muir (Call Transcript)",
                            "filename": fname,
                            "timestamp": datetime.now().isoformat()
                        })

    if new_count > 0:
        save_processed_hashes(processed_set)

    return new_count

def run_single_scan(target_device: Optional[str] = None) -> int:
    devices = get_connected_devices()
    if not devices:
        logger.info("No active ADB devices connected over Wi-Fi/USB. Waiting for next cycle.")
        return 0

    target = target_device if target_device and target_device in devices else devices[0]
    logger.info(f"Scanning active device: {target} (Total connected: {len(devices)})")

    processed = load_processed_hashes()
    total_new = 0
    total_new += scan_wireless_sms(target, processed)
    total_new += scan_wireless_recordings(target, processed)
    return total_new

def main():
    parser = argparse.ArgumentParser(description="Opportunistic Android Wireless Debugging Ingestion Vector")
    parser.add_argument("--status", action="store_true", help="Check ADB status and connected devices")
    parser.add_argument("--scan", action="store_true", help="Perform single scan across connected devices")
    parser.add_argument("--connect", type=str, help="Connect to IP:port (e.g. 192.168.1.50:5555)")
    parser.add_argument("--daemon", action="store_true", help="Run daemon continuously")
    parser.add_argument("--interval", type=int, default=60, help="Poll interval in seconds (default: 60)")
    args = parser.parse_args()

    if args.status:
        print(f"ADB Binary: {ADB_BIN or 'NOT FOUND'}")
        devices = get_connected_devices()
        print(f"Connected Devices ({len(devices)}): {devices}")
        print(f"Cloud Run Target: {CLOUD_RUN_INGEST_URL}")
        processed = load_processed_hashes()
        print(f"Processed Entity Hashes: {len(processed)}")
        return

    if args.connect:
        logger.info(f"Connecting to wireless device: {args.connect}...")
        code, out, err = run_adb_command(["connect", args.connect])
        print(out.strip() or err.strip())
        return

    if args.scan:
        n = run_single_scan()
        print(f"Scan complete. Ingested {n} new entities.")
        return

    if args.daemon:
        logger.info(f"Starting Wireless ADB Ingestion Daemon (interval: {args.interval}s)...")
        while True:
            try:
                run_single_scan()
            except Exception as e:
                logger.error(f"Daemon scan iteration error: {e}")
            time.sleep(args.interval)

    # Default to single scan
    run_single_scan()

if __name__ == "__main__":
    main()
