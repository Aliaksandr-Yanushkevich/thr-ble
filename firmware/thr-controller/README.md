# THR-II ESP32-C3 OLED button controller

Board: user-verified SuperMini-style ESP32-C3 with a 0.42-inch SSD1306 72×40 display. Direct display driver on GPIO5 SDA / GPIO6 SCL, address 0x3C, RAM offset 28. Standard blue GPIO8 LED, active-low. Flash DIO 40 MHz.

## Button wiring

With power disconnected, connect a normally open momentary button between **GPIO3 (pin 3) and GND**. INPUT_PULLUP is enabled; no external resistor is required. A four-pin tactile switch has two permanently connected pairs: use contacts that connect only when pressed.

The button must be released after startup. A stable 35 ms press sends one command; holding does not repeat. Input is accepted only in READY; new presses during transmission (about 250 ms) are ignored rather than queued.

## Operation

Turn off AIRSTEP, close THR Remote on all devices, and turn on the amplifier. Display states:

- SCAN — searching for LE_THRII and the BLE-MIDI UUID.
- LINK — connecting and discovering the service/characteristic.
- INIT — encryption/read/subscription and three response-gated activation steps.
- READY — button input is enabled; LED stays on.
- ERROR — failure followed by automatic reconnection. The LED blinks in other states.

READY initially shows a dash: the current amplifier slot is not read. The first press selects 1, followed by 2→3→4→5→1. Reconnection restores the dash and first selection of 1. Connecting does not automatically select a slot. The number shows the last locally sent selection, not confirmed amplifier state; manual changes on the amplifier are not synchronized. A small dot on the right indicates transmission in progress.

The characteristic is found by UUID, without fixed handles. Requested MTU is 247; actual capacity is checked for each message, with the longest initialization write at 55 bytes. CCCD subscription uses a response, followed by a 1-second delay. Initialization steps wait up to 8 seconds for matching captured responses, masking offset 10 only for steps 2/3. Slot command: 32 bytes, Write Without Response, slot-1 at offset 24. Preset saving and amplifier firmware updates are not implemented.

The BLE stack performs Just Works pairing and stores the bond in ESP NVS; keys are not set manually. SC is enabled locally; the final method is negotiated with the amplifier.

## Build

From the repository root:

```sh
.tools/esp-venv/bin/pio run -d firmware/thr-controller
.tools/esp-venv/bin/pio run -d firmware/thr-controller -t upload
```

PlatformIO espressif32 6.12.0, Arduino-ESP32 2.0.17, NimBLE-Arduino 1.4.3.
`generate_profile.py` reads Git-ignored `private/activation-profile.json` and generates a private header only in `.tools/build-thr-controller/`. Do not commit or publish the profile, binaries, bond or backups. The binary contains the private profile.

## Diagnostics

```sh
.tools/esp-venv/bin/python scripts/esp32-controller-status.py
```

Reads non-secret RTC markers through the ROM API and resets the board, interrupting BLE. Use the ELF matching the current firmware; nm locates the symbol address automatically.

Errors: 1 connection, 2 encryption, 3 characteristic/properties, 4 read, 5 subscribe, 6 MTU, 7 init write, 10/11/12 timeouts for steps 1/2/3, 20 slot write, 30 queue allocation, 31 task allocation. tx counts writes successfully queued in the stack, not confirmed delivery; rx counts notifications.

## Validation

Build succeeded: flash 547824 bytes, static RAM 24332 bytes. esptool verified written-region hashes. The command matches the verified Mac template byte-for-byte. Initial RTC diagnostics: SCAN, uptime10814ms, loops1333, button_high1, tx0, rx0, error0. Physical button input and amplifier BLE switching still require verification.
