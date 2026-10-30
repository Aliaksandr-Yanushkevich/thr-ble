# Yamaha THR10II: BLE preset control

## Confirmed result

A standard AIRSTEP connects directly to LE_THRII. The user configured A–E to select slots 1–5. Two A → B → A → B → C → D → E experiments after reconnection produced identical commands. In the Mac test, the user confirmed slot 1 was selected after initialization. Saved presets and amplifier/pedal firmware were unchanged. Effects were excluded from the original task by the user.

## Connection and GATT

AIRSTEP is the initiator/central; THR is the advertiser/peripheral: CONNECT_IND in connection-05 frame 1162 and connection-06 frame 3799. The initial unsuccessful connection-01 frame 3199 is not used for exact parameters: decoded fields are suspicious and connection following failed.

BLE-MIDI service: `03b80e5a-ede8-4b33-a751-6ce34ec4c700`.
MIDI I/O characteristic: `7772e5db-3868-4112-a1a9-f2669d106bf3`.
The UUIDs and format match [BLE-MIDI 1.0](https://microsoft.github.io/MIDI/kb/ble-midi-transport-architecture/).

Both captures use value handle 0x000c and CCCD 0x000d. These are observations from specific sessions, not permanent identifiers. The Mac discovers the service and characteristic by UUID. Characteristic properties 0x1e: Read, Write, Write Without Response, Notify. Service discovery: connection-05 frames 1176/1179, characteristic 1187; connection-06 frames 3817/3822/3843. Pedal MTU request: 247; amplifier response: 96 (connection-05 frames 1163/1168). Effective ATT MTU is 96, allowing up to 93 value bytes in a typical ATT write.

The pedal subscribes with a Write Request to the CCCD containing `01 00` (connection-05 frame 1230, response 1235). Commands use Write Command (ATT 0x52); responses use Handle Value Notification (0x1b). Indications were not established in the examined sequence.

## BLE-MIDI and SysEx

The characteristic value contains a BLE-MIDI header, timestamp and MIDI stream. Complete messages include `80 80 f0 … 80 f7`: the first 80 is the header, the second is the timestamp before F0, and the penultimate byte is the timestamp before F7. SysEx continuations begin with header 80 followed immediately by MIDI data; do not unconditionally drop the first two bytes of every notification. A value can contain two SysEx messages: connection-05 frame 1253.

The timestamp is 13 bits: `((header & 0x3f) << 7) | (timestamp & 0x7f)`. It is zero in all successfully parsed messages from both pedal experiments. Action times therefore come from capture timestamps, not MIDI timestamps. These measure command transmission, not independently measured button contact times.

`scripts/reassemble-sysex.py` reassembles the observed SysEx stream separately by direction and records all contributing frame numbers. connection-05: 95 complete messages, 21 pedal → amplifier and 74 in the reverse direction, no parser errors. connection-06: 91 complete messages and 4 diagnostic errors/gaps; damaged response fragments are not reconstructed by guessing. The script deliberately handles SysEx only and is not a full MIDI running-status decoder.

## Slot selection

Complete BLE characteristic value, 32 bytes:

```text
80 80 f0 00 01 0c 24 00 4d 01 00 00 00 0b 00 0e
00 00 00 04 00 00 00 00 NN 00 00 00 00 00 80 f7
```

NN is the slot number minus 1, at offset 24 from the beginning of the BLE value (zero-based). Removing the BLE-MIDI header/timestamps yields a 29-byte SysEx. The internal semantics of every other field have not been established and cannot be inferred solely from field names in a third-party project.

| Action | Characteristic UUID | GATT | Value bytes | Initialization | Response / evidence |
|---|---|---|---|---|---|
| Slot 1, A | 7772e5db-3868-4112-a1a9-f2669d106bf3 | Write Command | Template, NN=00 | Working sequence below | connection-05 frames 8533/9124; connection-06 frames 5357/5959; Mac: user confirmed |
| Slot 2, B | Same | Write Command | Template, NN=01 | Same; minimality unproven | 05 frames 8814/9405; 06 frames 5666/6320 |
| Slot 3, C | Same | Write Command | Template, NN=02 | Same | 05 frame 9687; 06 frame 6590 |
| Slot 4, D | Same | Write Command | Template, NN=03 | Same | 05 frame 10008; 06 frame 6907 |
| Slot 5, E | Same | Write Command | Template, NN=04 | Same | 05 frame 10322; 06 frame 7198 |

A and B are byte-identical on repeated selections within a connection; all seven commands match between connections. The index does not behave like a counter: it repeats when returning to A/B. The user visually confirmed the slots in the first experiment.

After each selection, the pedal sends the same additional command about 0.45–0.60 seconds later:

`8080f000010c24004d010000000b000c0000000400003c007f7f7f7f000080f7`

Examples: connection-05 frames 8567/8839, connection-06 frames 5391/5698. Fragmented state dumps follow. The exact purpose of this additional command is unproven. Mac switching did not require it: after initialization, only one slot-selection command was sent and the visible slot changed. Selection responses include a short acknowledgment and state-change notifications (05 frames 8540/8549/8555; similar callbacks on Mac).

## Initialization and Mac validation

First experiment: read/subscribe and one slot-1 command without SysEx initialization. The user reported the amplifier remained on 5. This does not isolate the cause; connection state could matter. The successful sequence below was tested after restarting the amplifier.

1. Discover the service/characteristic by UUID; read the characteristic and enable notifications. The Mac received 5 bytes on read; their semantics were not investigated. The necessity of the read is unproven.
2. Send Universal Identity Request, BLE value `8080f07e7f060180f7`. Wait for the matching response (05 frames 1232/1241; 06 frames 3867/3873).
3. Send the version query from 05 frame 1247 (=06 frame 3878). Wait for response 05 frame 1262 / 06 frame 3887, matching all bytes except the observed counter at offset 10.
4. Send the captured activation SysEx pair in one BLE value (05 frame 1253 =06 frame 3884). Wait for response 05 frame 1266 /06 frame 3892, masking only that same counter. Activation data is in Git-ignored `private/activation-profile.json`.
5. Send one slot-1 command using Write Without Response. Other initialization commands, dump requests and the additional post-selection command are not sent.

Activation agrees with the [third-party THR-II controller source](https://github.com/martinzw/THRII-direct-USB-pedalboard/blob/343228a4fe343eb2f533c3828da6708f6fd1e08b/src/ParseSysEx.cpp#L381). This is supplementary interpretation; transmitted BLE bytes come only from our captures. The amplifier version in the text response is `1.5.0.0.b`.

Successful run: 2026-10-28 21:56:46–21:56:56 UTC. macOS had already restored the connection after the amplifier restart, so the probe used `retrieveConnectedPeripherals`. All three stages received matching responses at 21:56:47; then one slot-1 command was sent. A short acknowledgment and two state notifications followed. The user confirmed slot 1 was selected. A Write Command normally has no ATT Write Response; evidence consists of notifications and visual confirmation, not the API returning.

The Mac radio capture does not expose decrypted payloads: successful replay is evidenced by CoreBluetooth callbacks and user confirmation. Radio frame numbers for the Mac commands are not claimed. `mac-replay-03.pcap` is a diagnostic radio recording, not an equivalent readable Mac GATT trace.

## Encryption and quality

connection-05/06 include pairing and LL_START_ENC; for example, 05 frames 1188/1191/1197/1198/1201. Readable ATT follows. The link is therefore encrypted even though the sniffer presents this captured exchange in cleartext. This does not establish decryptability for every future connection. Captures contain pairing secrets and remain local, outside Git.

CRC errors, retransmissions and undecoded frames occur. The second SysEx analysis explicitly reports incomplete/invalid responses. Zero packet loss is not claimed. Wireshark Not acknowledged is not itself a loss counter. The first capture contains CONNECT_IND and subsequent data-channel traffic; all sequence commands and their responses can be compared. Mac captures include bad MIC; the pedal pairing method is established below, while Mac pairing was not separately classified.

Channel Map is the set of enabled channels; the hopping algorithm and connection parameters determine their sequence. Knowing the map does not decrypt the payload.

## Unknowns and limits

The minimal necessity of every step in the working handshake is unproven. Other firmware versions, other amplifiers, long-term operation, automatic reconnect and multiple clients have not been validated. The Mac was initially tested only on a transition to slot 1; slots 2–5 were established in two pedal experiments before the later Mac test below. The full state-dump format and THR SysEx bit packing remain unexplored. Effect and preset-save commands were outside the original task.

### Additional Mac validation for slots 1–5

On 2026-10-28 at 22:05:48–22:06:21 UTC, slots 1 → 2 → 3 → 4 → 5 were selected in one CoreBluetooth connection after one initialization, with approximately 8-second pauses. The amplifier responded to every command; the user visually confirmed all five transitions. Mac replay is therefore verified for all five slots. This repeat had no concurrent radio capture; details are in the experiment log.

### Pairing classification from both original captures

Checked Pairing Request/Response: connection-05 frames 1165/1170, connection-06 frames 3802/3807. Both directions have AuthReq=0x01: SC=0, MITM=0, bonding=1; IO Capability=No Input, No Output; no OOB; Max Encryption Key Size=16. This is LE Legacy Pairing using Just Works, not LE Secure Connections. TK=0; the random values transmitted during pairing let a passive observer calculate the STK and session key. This explains decryption of a full pairing capture without brute-forcing AES. The conclusion applies to these two AIRSTEP–THR connections, not automatically to the Mac or any other client. See Bluetooth SIG Security Manager Specification, LE legacy pairing — Just Works. Keys are not copied into these notes.

### iPhone comparison: 2026-10-30

THR Remote slot-selection commands for all five slots match the AIRSTEP template after excluding BLE-MIDI header/timestamps (offsets 0, 1, 30) and the observed message counter (offset 10). The controlled sequence 2 → 1 → 2 → 3 → 4 → 5 is recorded in `iphone-03.pcap`; frame numbers are in the experiment log. iPhone sends additional queries and requests a state dump about 0.150–0.164 seconds after selection, versus about 0.45–0.60 seconds for AIRSTEP. Slot-selection content matches; full session traffic differs.
