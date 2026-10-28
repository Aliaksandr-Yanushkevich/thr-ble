#!/usr/bin/env python3
"""Extract the validated initialization profile from connection-05 and -06.

Run from the repository root. Output contains an activation code and must
remain in ignored private/. No capture is modified or key printed.
"""
import json
from pathlib import Path
import subprocess

TSHARK = '/Applications/Wireshark.app/Contents/MacOS/tshark'


def values(name):
    result = subprocess.run([TSHARK, '-r', f'captures/connection-{name}.pcap',
                             '-Y', 'btatt', '-T', 'fields', '-e', 'frame.number',
                             '-e', 'btatt.value'], check=True, capture_output=True, text=True)
    return dict(line.split('\t', 1) for line in result.stdout.splitlines())


a, b = values('05'), values('06')
profile = []
for tx1, rx1, tx2, rx2, mask in [(1232, 1241, 3867, 3873, []),
                                (1247, 1262, 3878, 3887, [10]),
                                (1253, 1266, 3884, 3892, [10])]:
    if a[str(tx1)] != b[str(tx2)]:
        raise SystemExit('Initialization writes differ; manual review required')
    first, second = bytearray.fromhex(a[str(rx1)]), bytearray.fromhex(b[str(rx2)])
    for index in mask:
        first[index] = second[index] = 0
    if first != second:
        raise SystemExit('Initialization responses differ outside counter; manual review required')
    profile.append(dict(tx=a[str(tx1)], rx=a[str(rx1)], mask=mask))
out = Path('private/activation-profile.json')
out.parent.mkdir(exist_ok=True)
# Exclusive creation avoids overwriting an earlier reviewed profile.
with out.open('x') as f:
    json.dump(profile, f, indent=2)
    f.write('\n')
out.chmod(0o600)
print(f'Validated three initialization stages; saved {out}')
