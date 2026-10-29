#include <Arduino.h>
#include <Wire.h>
#include <U8g2lib.h>

// Common 0.42-inch board hypothesis; verified visually after uploading.
constexpr int SDA_PIN = 5;
constexpr int SCL_PIN = 6;
U8G2_SSD1306_72X40_ER_F_HW_I2C display(U8G2_R0, U8X8_PIN_NONE, SCL_PIN, SDA_PIN);
bool found = false;

void setup() {
  Serial.begin(115200);
  delay(1500);
  Serial.println("THR display test: SSD1306 72x40, SDA=5 SCL=6");
  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.setClock(100000);
  for (uint8_t address = 8; address < 120; ++address) {
    Wire.beginTransmission(address);
    if (Wire.endTransmission() == 0) {
      Serial.printf("I2C ACK at 0x%02X\n", address);
      if (address == 0x3c || address == 0x3d) {
        display.setI2CAddress(address << 1);
        found = true;
      }
    }
  }
  if (!found) { Serial.println("No OLED at 0x3C/0x3D; no display commands sent"); return; }
  display.begin();
  display.setContrast(96);
  Serial.println("OLED init done; alternating grid and digits 1-5; BLE disabled");
}

void loop() {
  if (!found) { delay(1000); return; }
  const uint32_t phase = (millis() / 2000) % 6;
  display.clearBuffer();
  display.drawFrame(0, 0, 72, 40);
  if (phase == 0) {
    display.setFont(u8g2_font_5x7_tr);
    display.drawStr(5, 11, "OLED TEST");
    display.drawStr(5, 22, "72 x 40");
    display.drawStr(5, 33, "SDA5 SCL6");
    display.drawPixel(2, 2);
    display.drawPixel(69, 37);
  } else {
    char digit[] = {char('0' + phase), 0};
    display.setFont(u8g2_font_logisoso28_tn);
    display.drawStr((72 - display.getStrWidth(digit)) / 2, 34, digit);
  }
  display.sendBuffer();
  delay(50);
}
