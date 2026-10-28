"""Prepare an experimental UF2 for an Adafruit bootloader; never flash it.

Uses the official PCA10059 application at 0x1000 (no SoftDevice).
Does not claim SuperMini hardware compatibility. Replaces SoftDevice region.
"""
import hashlib
import struct
import zipfile
from pathlib import Path

source = Path.home() / ".nrfutil/share/nrfutil-ble-sniffer/firmware/sniffer_nrf52840dongle_nrf52840_4.1.1.zip"
target = Path("private/sniffer-dongle-4.1.1-at-1000.uf2")
base = 0x1000
with zipfile.ZipFile(source) as archive:
    data = archive.read("sniffer_nrf52840dongle_nrf52840_4.1.1.bin")
stack, reset = struct.unpack_from("<II", data)
assert 0x20000000 <= stack <= 0x20040000
assert reset & 1 and base <= (reset & ~1) < base + len(data)
count = (len(data) + 255) // 256
assert base + count * 256 < 0x26000  # no bootloader/UICR/old application writes
blocks = []
for number in range(count):
    payload = data[number * 256:(number + 1) * 256].ljust(256, b"\xff")
    header = struct.pack("<8I", 0x0A324655, 0x9E5D5157, 0x2000,
                         base + number * 256, 256, number, count, 0xADA52840)
    blocks.append(header + payload + bytes(220) + struct.pack("<I", 0x0AB16F30))
result = b"".join(blocks)
assert len(result) == count * 512
assert b"".join(block[32:288] for block in blocks)[:len(data)] == data
target.parent.mkdir(exist_ok=True)
target.write_bytes(result)
print("Official BIN SHA256:", hashlib.sha256(data).hexdigest())
print("UF2 SHA256:", hashlib.sha256(result).hexdigest())
print("Write addresses:", hex(base), "to", hex(base + count * 256), "exclusive")
print("Output:", target, "bytes:", len(result))
