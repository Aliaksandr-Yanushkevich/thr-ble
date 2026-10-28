#!/usr/bin/env python3
"""Select a discovered Nordic extcap device after its toolbar ADD event.

Uses Wireshark's extcap toolbar wire protocol; never opens the serial port
itself. Ctrl-C stops the single official capture process. Raw output stays
in the requested (previously nonexistent) capture file.
"""
import argparse
import os
from pathlib import Path
import select
import signal
import struct
import subprocess
import tempfile


def message(control, command, payload=b''):
    return b'T' + (len(payload) + 2).to_bytes(3, 'big') + bytes([control, command]) + payload


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('output', type=Path)
    ap.add_argument('--name', default='LE_THRII')
    ap.add_argument('--port', default='/dev/tty.usbmodem1101')
    args = ap.parse_args()
    shim = Path.home()/'.local/lib/wireshark/extcap/nrfutil-ble-sniffer-shim'
    # Reserve output without overwriting any earlier experiment.
    with args.output.open('xb'):
        pass
    with tempfile.TemporaryDirectory(prefix='thr-extcap-') as tmp:
        paths = [Path(tmp)/n for n in ('control-in', 'control-out')]
        for p in paths:
            os.mkfifo(p, 0o600)
        fds = [os.open(p, os.O_RDWR | os.O_NONBLOCK) for p in paths]
        proc = subprocess.Popen([str(shim), '--capture', '--extcap-interface', args.port,
            '--fifo', str(args.output.resolve()), '--extcap-control-in', str(paths[0]),
            '--extcap-control-out', str(paths[1])], start_new_session=True)
        selected = False
        buf = b''
        try:
            os.write(fds[0], message(0, 1, b' '))
            os.write(fds[0], message(1, 1, b'0'))
            os.write(fds[0], message(3, 1, b'37,38,39'))
            os.write(fds[0], message(255, 0))  # Toolbar initialized.
            while proc.poll() is None:
                if not select.select([fds[1]], [], [], 1)[0]:
                    continue
                buf += os.read(fds[1], 65536)
                while len(buf) >= 4:
                    length = int.from_bytes(buf[1:4], 'big')
                    if buf[0] != ord('T') or length < 2:
                        raise RuntimeError('Unexpected extcap control framing')
                    if len(buf) < 4 + length:
                        break
                    control, command = buf[4:6]
                    payload = buf[6:4+length]
                    buf = buf[4+length:]
                    if control == 0 and command == 2 and not selected:
                        print('Device item:', repr(payload), flush=True)
                        value, _, label = payload.partition(b'\0')
                        if args.name.encode() in label:
                            print('Discovered target:', label.decode(errors='replace'), flush=True)
                            os.write(fds[0], message(0, 1, value))
                            selected = True
                            print('FOLLOW selection sent:', value.decode(errors='replace'), flush=True)
                    elif control == 6:
                        text = payload.decode(errors='replace')
                        if any(t in text.lower() for t in ('follow', 'error', 'connect')):
                            print(text.strip(), flush=True)
            raise SystemExit(proc.returncode)
        except KeyboardInterrupt:
            print('Stopping capture.', flush=True)
        finally:
            if proc.poll() is None:
                os.killpg(proc.pid, signal.SIGINT)
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid, signal.SIGTERM)
                    proc.wait(timeout=5)
            for fd in fds:
                os.close(fd)


if __name__ == '__main__':
    main()
