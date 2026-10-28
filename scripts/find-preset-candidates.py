#!/usr/bin/env python3
"""Find the experimentally observed slot-select byte template in ATT writes.

Does not prove slot semantics, remove retransmissions, or reconstruct SysEx.
Byte offset 24 is zero-based in the original characteristic value.
"""
import argparse
import json
import subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('capture')
p.add_argument('--tshark', default='/Applications/Wireshark.app/Contents/MacOS/tshark')
a = p.parse_args()
template = bytes.fromhex('8080f000010c24004d010000000b000e000000040000000000000000000080f7')
fields = ['frame.number', 'frame.time_epoch', 'frame.time_relative', 'btatt.handle', 'btatt.value']
cmd = [a.tshark, '-r', a.capture, '-Y', 'btatt.opcode == 0x52', '-T', 'fields']
for field in fields:
    cmd += ['-e', field]
result = subprocess.run(cmd, check=True, capture_output=True, text=True)
found = []
for line in result.stdout.splitlines():
    frame, epoch, relative, handle, value = line.split('\t')
    data = bytes.fromhex(value)
    if len(data) != len(template) or data[:24] != template[:24] or data[25:] != template[25:]:
        continue
    found.append(dict(frame=int(frame), epoch=epoch, relative=relative,
                      handle=handle, candidate_index=data[24], value=value))
print(json.dumps(found, indent=2))
