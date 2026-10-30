# ESP32 THR-II controller

## Hardware check: 2026-10-29

- USB: Espressif USB JTAG/serial, VID:PID 303a:1001.
- Port: `/dev/cu.usbmodem1101` (may change).
- esptool 4.12.0 in `.tools/esp-venv`; installed with pip for system Python 3.9.
- `flash_id`: ESP32-C3 (QFN32), revision v0.4, 40 MHz crystal, embedded XMC 4 MB flash; manufacturer 46, device 4016.
- No flash writes/erases or eFuse changes during identification. Diagnostics load a temporary RAM stub and reset the board.
- USB does not identify the exact PCB, display controller or wiring. A photo/link was required; 72×40 resolution and SDA=5/SCL=6 were initially unconfirmed.
- No Arduino/PlatformIO/ESP-IDF build tools were found in the standard directories checked.

Commands:

```sh
.tools/esp-venv/bin/python -m esptool --port /dev/cu.usbmodem1101 flash_id
.tools/esp-venv/bin/python -m esptool --port /dev/cu.usbmodem1101 --baud 460800 read_flash 0 ALL private/board-backups/esp32c3-original-20261029.bin
```

The backup is in Git-ignored `private/board-backups/`; completion and checksum are recorded separately.

Required behavior: a momentary button with debouncing, one transition per press, cycling slots 1–5, a display showing the number and BLE state, and automatic reconnection with initialization repeated. Select the GPIO after PCB identification. BLE UUIDs and messages come from the verified Mac client; handles are discovered dynamically.

Backup read completed successfully: 4194304 bytes, SHA256 `75aded6ec182bdd2dc4d57707b17ae080220c69c48443b90fbbcd1a92596d3db`. esptool exited with code 0.

## OLED test

Built and flashed `firmware/display-test`: Arduino-ESP32 2.0.17, PlatformIO espressif32 6.12.0, U8g2 2.36.15. Flash: 273114 bytes; RAM: 14744 bytes. Bootloader/partition/application writes completed; esptool verified written-region hashes. No full erase was performed.

Hypothesis: SSD1306 72×40, I²C GPIO5/6; test pattern and digits 1–5 every 2 seconds. BLE is disabled. USB CDC reads after boot and RTS reset attempts returned no text: neither display ACK nor application execution had yet been confirmed through logs. Visual confirmation was needed; for a blank screen, start with physical RESET/USB reconnection, then investigate CDC/I²C. No button was assigned yet.

The user reported a blank screen after the first flash. Uploaded diagnostics using DIO/40 MHz flash and an ALIVE/OLED message every 2 seconds. Build and write verification succeeded, but USB CDC remained silent. A watchdog reset of the previous image also produced no log. Display failure or incorrect wiring could not yet be established because application execution was unconfirmed. Requested complete USB power removal and reconnection.

## Initialization diagnosis and fix

Added an independent GPIO8 blink (250/750 ms) and RTC_NOINIT markers. ROM esptool reads without a stub confirmed magic=54485232, stage=3 (before display.begin), address=3C, uptime=0, loops=0 in the previous library implementation. The application therefore starts and the OLED responds; the hang occurs during display.begin, with the exact cause unresolved.

Replaced display output with direct Wire SSD1306 commands: GPIO5/6, I²C 100 kHz, 30 ms timeout, offset 28, page mode. Initialization and updates receive ACKs. After a verified flash, diagnostics read stage=4, uptime=0x78a1, loops=0xdb, address=3C. Main-loop execution was confirmed; visual confirmation was pending. A blue GPIO8 LED is a common SuperMini hypothesis, not proof of the exact PCB revision.

## Button controller

The user confirmed the fixed display and blinking work. Created and flashed `firmware/thr-controller`: GPIO3–GND, INPUT_PULLUP, 35 ms debounce, one selection per press, slots 1–5, first selection of 1 only after a button press. NimBLE 1.4.3 handles UUID discovery, stack-managed pairing, read/subscribe, response-gated initialization from a private profile, and a requested MTU of 247 with size checks. The UI shows connection states; reconnect is automatic and resets the local slot number. See the controller README for source details. RTC confirmed SCAN startup without errors; physical button operation and actual amplifier switching from ESP were not yet confirmed.

The user saw SCAN. Read-only CoreBluetooth `retrieveConnectedPeripherals` on the Mac found an OS-held LE_THRII connection. Calling cancelPeripheralConnection from a separate central did not release it: LE_THRII remained listed after 3 seconds. This likely explains missing amplifier advertising; it does not establish an ESP scanning defect. Requested temporarily disabling Mac Bluetooth and restarting the amplifier; firmware was unchanged. Historical capture05 shows both LE_THRII and the BLE-MIDI UUID in ADV_IND (frame 1), so there was no evidence supporting a weaker scan filter.

After Mac Bluetooth was disabled, ESP RTC diagnostics confirmed READY: init_step3, tx3, rx4, error0, MTU96, slot0, clicks0, button_high1, uptime309509ms. All three activation steps received matching responses. This confirms ESP BLE connection and initialization, but not a physical press or actual slot change. The diagnostic read reset the ESP, after which automatic reconnection resumes.
