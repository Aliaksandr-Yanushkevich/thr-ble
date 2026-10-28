#!/usr/bin/env python3
"""Reassemble the SysEx-only BLE-MIDI streams observed in these THR captures.

Not a general MIDI decoder: unsupported channel/running-status messages raise
an error instead of guessing. Output may contain preset state: keep private.
BLE-MIDI header/timestamp rules: Microsoft MIDI transport architecture,
https://microsoft.github.io/MIDI/kb/ble-midi-transport-architecture/
"""
import argparse
import json
import subprocess
import sys


class Stream:
    def __init__(self):
        self.data = bytearray()
        self.frames = []
        self.timestamps = []

    def packet(self, value, frame):
        if not value or value[0] & 0xc0 != 0x80:
            raise ValueError('invalid BLE-MIDI header')
        i = 1
        complete = []
        if self.data:
            self.frames.append(frame)
        while i < len(value):
            b = value[i]
            if self.data and b < 0x80:
                self.data.append(b); i += 1; continue
            # Outside SysEx, and before EOX or realtime, expect timestamp.
            if b < 0x80 or i + 1 == len(value):
                raise ValueError('missing timestamp/status or orphan continuation')
            timestamp = ((value[0] & 0x3f) << 7) | (b & 0x7f)
            status = value[i + 1]; i += 2
            if status == 0xf0 and not self.data:
                self.data = bytearray([status]); self.frames = [frame]
                self.timestamps = [timestamp]
            elif status == 0xf7 and self.data:
                self.data.append(status); self.timestamps.append(timestamp)
                complete.append(dict(frames=self.frames, timestamps=self.timestamps,
                                     midi=self.data.hex()))
                self.data = bytearray(); self.frames = []; self.timestamps = []
            elif status >= 0xf8:
                # Realtime is independent; it never closes SysEx.
                continue
            else:
                raise ValueError(f'unsupported/unexpected MIDI status {status:02x}')
        return complete


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('capture')
    ap.add_argument('--handle', default='0x000c', help='Observed value handle in this capture only')
    ap.add_argument('--tshark', default='/Applications/Wireshark.app/Contents/MacOS/tshark')
    args = ap.parse_args()
    fields = ['frame.number', 'btatt.opcode', 'btatt.value', 'nordic_ble.flags', '_ws.expert.message']
    cmd = [args.tshark, '-r', args.capture, '-Y',
           f'btatt.handle == {args.handle} && (btatt.opcode == 0x52 || btatt.opcode == 0x1b)', '-T', 'fields']
    for field in fields:
        cmd += ['-e', field]
    rows = subprocess.run(cmd, check=True, capture_output=True, text=True).stdout.splitlines()
    streams = {'0x52': Stream(), '0x1b': Stream()}
    errors = 0
    for row in rows:
        frame, opcode, payload, flags, expert = row.split('\t')
        stream = streams[opcode]
        if 'Retransmission' in expert:
            continue
        try:
            if not int(flags, 16) & 1:
                raise ValueError('CRC flag not OK')
            for message in stream.packet(bytes.fromhex(payload), int(frame)):
                message['direction'] = 'pedal_to_amp' if opcode == '0x52' else 'amp_to_pedal'
                print(json.dumps(message))
        except ValueError as exc:
            errors += 1; print(f'frame {frame}: {exc}', file=sys.stderr)
            streams[opcode] = Stream()
    for opcode, stream in streams.items():
        if stream.data:
            errors += 1; print(f'{opcode}: incomplete SysEx at EOF', file=sys.stderr)
    print(f'Parser errors/incomplete messages: {errors}', file=sys.stderr)
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
