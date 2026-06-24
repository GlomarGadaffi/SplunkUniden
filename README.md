# bcd325-splunk-addon

Splunk Technology Add-on for the Uniden BCD325P2 radio scanner. ingests real-time RF telemetry from a serial bridge, parses P25 control channels and EDACS trunking data, emits structured JSON indexed natively in Splunk.

## integration

**input**: BCD325P2 serial stream via bcd325p2_stream.py (raw JSON-per-line)

**sourcetype**: `uniden:bcd325p2:glg` (Custom add-on)

**indexing config** (`default/props.conf`):
- `INDEXED_EXTRACTIONS = json` — promotes all top-level keys to searchable fields
- `SHOULD_LINEMERGE = false` — each line is a complete event
- `NO_BINARY_CHECK = true` — trust the input
- `KV_MODE = none` — skip redundant extraction

## events & fields

each JSON event from the scanner contains:
- **frequency** (MHz), **mode** (FM/NFM/etc.), **short_name** (talkgroup ID)
- **subunit_id**, **subunit_shortname** (fleet/individual)
- **phase_id** (P25 multisite tracking)
- **timestamp**, **duration** (call length)
- optional: signal quality metrics, EDACS status

## deployment

1. install add-on to `$SPLUNK_HOME/etc/apps/uniden_bcd325p2_addon`
2. configure bcd325p2_stream.py input (serial port, baud rate)
3. set index destination
4. Splunk auto-indexes with the schema above

## use cases

- **RF audit**: archive and search all scanner traffic by frequency, talkgroup, or unit
- **compliance**: capture and retain P25/EDACS calls for regulatory archival
- **incident timeline**: correlate radio traffic with system events

## notes

P25 control channel parsing via a separate phase-II decoder (not included); this add-on consumes its output.
