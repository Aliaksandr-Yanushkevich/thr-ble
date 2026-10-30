# Environment and hardware

Initial check: 2026-10-28, stages 1–2 before flashing or capture. Initial findings are retained below as history; the next section records the later state.

## State after entering the bootloader

### Experimental firmware: startup confirmed

With user authorization for the experiment, prepared UF2 from official Dongle BIN 4.1.1 at `0x1000`; `scripts/prepare-sniffer-uf2.py` checks vectors and range. Written addresses: `[0x1000,0x12000)`; MBR/bootloader/UICR excluded. Part of SoftDevice was replaced. BIN SHA256 `51e557ba329232c66ca7420279cb16354b842d6ac2ea66ceb8f1b99f7a396905`, UF2 SHA256 `bb8f0a497a298e1710c4a8fe3a3dca11f41dd74b3f1b8c8daef9e84f83c43277`.

Ran `cp private/sniffer-dongle-4.1.1-at-1000.uf2 /Volumes/NICENANO/SNIFFER.UF2` with sandbox approval. The board restarted and NICENANO disappeared. USB and `device list` show `nRF Sniffer for Bluetooth LE`, port `/dev/tty.usbmodem1101`, traits nordicUsb/serialPorts/usb. Outside the sandbox, `tshark -D` detects the same interface. Radio reception passed: see smoke-01 in experiments.md. Connection following, stability and bootloader recovery were not yet verified at this checkpoint.

Do not copy UF2 again unnecessarily. Working first-capture command:

```sh
.tools/nrfutil ble-sniffer sniff --port /dev/tty.usbmodem1101 --output-pcap-file captures/sniffer-smoke-01.pcap
```

Stopped with Ctrl-C; the process exited and released the port. Each subsequent capture must use a new filename. In the sandbox, `tshark -D` may miss the sniffer because extcap cannot write to `~/.nrfutil/logs`; outside the sandbox the interface is detected. Saved-file analysis with tshark works in the sandbox.

Read `/Volumes/NICENANO/INFO_UF2.TXT` without writing to the device:

```text
UF2 Bootloader 0.7.0 lib/nrfx (v2.0.0) lib/tinyusb (0.12.0-145-g9775e7691) lib/uf2 (remotes/origin/configupdate-9-gadbb8c7)
Model: nice!nano
Board-ID: nRF52840-nicenano
Date: Jul 13 2022
SoftDevice: S140 6.1.1
```

- Installed official universal macOS nRF Util in Git-ignored `.tools/nrfutil`, version 8.2.1, host aarch64-apple-darwin.
- Modules: ble-sniffer 0.21.0, device 2.23.0; bootstrap succeeded.
- Bluetooth LE Sniffer 4.1.1 images are in the expected firmware directory.
- `device list` detects nice!nano, port `/dev/tty.usbmodem1101`, traits `serialPorts, usb`. This does not establish Nordic DFU programming support.
- J-Link was absent and was not installed; it was not required at this stage.

Commands run (required sandbox approval for network and user-directory access):

```sh
curl --fail --location https://files.nordicsemi.com/artifactory/swtools/external/nrfutil/executables/universal-apple-darwin/nrfutil -o .tools/nrfutil
chmod +x .tools/nrfutil
.tools/nrfutil --version
.tools/nrfutil --help
.tools/nrfutil install ble-sniffer
.tools/nrfutil install device
.tools/nrfutil list
.tools/nrfutil ble-sniffer bootstrap --help
.tools/nrfutil ble-sniffer sniff --help
.tools/nrfutil ble-sniffer bootstrap
.tools/nrfutil device list
```

### Compatibility limits

**Clarification after inspecting 0.7.0 source:** the earlier conclusion below about not simply preserving SoftDevice remains valid, but UF2 supports replacing SoftDevice with an application that does not use it. `src/usb/uf2/ghostfat.c` treats SoftDevice as part of the application area; `uf2cfg.h` defines USER_FLASH_START=MBR_SIZE (`0x1000`); `bootloader_app_start()` in `lib/sdk11/components/libraries/bootloader_dfu/bootloader.c` supports starting without SD from `MBR_SIZE`. Thus experimentally packaging the stock Dongle BIN at `0x1000` is possible without relocating code or writing MBR/bootloader. Hardware compatibility had not yet been established. Source: https://github.com/adafruit/Adafruit_nRF52_Bootloader/tree/0.7.0 .

The user authorized trial and error. Saved CURRENT.UF2, INFO_UF2.TXT and INDEX.HTM from the volume to Git-ignored `private/board-backups/`. CURRENT.UF2: SHA256 `b7d0012ebf408f5a26216fc320e9a7823dea8489f6d51090d25979ff0c9de40e`, 3728 blocks, addresses `[0x1000,0xea000)`, family/board ID `0x239a00b3`. This is not a complete bootloader/MBR/UICR image or a recovery guarantee. Prepare the experimental file with `python3 scripts/prepare-sniffer-uf2.py`; output stays in private/. The plan was to write the application from `0x1000`, replacing part of SoftDevice without touching MBR or bootloader. Source indicates double-reset should remain available, but the installed build may differ.

Inspected the user-provided listing: https://www.aliexpress.com/item/1005007557383132.html . Seller title: NRF52840 Development Board Compatible With Nice Nano V2.0 Bluetooth Charging Management Pro Micro. IC GOICIC photos show USB-C, a PCB antenna and four labeled rear pads `VDD`, `DIO`, `CLK`, `GND` (SWD access). Source image: https://ae-pic-a1.aliexpress-media.com/kf/S47c23545e5e3492fa4c1243f62cb25c2C.jpg . The exact PCB revision and chip marking are illegible; correspondence with the delivered board was not yet confirmed. Pads make SWD an access option but do not guarantee read/write access under protection or establish image compatibility.

Practical options at that stage: a supported PCA10059, or separate SuperMini investigation confirming photos, SWD adapter availability and memory map. No image preserving the SuperMini bootloader had yet been verified. No programmer purchase or recover/erase operation was performed or proposed as mandatory.

The PCA10059 ZIP contains a manifest and Nordic DFU `.dat`/`.bin`, not UF2. The BIN reset-handler vector is `0xab1d` (code address `0xab1c`), below the typical Adafruit S140 v6 application region (`0x26000`, according to bootloader documentation). Converting BIN to UF2 and moving it to `0x26000` does not fix absolute code addresses, so this relocation is not a verified installation method. The DK HEX also contains data starting at `0x0`.

At the earlier planning stage, preserving the existing bootloader/SoftDevice and simply copying the stock image could not be considered compatible. Options were supported PCA10059 hardware or investigating an adapted image for the exact SuperMini, memory map and bootloader. The latter still required exact revision/photos and a recovery-method check; installing or buying an SWD programmer was not yet required. No files had been written to NICENANO at that checkpoint.

Reproduce image inspection with `python3 scripts/inspect-firmware.py`.
UF2, address and SoftDevice reference: https://github.com/adafruit/Adafruit_nRF52_Bootloader#making-your-own-uf2 .

### Original planned capture command (historical; do not start blindly)

After obtaining a working sniffer and verifying its port:

```sh
.tools/nrfutil ble-sniffer sniff --port <PORT> --follow-by-name LE_THRII --output-pcap-file captures/session-01.pcap
```

At this stage LE_THRII still needed advertising confirmation; select the device address if ambiguous. Do not run a simultaneous Wireshark capture on the same port. Later experiments use `scripts/capture-follow.py` to select the target after discovery.

## Initial local findings

- Apple M2, arm64; macOS 26.6.2, build 25G83.
- Wireshark/tshark 4.6.9; `/Applications/Wireshark.app/Contents/MacOS/tshark`.
- Python 3.9.6; Git 2.50.1 (Apple Git-155).
- `brew` and `nrfutil` were absent from PATH; nrfutil was also absent from checked standard directories and Downloads.
- `tshark -D`: no Nordic interface.
- Personal Extcap: `~/.local/lib/wireshark/extcap`.
- `ioreg -p IOUSB -w 0`: VIA USB2/USB3 hubs, ASIX AX88179A and VIA USB Billboard Device. The nRF board was not identified.
- Serial ports: Bluetooth-Incoming-Port, SparkNEOAudio, debug-console; no board USB port.
- `system_profiler SPUSBDataType` returned no data; IORegistry was used.
- Sandbox denied process listing through `ps`; THR Remote closure had not been verified.

## Initial identification requirements

Recheck on 2026-10-28: the user identified SuperMini nRF52840. USB then appeared as `Feather nRF52840 Express`, Adafruit, VID:PID `239a:8029`, port `/dev/cu.usbmodem1101`. No UF2 volume in `/Volumes`. This identifies the current USB firmware, not the board model or bootloader version. The next step was a standard double-reset if a labeled RESET button was present, then reading `INFO_UF2.TXT` without writing files. Adafruit documents two resets within 500 ms: https://github.com/adafruit/Adafruit_nRF52_Bootloader#how-to-use . SuperMini is absent from Nordic's officially supported board list; PCA10059 image compatibility was unproven.

Required: photos of both nRF-board sides with readable markings or a link to the exact model, bootloader information, and a USB data cable. USB descriptors alone do not establish PCA10059 compatibility.
The AIRSTEP version/mode and actual pedal → amplifier connection topology were initially unknown.

## Original installation plan (completed; see above)

Official macOS nRF Util build: universal-apple-darwin. Use the current binary rather than the Python nrfutil package.
After download, check `--version` and `--help`, then:

```sh
nrfutil install ble-sniffer
nrfutil install device
nrfutil ble-sniffer --help
nrfutil ble-sniffer bootstrap --help
nrfutil ble-sniffer bootstrap
nrfutil device list
```

Installation writes outside the workspace and may require sandbox approval.
Select firmware only after identifying the board, wiring and bootloader. No erase/recover before that.
Expected directory: `~/.nrfutil/share/nrfutil-ble-sniffer/firmware/`; the actual path and versions were initially unverified.

| Board | Official image |
|---|---|
| PCA10059 nRF52840 Dongle | `sniffer_nrf52840dongle_nrf52840_*.zip` |
| PCA10056 nRF52840 DK | `sniffer_nrf52840dk_nrf52840_*.hex` |
| PCA10100 nRF52833 DK | `sniffer_nrf52833dk_nrf52833_*.hex` |
| PCA10040 nRF52 DK | `sniffer_nrf52dk_nrf52832_*.hex` |

The capture command was to be recorded after checking installed `sniff --help` and detecting the interface. Only one program can own the port at a time.

## Official references

- https://docs.nordicsemi.com/r/bundle/nrfutil/page/guides/installing.html/installing-nrf-util-from-the-web-default
- https://docs.nordicsemi.com/r/bundle/nrfutil/page/guides/installing_wireshark.html/installing-nrf-util-plugins
- https://docs.nordicsemi.com/r/bundle/nrfutil/page/nrfutil-ble-sniffer/nrfutil-ble-sniffer.html/ble-sniffer-bootstrap
- https://academy.nordicsemi.com/courses/bluetooth-low-energy-fundamentals/lessons/lesson-6-bluetooth-le-sniffer/topic/nrf-sniffer-for-bluetooth-le/?version=v3.4.1

## Mac slot replay probe

Native CoreBluetooth; no Python Bluetooth dependencies required. Build (from repository root):

```sh
swiftc -module-cache-path private/swift-module-cache scripts/replay-slot.swift -o .tools/replay-slot -Xlinker -sectcreate -Xlinker __TEXT -Xlinker __info_plist -Xlinker scripts/macos-ble-info.plist
.tools/replay-slot --help
```

With pedal OFF, `.tools/replay-slot --slot 1` connects to LE_THRII, discovers the MIDI characteristic by UUID, subscribes, and queues one slot-selection write. It omits the pedal initialization as a controlled sufficiency test. At the initial checkpoint it was not yet validated as a working preset switch; see the successful profile-based test below. Requires macOS Bluetooth permission; no fixed GATT handle. Capture concurrently with scripts/capture-follow.py (separate radio hardware, no serial-port competition). Logs/exports and compiled binaries remain private/ignored.

## Verified Mac execution

The successful test followed an amplifier restart with the pedal off. Initialization responses and visible slot-1 selection were confirmed. The profile is specific to the captured device/version; validate before using it with different firmware.

```sh
# If private/activation-profile.json does not exist yet:
python3 scripts/prepare-activation-profile.py

# Build with a macOS Bluetooth permission description:
swiftc -module-cache-path private/swift-module-cache scripts/replay-slot.swift -o .tools/replay-slot -Xlinker -sectcreate -Xlinker __TEXT -Xlinker __info_plist -Xlinker scripts/macos-ble-info.plist

# Pedal off. Performs the handshake and one slot selection:
.tools/replay-slot --slot 1 --init-profile private/activation-profile.json
```

Without `--init-profile`, the diagnostic variant omits SysEx initialization; it did not switch the slot in the first experiment. The successful variant uses the profile. If macOS already holds a connection, the application reuses the system connection with the MIDI service and LE_THRII name. Application exit does not guarantee physical closure of the system BLE connection.

Analyze without modifying captures:

```sh
python3 scripts/find-preset-candidates.py captures/connection-05.pcap
python3 scripts/export-att.py captures/connection-05.pcap > private/connection-05-att.tsv
python3 scripts/reassemble-sysex.py captures/connection-05.pcap > private/connection-05-sysex.jsonl
```

`reassemble-sysex.py` returns nonzero for damaged/incomplete messages; for connection-06 this is expected diagnostic output, not permission to ignore errors. Capture-follow owns one serial port through the official extcap shim. Do not run another sniffer/Wireshark instance on that port simultaneously. In Mac tests the sniffer uses a separate radio; CoreBluetooth does not compete for its USB port.
