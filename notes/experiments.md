# Experiment log

Keep original files unchanged in `captures/`; do not commit them. Store logs containing addresses and keys there or in `private/`.

## smoke-01: radio check after experimental firmware

- File: `captures/sniffer-smoke-01.pcap`, 475355 bytes.
- SHA256: `a6aea53683e1aee57452700d2d1e5b6b63b1e896331131b6993d6558f94084a3`.
- 6861 packets; last relative timestamp 49.659617 s.
- SuperMini/nice!nano with official Dongle Sniffer 4.1.1 experimentally loaded via UF2 at 0x1000.
- No follow target selected and no controlled button presses. Amplifier preparation and THR Remote state were unknown.
- AIRSTEP appears in 1909 packets; first frames 3, 4, 5, 18, 19. This does not identify the pedal model/mode.
- LE_THRII was not found. Cause unknown; this does not establish amplifier or BLE absence.
- tshark hierarchy: all packets nordic_ble/btle; 82 marked malformed, plus 3 nested malformed within 4 pbadv. Each suspicious packet requires CRC/metadata validation. Isolated unreadable names were not interpreted.
- This experiment does not establish the control protocol, encryption, completeness or connection following.
- Analysis: `python3 scripts/summarize-capture.py captures/sniffer-smoke-01.pcap`.

## Initial capture plan

1. Identify AIRSTEP and mode; do not yet assume A–E map to slots 1–5.
2. Close THR Remote on Mac and phone; turn the pedal off and amplifier on.
3. Start the BLE sniffer, select amplifier advertising, then turn the pedal on.
4. Record connection establishment and 10–15 seconds idle.
5. Press A → B → A → B → C → D → E with approximately 5-second pauses; record actual rather than planned times.
6. Repeat after reconnection in a separate capture.
7. Separately record toggling one known effect.

For every experiment record: filename and SHA-256, hardware/mode, start time, each press and observed action, frame numbers, gaps and outcome. Record press times in UTC and relative to capture start, with uncertainty estimates.

## amp-advertising-01: amplifier on, as reported by user

Original file: `captures/amp-advertising-01.pcap` (not committed). SHA256: `7298855cd74e4e3bbd6eb223052e983620b5290b2ee5d96a4d3224f2bedd6cca`. 5187 frames, last timestamp 8.619074 s. AIRSTEP appears 1553 times (first frames 1, 2, 3); LE_THRII not found. 64 frames marked malformed; isolated damaged names are not interpreted. The pedal is advertising; pedal power-off and THR Remote closure were not yet confirmed. Capture stopped and port released. Missing amplifier name does not establish missing radio traffic or encryption.

## amp-pedal-off-01: standard AIRSTEP turned off by user

`captures/amp-pedal-off-01.pcap`, SHA256 `c0b4133ef5b9007777c3f8c6aa7092c266c02f4423b254d0dedf088ff5bc012f`. 1742 frames, last timestamp 11.891238 s. LE_THRII: 138 advertising packets, first frames 18–20 and 51–53. Amplifier advertising appeared after AIRSTEP was turned off, consistent with an earlier occupied connection, but that connection itself had not been captured. 28 malformed; damaged name variants excluded from interpretation. User clarified: standard AIRSTEP, not YT Edition; button assignments still unknown.

## connection-01: first power-on of standard AIRSTEP

`captures/connection-01.pcap`, SHA256 `d0f33d3f366e93230efee6f3b7739adbda44098c120815fd5f29397d512c4ada`, 6549 frames, last timestamp 40.108907 s. Started with `--follow-by-name LE_THRII --scan-follow-rsp`. CONNECT_IND frame 3199 at t=17.117474 s: initiator matches previously observed AIRSTEP, advertiser is LE_THRII, Nordic CRC Ok, interval 30 ms. However, decoded hop=0 is suspicious; parameters require validation. Frames 4925/4929 are not evidence (damaged packets; 4929 CRC Error). No btatt/btsmp/LL control packets; all packets use the advertising access address. Connection following is unconfirmed; encryption cannot be inferred. The user reported connection; no presses were requested. Next experiment: follow by address after pedal power-off. Capture stopped.

## connection-02: address-follow attempt

Capture: `captures/connection-02.pcap`; SHA256 `95f6ffc59c7ee59060490effc881e49fd9bb79f61bcd844de76f7d24514a97e6`.
902 frames; last relative timestamp 18.485333 s. LE_THRII appears 152 times, first frames 3–5; RSSI roughly -74 to -80 dBm. No CONNECT_IND, data-channel packets, ATT, SMP or LL control observed. User reported connection. Capture stopped.
Local sniffer log warns follow was sent before device registration; subsequent device entry has is_followed=false, and unknown packet ID 0 is logged. Cause remains unresolved; advertising reception alone does not validate connection following on this experimental board. Next: improve placement, restart sniffer and verify follow registration before another pedal connection.

## connection-03 through connection-05: deferred selection

After USB restart, LE_THRII RSSI improved to approximately -50 to -57 dBm. CLI name-follow log explicitly says no device found and cannot send follow request; earlier advertising-only capture was not a valid following experiment. connection-03 and connection-04 are diagnostic scans, not command evidence. Added scripts/capture-follow.py using the official extcap shim and Wireshark toolbar protocol. In connection-05, selection is sent only after the target ADD event. Runtime log confirms SCANNING to FOLLOWING and follow request sent to the target random address. Actual data-channel following still requires a new connection. Pedal remains off pending instruction.

connection-05: user reports pedal connected. CONNECT_IND 1162 at relative 97.172996 s; ATT/SMP/LL traffic successfully captured. No button sequence requested yet: ordinary AIRSTEP button configuration must be clarified. Capture remains running; exports under private/.

## connection-05: preset sequence 1 requested

User confirms ordinary AIRSTEP has an active, user-configured preset-switching mode. Short presses only. Requested order A, B, A, B, C, D, E with about 5 s between presses. Instruction preparation UTC: 2026-10-28T21:37:02.025584+00:00. This is not an actual press timestamp; exact button times remain to be inferred from packet bursts and user observations. Last observed frame before instruction: 7397 (epoch 1793223413.044474). User confirmation of completion and visible slot mapping pending.

## connection-05: sequence 1 completed

User reported completion of requested A B A B C D E. Visible slot mapping was not explicitly confirmed. Capture stopped; SHA256 `1fb756541f412ea0651b8b68355a90a743641c103d921809af20f605d93e1608`. Times below are observed command transmission times, not independently measured footswitch times.

|Requested action|Frame|Relative seconds|Epoch seconds|Candidate index|
|---|---:|---:|---:|---:|
|A|8533|283.152933000|1793223443.916846000|0|
|B|8814|287.052708000|1793223447.816621000|1|
|A|9124|292.122594000|1793223452.886507000|0|
|B|9405|296.382549000|1793223457.146462000|1|
|C|9687|300.912407000|1793223461.676320000|2|
|D|10008|306.162672000|1793223466.926585000|3|
|E|10322|311.022281000|1793223471.786194000|4|

A repeats are byte-identical; B repeats are byte-identical. All seven primary writes differ only at characteristic-value offset 24 (zero-based). Each is followed approximately 0.45-0.60 seconds later by the same secondary write, then state notifications. Reconnection repeat still required.

User explicitly confirms first sequence visibly selected slots 1,2,1,2,3,4,5 and pedal is now off. Preparing connection-06 for a fresh-connection repeat.

## connection-06: repeat sequence requested

CONNECT_IND 3799 at t=27.034161 s; ATT initialization readable, SMP and encryption startup present. Preparing same A B A B C D E sequence with approximately 5 s pauses. Instruction preparation UTC 2026-10-28T21:41:04.361825+00:00. Latest observed frame/epoch before instruction: 4747 / 1793223668.586336000. These are not footswitch timestamps. Completion pending.

## connection-06: repeat completed

User reports completion. Capture stopped; SHA256 `24baf67983fd6c937fe7f7550e5a6bc68d11ace051fc24283e6ac5d8359bf1e7`. All seven primary writes equal the first session byte-for-byte. Observed transmission times, not independently measured press times:

|Button|Frame|Relative seconds|Epoch seconds|Slot|
|---|---:|---:|---:|---:|
|A|5357|64.176723000|1793223684.306514000|1|
|B|5666|68.556891000|1793223688.686682000|2|
|A|5959|72.247172000|1793223692.376963000|1|
|B|6320|78.037534000|1793223698.167325000|2|
|C|6590|81.667501000|1793223701.797292000|3|
|D|6907|86.167843000|1793223706.297634000|4|
|E|7198|90.368038000|1793223710.497829000|5|

## mac-replay-01: one slot 1 command from Mac

Scope updated by user: preset switching only; effect investigation excluded. Pedal switched off by user. Built Swift CoreBluetooth probe; discovered service and characteristic by UUID, enabled notifications, sent exactly one captured slot-1 Write Command at host log UTC 2026-10-28T21:46:38Z. Connected at 21:46:30Z, subscribed at 21:46:37Z; disconnected after 8 seconds. No initialization SysEx, secondary query, save operation or firmware operation sent. No notification callback received. Queueing without-response write does not establish delivery or slot change. Visual result pending.

Sniffer capture `captures/mac-replay-01.pcap` stopped; SHA256 `d67757780322b979fc69cc0ecb609dca3d1187bef72f347e125134740fe1b052`. CONNECT_IND 6814. Encryption startup is present, but ATT write is not readable; bad MIC at 7261/7328. The Mac capture cannot independently confirm transmitted command bytes or successful decryption. Do not infer link encryption type solely from a single partially captured pairing request.

mac-replay-01 visual result: user reports amplifier stayed on slot 5. Thus subscription plus primary command alone did not achieve the requested change; no conclusion about delivery vs session activation from that test alone.

mac-replay-02 prepared: identity request (connection-05 1232/1241), version query (1247/1262), activation pair in one characteristic write (1253/1266), then slot 1. Initialization profile is private/activation-profile.json and is not committed. Version and activation response counter byte at characteristic-value offset 10 is masked, based on differences at corresponding connection-06 frames 3887/3892. Other response bytes must match before proceeding. Cross-check: external THR-II controller source commit 343228a4fe343eb2f533c3828da6708f6fd1e08b, ParseSysEx.cpp lines 381 onward identifies matching activation pair (USB framing differs, so actual transmitted bytes come only from our BLE capture). No other initialization/state/save commands are sent.

mac-replay-02a: scan timed out without transmitting. macOS retained a connection to LE_THRII; retrieveConnectedPeripherals found it in the next attempt. mac-replay-02b reused it, subscribed successfully and sent identity request at UTC 21:51:42. No identity response observed yet.

mac-replay-02b timed out at UTC 21:52:28 after identity request only; no notification received, so no activation and no slot write. mac-replay-02c added characteristic read before subscription: read completed with 5 bytes at 21:52:42; identity request sent 21:52:44; no reply; timed out 21:53:30. Activation and slot stages were not reached. Both attempts reused the OS-held connection. All probe and capture processes now stopped. Need a fresh amplifier link to distinguish stale macOS/amp connection state from transport/initialization issues; do not claim successful replay or necessity of specific remaining commands.

## mac-replay-03: success confirmed

After user power-cycled amplifier, macOS automatically re-established the link. Probe reused OS-connected LE_THRII at UTC 21:56:46. Handshake read returned 5 bytes and subscription succeeded. At 21:56:47 identity response, version response, and activation response each matched the captured profile (only the documented counter is masked). Then one slot-1 Write Command was queued; amplifier returned a short acknowledgment and two state-change notifications. No secondary dump/query or other initialization was sent. Probe disconnected/exited at 21:56:56. User explicitly confirmed slot 1 selected. Capture mac-replay-03.pcap SHA256 `f67f4a582b4b83f3d0026aea6b86b3b3bfac021cd6dfed209f3011e00b7adb65` is diagnostic radio data, not a decrypted ATT record of this system-held connection. Evidence for replay is CoreBluetooth callbacks and visual confirmation. All capture/probe processes stopped.

### 2026-10-28: Mac slot sequence

At the user's request, ran `.tools/replay-slot --slots 1,2,3,4,5 --init-profile private/activation-profile.json` in one connection after three initialization steps with matching responses. Transmission times (UTC): slot 1 at 22:03:49; 2 at 22:03:57; 3 at 22:04:06; 4 at 22:04:14; 5 at 22:04:23. Each received a short response and two state-change notifications. User visual confirmation was still pending at this checkpoint. No radio capture or preset-save commands for this experiment.

The script now accepts `--slots` with a list of 1–5, initializes once and waits eight seconds after each command. Single-slot `--slot` mode is retained.

### 2026-10-28: visually confirmed Mac repeat

Repeated `--slots 1,2,3,4,5` in one connection after three initialization steps with matching responses. Transmission times UTC: slot 1 at 22:05:48; 2 at 22:05:56; 3 at 22:06:04; 4 at 22:06:13; 5 at 22:06:21. Each command received a short response and two state notifications. The process exited with code 0 at 22:06:30 UTC. The user explicitly confirmed all five visible transitions. Final slot: 5. No radio capture or preset-save commands.

## iPhone Gain capture — 2026-10-30

`captures/iphone-02.pcap`: initial iPhone pairing and readable ATT/SysEx captured; later readable traffic stops around 130.31 s despite continuing radio capture. Subsequent user movements cannot be attributed to those earlier packets. Capture stopped; pairing secrets remain in ignored local capture.

`captures/iphone-03.pcap`: target selected after discovery at about 49.89 s, CONNECT_IND frame 5477 at 50.225538 s. Encryption restart followed by readable ATT and application handshake. User confirms initial Gain 60, then moves only Gain to 50. Fifteen Write Commands at frames 22336–23060 (113.521558–115.929186 s) capture this movement, each containing two SysEx messages. Final write frame 23060 has responses at 23071 and 23079. Second SysEx consistently contains packed bytes `0c0100005800`; association with Gain follows this controlled user action, exact field semantics/value encoding not yet established. Final raw ATT value: `b6aaf000010c24004d003e000007000a0000001000000000000000000000aaf7abf000010c24004d003f00000f000c010000580000010004000000726500013f0000000000abf7`. No replay or preset save performed. Capture continues at time of this note.

### iPhone slot 1 comparison

User selected stored amplifier slot 1 in THR Remote. iphone-03 frame 55407 at 238.133176 s: `b18df000010c24004d010700000b000e00000004000000000000000000008df7`. Compared with AIRSTEP slot-1 template in protocol.md, the only differing BLE-value offsets are 0, 1 and 30 (BLE-MIDI header/timestamps), and 10 (07 vs 00, observed message counter position). Slot payload remains zero. iPhone additionally sends frame 55437, then dump request 55459 at 238.290724 s; dump-request content matches the pedal's additional request after removing timestamps and counter. Thus slot-1 selection uses the same observed command structure; further slots still require controlled capture.

### iPhone slots 2 → 1 → 2 → 3 → 4 → 5

User completed requested sequence. iphone-03 selection frames: 69428 (290.448157 s, slot 2), 70935 (295.780923, slot 1), 72734 (302.125454, slot 2), 75057 (310.533974, slot 3), 76624 (316.084232, slot 4), 78291 (322.009518, slot 5). All six selection values match the AIRSTEP slot template after masking BLE-MIDI offsets 0/1/30 and observed counter offset 10; slot index at offset 24 is 1,0,1,2,3,4. Each is followed by the additional iPhone request (opcode bytes 0f) and matching pedal-style dump request about 0.150–0.164 s after selection. Pedal dump request was about 0.45–0.60 s after selection. Additional iPhone reads follow. Same slot-selection payload across all five slots established; complete session traffic is not identical. No writes were replayed by this experiment.

