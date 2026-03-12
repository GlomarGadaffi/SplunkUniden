# TA-bcd325p2-sentinel

> **Splunk Technology Add-on for the Uniden BCD325P2**
> Native serial bridge. Real-time RF telemetry ingestion. P25/EDACS control channel parsing. No middleware.

---

## What It Does

Polls the BCD325P2 via USB serial using the native `GLG` command at 10Hz. Parses each response into structured JSON and emits it to `stdout` — which Splunk ingests as a scripted input. You get a live stream of every frequency hit, TGID, system name, NAC/color code, squelch event, and modulation type, indexed and searchable in real time.

No agents. No third-party SDR tooling. The scanner does the RF work; this just gets the data out of it cleanly.

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.x | Must be accessible to the Splunk process |
| `pyserial` | Install into Splunk's Python env: see below |
| Uniden BCD325P2 | Connected via USB, serial port identified |
| Splunk 8.x+ | Heavy Forwarder or full instance |

### Install pyserial into Splunk's Python environment

```bash
# Linux / macOS
$SPLUNK_HOME/bin/python3 -m pip install pyserial

# Windows
%SPLUNK_HOME%\bin\python3.exe -m pip install pyserial
```

---

## Installation

```bash
# Clone into Splunk's apps directory
cd $SPLUNK_HOME/etc/apps
git clone https://github.com/YOUR_USERNAME/TA-bcd325p2-sentinel.git

# Make the script executable (Linux/macOS)
chmod +x TA-bcd325p2-sentinel/bin/bcd325p2_stream.py
```

---

## Configuration

**One required edit before first run:**

Open `bin/bcd325p2_stream.py` and set `SERIAL_PORT` to match your system:

```python
# Linux / macOS
SERIAL_PORT = '/dev/ttyUSB0'

# Windows
SERIAL_PORT = 'COM3'
```

Find your port:

```bash
# Linux
ls /dev/tty{USB,ACM}*

# macOS
ls /dev/cu.*

# Windows (PowerShell)
Get-PnpDevice -Class Ports | Select FriendlyName
```

Baud rate defaults to `115200` — the BCD325P2's maximum. Do not lower this unless you have a specific reason.

---

## Data Schema

Each JSON event written to Splunk has the following fields:

| Field | Description |
|---|---|
| `command` | Always `GLG` |
| `frequency_or_tgid` | Frequency in Hz or Trunked Group ID |
| `modulation` | `FM`, `NFM`, `AM`, `P25`, etc. |
| `attenuation` | Attenuation flag (0 = off, 1 = on) |
| `ctcss_dcs` | CTCSS/DCS tone or code if active |
| `system_name` | Programmed system name from scanner |
| `group_name` | Programmed group/channel group name |
| `channel_name` | Programmed channel name |
| `squelch_status` | `0` = closed, `1` = open |
| `mute_status` | Mute state |
| `system_tag` | System tag ID |
| `channel_tag` | Channel tag ID |
| `p25_nac` | P25 Network Access Code (hex) or `NONE` |

---

## Splunk Queries

### Activity by system
```spl
sourcetype="uniden:bcd325p2:glg"
| stats count by system_name
| sort -count
```

### P25 NAC frequency hits
```spl
sourcetype="uniden:bcd325p2:glg" p25_nac!="NONE"
| timechart span=5m count by p25_nac
```

### Live intercept log (last 60 min)
```spl
sourcetype="uniden:bcd325p2:glg"
| table _time, frequency_or_tgid, system_name, group_name, channel_name, p25_nac, squelch_status
| sort -_time
```

### Squelch open events only
```spl
sourcetype="uniden:bcd325p2:glg" squelch_status=1
| table _time, frequency_or_tgid, system_name, channel_name, modulation, p25_nac
```

---

## Dashboard

A pre-built dashboard ships with the add-on at `default/data/ui/views/sentinel_overview.xml`. After installation and restart, it appears under **Apps → BCD325P2 Sentinel Protocol → Sentinel Protocol: RF Telemetry**.

Panels:
- Active systems by hit count (pie)
- P25 NAC/color code hits (bar)
- Real-time intercept log (table, last 60 min)

---

## Known Limitations

- The `GLG` command returns data only when the scanner is actively monitoring. Idle scanner = no events. This is expected behavior, not a bug.
- `GLG` responses during scan hold or key lock may return malformed lines. These are dropped silently by the parser.
- Windows serial port names above `COM9` require the `\\.\COM10` prefix in Python. The script handles standard `COMx` names; adjust manually if needed.
- This add-on polls at 100ms intervals. Faster polling saturates the serial buffer; slower polling misses short transmissions.

---

## Project Structure

```
TA-bcd325p2-sentinel/
├── bin/
│   └── bcd325p2_stream.py       # Serial poller and GLG parser
├── default/
│   ├── app.conf                 # Add-on identity
│   ├── inputs.conf              # Scripted input definition
│   ├── props.conf               # Sourcetype config
│   └── data/ui/views/
│       └── sentinel_overview.xml  # Pre-built dashboard
├── .github/
│   └── ISSUE_TEMPLATE.md        # Bug report template
├── LICENSE
└── README.md
```

---

## License

MIT. See [LICENSE](LICENSE).

---

## Author

**Glomar** — Scanner nerd, RF intelligence hobbyist.
This exists because I wanted P25 telemetry in Splunk and nothing off-the-shelf did it without three layers of abstraction I didn't trust.
