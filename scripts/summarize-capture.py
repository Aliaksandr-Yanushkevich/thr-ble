"""Read-only initial capture summary; does not infer commands or encryption."""
import argparse
import collections
import hashlib
import subprocess
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("capture", type=Path)
parser.add_argument("--tshark", default="/Applications/Wireshark.app/Contents/MacOS/tshark")
args = parser.parse_args()
command = [args.tshark, "-r", str(args.capture), "-T", "fields"]
for field in ("frame.number", "frame.time_relative",
              "btcommon.eir_ad.entry.device_name", "_ws.malformed"):
    command.extend(["-e", field])
result = subprocess.run(command, capture_output=True, text=True, check=True)
rows = [line.split("\t") for line in result.stdout.splitlines()]
print("SHA256:", hashlib.sha256(args.capture.read_bytes()).hexdigest())
print("Frames:", len(rows))
if rows:
    print("Last relative timestamp:", rows[-1][1])
names = collections.defaultdict(list)
malformed = []
for row in rows:
    if len(row) > 2 and row[2]:
        names[row[2]].append(row[0])
    if len(row) > 3 and row[3]:
        malformed.append(row[0])
for name, frames in names.items():
    print("Advertised name:", repr(name), "count:", len(frames), "first frames:", frames[:5])
print("Malformed-marked frames:", len(malformed), "first:", malformed[:10])
print("Names are raw observations; malformed/CRC-failed packets require separate checks.")
