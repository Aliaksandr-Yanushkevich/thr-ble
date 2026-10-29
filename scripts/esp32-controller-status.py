#!/usr/bin/env python3
"""Read non-secret RTC diagnostics. Temporarily interrupts BLE and resets ESP32."""
import argparse
from pathlib import Path
import subprocess
import json
import esptool
root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--port',default='/dev/cu.usbmodem1101')
a=p.parse_args()
nm=root/'.tools/platformio/packages/toolchain-riscv32-esp/bin/riscv32-esp-elf-nm'
elf=root/'.tools/build-thr-controller/esp32-c3/firmware.elf'
line=next(x for x in subprocess.check_output([str(nm),str(elf)],text=True).splitlines() if x.endswith(' B thrDiagnostic'))
address=int(line.split()[0],16)
esp=esptool.detect_chip(a.port,115200)
try:
 values=[esp.read_reg(address+4*i) for i in range(12)]
 if values[0]!=0x54485243: raise SystemExit('RTC marker missing; firmware not running or mismatched ELF')
 names=['magic','state','init_step','slot','uptime_ms','clicks','tx','rx','error','mtu','button_high','loops']
 data=dict(zip(names,values));data['state_name']=['SCAN','LINK','INIT','READY','ERROR'][values[1]] if values[1]<5 else '?'
 print(json.dumps(data,indent=2))
finally:
 esp.hard_reset()
 esp._port.close()
