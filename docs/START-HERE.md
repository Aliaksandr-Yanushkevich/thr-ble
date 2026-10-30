# How to use this repository

The project has three separate workflows: capture BLE traffic with an nRF52840, control the amplifier from a Mac, and control it with a button on an ESP32-C3. The sniffer is an investigation tool. Normal ESP controller operation does not require the Mac or sniffer.

Run all commands below from the repository root. USB paths are examples: check which board is connected and which port it uses. The same `/dev/cu.usbmodem1101` appeared for different boards at different times in the experiment logs.

## Which files belong to which device

| Task / device | Source or tool | Output / destination |
| --- | --- | --- |
| nRF52840: passive BLE sniffer | Official Nordic firmware; `scripts/prepare-sniffer-uf2.py` prepares an experimental variant | `private/sniffer-dongle-4.1.1-at-1000.uf2`, for the investigated nRF board with its UF2 bootloader |
| ESP32-C3: button and OLED controller | `firmware/thr-controller/` | `.tools/build-thr-controller/esp32-c3/`; upload through PlatformIO |
| ESP32-C3: standalone OLED and LED test | `firmware/display-test/` | `.tools/build-display-test/esp32-c3/`; upload through PlatformIO, replacing the controller on the board |
| Mac: direct THR control over Bluetooth | `scripts/replay-slot.swift` + `scripts/macos-ble-info.plist` | Executable `.tools/replay-slot`, run on the Mac |
| Mac: record traffic from the USB sniffer | `scripts/capture-follow.py` + Nordic extcap | Capture file `captures/<name>.pcap` |
| Mac: analyze recorded traffic | Python scripts in `scripts/`, Wireshark/tshark | Reports and exports under `private/` |

This repository does not contain Nordic Sniffer source code or firmware for the amplifier, iPhone, or AIRSTEP. The `firmware/` directory contains two ESP32-C3 projects. The Python and Swift tools in `scripts/` run on the Mac.

## Directory map

| Path | Contents |
| --- | --- |
| `README.md` | Investigation overview, diagram, results, and limitations |
| `docs/START-HERE.md` | This guide: devices, files, and workflows |
| `firmware/thr-controller/src/main.cpp` | Button input, BLE, THR initialization, slot selection, and reconnection |
| `firmware/thr-controller/src/display.h` | OLED driver and controller status display |
| `firmware/thr-controller/platformio.ini` | Board, dependencies, build settings, and controller upload port |
| `firmware/thr-controller/generate_profile.py` | Automatic build step converting the private JSON profile into a C++ header |
| `firmware/display-test/src/main.cpp` | Standalone OLED/LED test without BLE or button input |
| `firmware/display-test/platformio.ini` | Test build and upload settings |
| `scripts/` | Mac tools; each is described below |
| `notes/setup.md` | Mac and nRF setup history, bootloader details, Mac replay commands |
| `notes/esp32.md` | ESP identification, backup, display, and BLE diagnosis history |
| `notes/protocol.md` | Protocol details, initialization/slot-selection bytes, and frame references |
| `notes/experiments.md` | Experiment log and individual capture results |
| `captures/` | Local original radio captures; excluded from Git |
| `private/` | Local profile, board backups, UF2, logs, and exports; excluded from Git |
| `.tools/` | Local tools, Python venv, PlatformIO, build outputs, and Mac executable; excluded from Git |

The `notes/` directory records intermediate states. Statements such as “not yet verified” may describe an earlier checkpoint. For everyday use, start with this guide and the relevant firmware README.

## ESP32-C3: build and upload the controller

Investigated board: ESP32-C3 with SSD1306 72×40; SDA GPIO5, SCL GPIO6, address `0x3C`. Connect the button between GPIO3 and GND with power disconnected. GPIO8 drives the LED. See the [controller README](../firmware/thr-controller/README.md).

You need PlatformIO and a local `private/activation-profile.json`. In the existing workspace, PlatformIO is at `.tools/esp-venv/bin/pio`. For a fresh clone, prepare it as follows (installation and the first build require network access):

```sh
mkdir -p .tools private
python3 -m venv .tools/esp-venv
.tools/esp-venv/bin/python -m pip install platformio esptool==4.12.0
```

The profile is excluded from Git. The `thr-controller` build fails without it. It contains three initialization steps (`tx`, `rx`, `mask`) from the validated exchange. `scripts/prepare-activation-profile.py` can extract it only from the original local `captures/connection-05.pcap` and `connection-06.pcap`, using fixed frame numbers. It is not a general generator for new captures. A different exchange requires manual analysis and profile validation.

```sh
# Build only, without writing to the board:
.tools/esp-venv/bin/pio run -d firmware/thr-controller

# Upload to the connected ESP32-C3; substitute its port:
.tools/esp-venv/bin/pio run -d firmware/thr-controller -t upload --upload-port /dev/cu.usbmodem1101
```

PlatformIO uploads the bootloader, partition table, and application at the required offsets. The generated header is `.tools/build-thr-controller/esp32-c3/private_include/activation_profile.h`; the binary also contains the private profile.

For operation, turn off AIRSTEP and close THR Remote. If the ESP stays in SCAN, check whether the Mac holds a Bluetooth connection to THR; disabling Mac Bluetooth helped in our experiment. After READY, the first button press selects slot 1, followed by 2→3→4→5→1. The displayed number is the last locally sent selection, not a slot read back from the amplifier.

To test the display separately, replacing the controller:

```sh
.tools/esp-venv/bin/pio run -d firmware/display-test
.tools/esp-venv/bin/pio run -d firmware/display-test -t upload --upload-port /dev/cu.usbmodem1101
```

This test requires no profile. It displays digits 1–5 and blinks the LED. Upload `thr-controller` again to restore THR control. See the [test README](../firmware/display-test/README.md).

## nRF52840: prepare the sniffer firmware

The sniffer uses a separate nRF52840 board. The original Nordic 4.1.1 archive is expected at:

```text
~/.nrfutil/share/nrfutil-ble-sniffer/firmware/sniffer_nrf52840dongle_nrf52840_4.1.1.zip
```

```sh
python3 scripts/inspect-firmware.py
python3 scripts/prepare-sniffer-uf2.py
```

The first script reads archives; the second creates `private/sniffer-dongle-4.1.1-at-1000.uf2`. Neither flashes the board. In the completed experiment, the investigated SuperMini/nice!nano-style nRF52840 entered its UF2 bootloader through a double RESET, then received the prepared UF2 by copying it to the bootloader USB volume. Verify the volume name and memory map before writing. This experimental image targets the specific bootloader arrangement: it writes the application at `0x1000` and replaces the previous SoftDevice region. Do not apply it to arbitrary nRF boards or ESP32 boards.

Identification, backup history, and limitations are in [notes/setup.md](../notes/setup.md). For another board, choose the official image for that model. This repository does not provide a universal sniffer installer.

## Mac: record and analyze traffic

You need a flashed USB sniffer, Python 3, Wireshark/tshark, and Nordic nRF Util with `ble-sniffer`. Prepare the host tools:

```sh
nrfutil install ble-sniffer
nrfutil ble-sniffer bootstrap
```

The capture script expects the shim at `~/.local/lib/wireshark/extcap/nrfutil-ble-sniffer-shim`. These installation commands do not flash the nRF board.

```sh
mkdir -p captures private
python3 scripts/capture-follow.py captures/session-new.pcap --name LE_THRII --port /dev/tty.usbmodem1101
```

Use a new capture filename. Wait for THR discovery and the follow-selection message, then connect the iPhone or AIRSTEP. Stop with Ctrl-C. No other Wireshark/sniffer process should own the same USB port. Decryption requires the relevant pairing/encryption startup or a previously known key; advertisements alone are insufficient.

```sh
python3 scripts/summarize-capture.py captures/session-new.pcap
python3 scripts/export-att.py captures/session-new.pcap > private/session-new-att.tsv
python3 scripts/reassemble-sysex.py captures/session-new.pcap > private/session-new-sysex.jsonl
```

These three tools default to `/Applications/Wireshark.app/Contents/MacOS/tshark` and accept `--tshark` for another path.

## Mac: control the amplifier without the sniffer

You need macOS, the Swift compiler (`swiftc`), Bluetooth permission, and the same private profile. Build:

```sh
mkdir -p .tools private/swift-module-cache
swiftc -module-cache-path private/swift-module-cache scripts/replay-slot.swift -o .tools/replay-slot -Xlinker -sectcreate -Xlinker __TEXT -Xlinker __info_plist -Xlinker scripts/macos-ble-info.plist
.tools/replay-slot --help
```

Turn off AIRSTEP and the ESP controller, close THR Remote, then run:

```sh
.tools/replay-slot --slot 1 --init-profile private/activation-profile.json
# Or select a sequence:
.tools/replay-slot --slots 1,2,3,4,5 --init-profile private/activation-profile.json
```

Without `--init-profile`, the client skips initialization; this did not switch the slot in the first experiment. Exiting the application does not guarantee that macOS releases its system BLE connection to THR.

## Reference for every file in scripts/

| File | Purpose and caveats |
| --- | --- |
| `check-environment.sh` | Checks macOS, USB, ports, and tools; run `sh scripts/check-environment.sh`. No flashing or capture |
| `inspect-firmware.py` | Reads official Nordic ZIP structure and BIN vectors without writing |
| `prepare-sniffer-uf2.py` | Creates the experimental nRF UF2; version and paths are fixed in the code |
| `capture-follow.py` | Starts Nordic extcap, discovers THR, selects follow, and writes PCAP |
| `summarize-capture.py` | Reports PCAP statistics and advertised names |
| `export-att.py` | Exports ATT operations and values through tshark as TSV |
| `reassemble-sysex.py` | Reassembles SysEx by direction; not a full MIDI decoder. `--handle` defaults to `0x000c`; verify the handle for another capture |
| `find-preset-candidates.py` | Finds the exact original AIRSTEP template in PCAP; does not normalize iPhone counters or timestamps |
| `prepare-activation-profile.py` | Historical JSON extraction from two specific private captures; does not overwrite an existing profile |
| `replay-slot.swift` | Native Mac CoreBluetooth client for direct THR control |
| `macos-ble-info.plist` | Bluetooth permission description embedded when building the Swift client |
| `esp32-controller-status.py` | Reads controller RTC diagnostics through esptool; requires the ELF matching the current firmware. **Resets the ESP and interrupts BLE** |

Example ESP diagnostics:

```sh
.tools/esp-venv/bin/python scripts/esp32-controller-status.py --port /dev/cu.usbmodem1101
```

## Validation status and fresh-clone requirements

Recorded experiment results:

- The nRF sniffer ran and recorded traffic; the Mac selected all five slots after initialization.
- The user visually confirmed the ESP display and blinking LED.
- The ESP reached READY: all three initialization steps received matching responses, with no errors. Physical button operation and actual amplifier switching from ESP still require confirmation. The later READY result is recorded in `notes/esp32.md` and the controller README.

Git contains source code, configuration, and documentation. Installed tools, PCAP captures, the private profile, backups, and compiled binaries are excluded. A fresh clone supports reading the documentation and preparing the display test; replay and controller builds first require a validated profile. Local directories are not distributed project dependencies; do not publish their contents with the source code.
