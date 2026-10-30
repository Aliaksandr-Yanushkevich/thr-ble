# OLED smoke test, corrected implementation

Repository navigation and device-specific workflows: [start here](../../docs/START-HERE.md). Uploading this test replaces the THR controller on the ESP32; upload `firmware/thr-controller` again to restore it.

Hardware hypothesis: ESP32-C3 SuperMini OLED 0.42 inch, SSD1306 72×40.
SDA=GPIO5, SCL=GPIO6, address 0x3C (ACK confirmed), RAM column offset 28.
Direct Wire driver; U8g2 is not used at runtime.
Blue standard LED: GPIO8, LOW turns it on, 250 ms on / 750 ms off; its task runs independently of the display.
Display: 72×40 border and seven-segment digits 1–5, each shown for 2 seconds. BLE and button input are not used yet.
Flash DIO/40 MHz. Build and upload from the repository root:

```sh
.tools/esp-venv/bin/pio run -d firmware/display-test
.tools/esp-venv/bin/pio run -d firmware/display-test -t upload
```

RTC_NOINIT diagnostics: locate the oledDiagnostic symbol with nm from the current ELF; do not assume a fixed address.
Five uint32 values: magic 0x54485232, stage (1 setup, 2 I2C, 3 before init, 4 init ACK, 5 transmission error), uptime_ms, OLED address, loop count.
Read using esptool.read_reg after resetting into ROM without loading a stub; RTC survives this reset but not power removal.
The initial test hung inside U8g2 display.begin (stage=3, address=0x3C, loops=0). The internal library cause remains unresolved.
After replacement: stage=4, uptime=30881 ms, loops=219, address=0x3C. The user subsequently confirmed the display and blinking work; see [the experiment history](../../notes/esp32.md).
The original flash image is saved in Git-ignored private/board-backups.
