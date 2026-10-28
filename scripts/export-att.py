#!/usr/bin/env python3
"""Export ATT operations with packet numbers, timestamps and raw ATT values.

Output may contain amplifier state; keep exports under private/. Does not
export SMP pairing keys. Input capture is never modified. Values are BLE
characteristic bytes, not yet reconstructed MIDI messages.
"""
import argparse
import subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('capture')
p.add_argument('--tshark', default='/Applications/Wireshark.app/Contents/MacOS/tshark')
a = p.parse_args()
fields = ['frame.number', 'frame.time_epoch', 'frame.time_relative',
          'nordic_ble.flags', 'btatt.opcode', 'btatt.handle', 'btatt.value']
cmd = [a.tshark, '-r', a.capture, '-Y', 'btatt', '-T', 'fields',
       '-E', 'header=y', '-E', 'separator=/t', '-E', 'quote=d']
for field in fields:
    cmd += ['-e', field]
subprocess.run(cmd, check=True)
