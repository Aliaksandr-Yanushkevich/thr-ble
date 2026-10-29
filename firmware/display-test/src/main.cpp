#include <Arduino.h>
#include <Wire.h>
#include <esp_attr.h>
extern "C" { RTC_NOINIT_ATTR volatile uint32_t oledDiagnostic[5]; }
uint8_t address=0x3c;
bool found=false;
uint8_t pixels[360];
void blinkTask(void*) {
  pinMode(8,OUTPUT);
  for (;;) { digitalWrite(8,LOW); vTaskDelay(pdMS_TO_TICKS(250)); digitalWrite(8,HIGH); vTaskDelay(pdMS_TO_TICKS(750)); }
}
bool send(uint8_t control,const uint8_t* bytes,size_t count) {
  Wire.beginTransmission(address); Wire.write(control); Wire.write(bytes,count);
  return Wire.endTransmission()==0;
}
void pixel(int x,int y) { if(x>=0&&x<72&&y>=0&&y<40) pixels[x+(y/8)*72]|=1<<(y%8); }
void box(int x,int y,int w,int h) {for(int a=x;a<x+w;a++) for(int b=y;b<y+h;b++) pixel(a,b);}
void setup() {
  oledDiagnostic[0]=0x54485232; oledDiagnostic[1]=1; oledDiagnostic[2]=0; oledDiagnostic[3]=0; oledDiagnostic[4]=0;
  xTaskCreate(blinkTask,"blink",2048,nullptr,1,nullptr);
  Serial.begin(115200); delay(500);
  Wire.begin(5,6,100000); Wire.setTimeOut(30); oledDiagnostic[1]=2;
  for(uint8_t a: {uint8_t(0x3c),uint8_t(0x3d)}) {
    Wire.beginTransmission(a);
    if(Wire.endTransmission()==0) { address=a; found=true; break; }
  }
  oledDiagnostic[3]=found?address:0; oledDiagnostic[1]=3;
  if(!found) return;
  // SSD1306 72x40: 40 multiplexed rows, internal charge pump, page addressing.
  const uint8_t init[]={0xae,0xd5,0x80,0xa8,0x27,0xd3,0,0xad,0x30,0x8d,0x14,0x40,0xa6,0xa4,0x20,2,0xa1,0xc8,0xda,0x12,0x81,96,0xd9,0x22,0xdb,0x20,0x2e,0xaf};
  if(send(0,init,sizeof(init))) oledDiagnostic[1]=4;
}
void loop() {
  oledDiagnostic[2]=millis(); oledDiagnostic[4]++;
  static uint32_t log=0;
  if(millis()-log>2000) { log=millis(); Serial.printf("ALIVE stage=%lu OLED=0x%02x\n",(unsigned long)oledDiagnostic[1],found?address:0); }
  if(!found) {delay(50); return;}
  memset(pixels,0,sizeof(pixels));
  for(int x=0;x<72;x++){pixel(x,0);pixel(x,39);} for(int y=0;y<40;y++){pixel(0,y);pixel(71,y);}
  // Seven-segment digits 1-5, each held for two seconds.
  const uint8_t segments[]={0x06,0x5b,0x4f,0x66,0x6d};
  uint8_t digit=(millis()/2000)%5, bits=segments[digit];
  if(bits&1) box(28,4,16,3); if(bits&2) box(43,6,3,12);
  if(bits&4) box(43,21,3,12); if(bits&8) box(28,33,16,3);
  if(bits&16) box(25,21,3,12); if(bits&32) box(25,6,3,12); if(bits&64) box(28,19,16,3);
  for(int page=0;page<5;page++) {
    uint8_t cmd[]={uint8_t(0xb0+page),0x0c,0x11}; // RAM column 28
    if(!send(0,cmd,3)) oledDiagnostic[1]=5;
    for(int col=0;col<72;col+=24) if(!send(0x40,pixels+page*72+col,24)) oledDiagnostic[1]=5;
  }
  delay(100);
}
