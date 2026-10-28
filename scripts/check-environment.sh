#!/bin/sh
# Read-only checks; no radio capture, firmware changes or installation.
set -eu
uname -m
sw_vers
python3 --version
git --version
ioreg -p IOUSB -w 0
for port in /dev/cu.*; do
    [ ! -e "$port" ] || printf '%s\n' "$port"
done
if command -v nrfutil >/dev/null 2>&1; then
    nrfutil --version
    nrfutil --help
fi
tshark=/Applications/Wireshark.app/Contents/MacOS/tshark
if [ -x "$tshark" ]; then
    "$tshark" --version
    "$tshark" -G folders
    "$tshark" -D
fi
