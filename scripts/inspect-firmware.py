"""Read-only inspection of the official sniffer archive; never writes firmware."""
import struct
import zipfile
from pathlib import Path

firmware = Path.home() / ".nrfutil/share/nrfutil-ble-sniffer/firmware"
for archive in sorted(firmware.glob("*52840dongle*.zip")):
    print(archive.name)
    with zipfile.ZipFile(archive) as source:
        print("files:", source.namelist())
        print(source.read("manifest.json").decode())
        for name in source.namelist():
            if name.endswith(".bin"):
                data = source.read(name)
                words = struct.unpack("<8I", data[:32])
                print(name, "bytes:", len(data))
                print("vector words:", " ".join(hex(word) for word in words))
                print("reset handler (Thumb bit cleared):", hex(words[1] & ~1))
