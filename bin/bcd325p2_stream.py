#!/usr/bin/env python3
"""
bcd325p2_stream.py

Polls the BCD325P2 via serial using the GLG (Get Last Global) command.
Emits one JSON object per line to stdout on each active hit.
Splunk's scripted input framework handles the rest.

GLG returns a comma-delimited response only when the scanner is actively
receiving. Silent scanner = no output. That is correct behavior.

Serial reconnect is automatic with a 5-second backoff. Splunk's input
framework will restart the script if it exits; this loop is a first-line
defense against transient serial errors (cable wiggle, USB re-enumeration).
"""

import sys
import time
import json
import serial

# --- Configuration ---
# Set SERIAL_PORT to match your system before first run.
# Linux: /dev/ttyUSB0 or /dev/ttyACM0
# macOS: /dev/cu.usbserial-XXXX
# Windows: COM3 (or \\.\COM10 for ports above COM9)
SERIAL_PORT = '/dev/ttyUSB0'
BAUD_RATE = 115200  # BCD325P2 maximum; do not lower without a specific reason

# 100ms poll interval. Faster saturates the serial buffer.
# Shorter transmissions can still be missed at this rate on very active trunked systems.
POLL_INTERVAL_SECONDS = 0.1

SERIAL_RECONNECT_DELAY_SECONDS = 5


def parse_glg_response_to_dict(raw_glg_line: str) -> dict | None:
    """
    Parses a raw GLG response string into a structured dictionary.

    BCD325P2 GLG format (13 fields, comma-delimited):
      GLG,<freq_or_tgid>,<modulation>,<attenuation>,<ctcss_dcs>,
          <system_name>,<group_name>,<channel_name>,<squelch_status>,
          <mute_status>,<system_tag>,<channel_tag>,<p25_nac>

    Returns None if the line doesn't have the expected number of fields.
    Caller is responsible for pre-filtering non-GLG lines before passing here.
    """
    parts = raw_glg_line.strip().split(',')

    if len(parts) < 13:
        return None

    return {
        "command":           parts[0],
        "frequency_or_tgid": parts[1],
        "modulation":        parts[2],
        "attenuation":       parts[3],
        "ctcss_dcs":         parts[4],
        "system_name":       parts[5],
        "group_name":        parts[6],
        "channel_name":      parts[7],
        "squelch_status":    parts[8],
        "mute_status":       parts[9],
        "system_tag":        parts[10],
        "channel_tag":       parts[11],
        "p25_nac":           parts[12],
    }


def emit_json_event(payload: dict) -> None:
    """Writes a single JSON event to stdout and flushes immediately.
    Splunk's scripted input reads line-by-line from stdout; flush is not optional."""
    sys.stdout.write(json.dumps(payload) + '\n')
    sys.stdout.flush()


def log_error(message: str) -> None:
    """Writes to stderr. Splunk captures stderr as internal logs, not indexed events."""
    sys.stderr.write(message + '\n')
    sys.stderr.flush()


def run_polling_loop(serial_connection: serial.Serial) -> None:
    """Inner loop. Runs until a serial error breaks it, which triggers reconnect in main."""
    while True:
        serial_connection.write(b'GLG\r')
        raw_response = serial_connection.read_until(b'\r').decode('ascii', errors='ignore')

        # Scanner error codes — log and continue, don't crash
        if raw_response.startswith(("ERR", "NG", "FER", "ORER")):
            log_error(f"BCD325P2 error response: {raw_response.strip()}")
            time.sleep(POLL_INTERVAL_SECONDS)
            continue

        # GLG.......... (dotted) means scanner is idle / scanning with no hit
        # GLG, (with data following) means active channel
        if raw_response.startswith("GLG,") and not raw_response.startswith("GLG.........."):
            parsed_event = parse_glg_response_to_dict(raw_response)
            if parsed_event:
                emit_json_event(parsed_event)

        time.sleep(POLL_INTERVAL_SECONDS)


def main() -> None:
    """Outer reconnect loop. Serial failures are recoverable; exit only on KeyboardInterrupt."""
    while True:
        try:
            with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2) as serial_connection:
                log_error(f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud.")
                run_polling_loop(serial_connection)

        except serial.SerialException as serial_error:
            log_error(f"Serial connection lost: {serial_error}. Retrying in {SERIAL_RECONNECT_DELAY_SECONDS}s.")
            time.sleep(SERIAL_RECONNECT_DELAY_SECONDS)

        except KeyboardInterrupt:
            log_error("Interrupted. Exiting.")
            sys.exit(0)

        except Exception as unexpected_error:
            log_error(f"Unexpected error: {unexpected_error}. Retrying in {SERIAL_RECONNECT_DELAY_SECONDS}s.")
            time.sleep(SERIAL_RECONNECT_DELAY_SECONDS)


if __name__ == '__main__':
    main()
