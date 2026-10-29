#include <Arduino.h>
#include <NimBLEDevice.h>
#include <atomic>
#include <esp_attr.h>
#include "activation_profile.h"
#include "display.h"
constexpr int BUTTON_PIN=3, LED_PIN=8;
const char* SERVICE="03b80e5a-ede8-4b33-a751-6ce34ec4c700";
const char* CHARACTERISTIC="7772e5db-3868-4112-a1a9-f2669d106bf3";
enum State {SCAN,LINK,INIT,READY,ERROR_STATE};
std::atomic<int> state{SCAN}, slot{0}, errorCode{0};
std::atomic<bool> pending{false};
extern "C" {RTC_NOINIT_ATTR volatile uint32_t thrDiagnostic[12];}
struct Rx {size_t size; uint8_t data[128];};
QueueHandle_t rxQueue,buttonQueue;
void notification(NimBLERemoteCharacteristic*,uint8_t* data,size_t size,bool){
 thrDiagnostic[7]++;
 if(size>128)return;
 Rx rx{};rx.size=size;memcpy(rx.data,data,size);xQueueSend(rxQueue,&rx,0);
}
bool matches(const Rx& rx,const InitStep& step){
 if(rx.size!=step.rxSize)return false;
 for(size_t i=0;i<rx.size;i++)if(int(i)!=step.mask&&rx.data[i]!=step.rx[i])return false;
 return true;
}
bool activate(NimBLEClient* client,NimBLERemoteCharacteristic* chr){
 state=INIT;thrDiagnostic[2]=0;
 if(!client->secureConnection()){errorCode=2;return false;}
 if(!chr->canRead()||!chr->canNotify()||!chr->canWriteNoResponse()){errorCode=3;return false;}
 auto value=chr->readValue();
 if(value.size()==0){errorCode=4;return false;}
 if(!chr->subscribe(true,notification,true)){errorCode=5;return false;}
 delay(1000);
 thrDiagnostic[9]=client->getMTU();
 if(client->getMTU()<35){errorCode=6;return false;}
 for(size_t i=0;i<3;i++){
  thrDiagnostic[2]=i+1;
  const auto& step=initSteps[i];
  if(step.txSize>size_t(client->getMTU()-3)){errorCode=6;return false;}
  xQueueReset(rxQueue);
  if(!chr->writeValue(step.tx,step.txSize,false)){errorCode=7;return false;}
  thrDiagnostic[6]++;
  uint32_t start=millis();bool matched=false;
  while(client->isConnected()&&millis()-start<8000){
   Rx rx{};
   if(xQueueReceive(rxQueue,&rx,pdMS_TO_TICKS(100))&&matches(rx,step)){matched=true;break;}
  }
  if(!matched){errorCode=10+i;return false;}
  delay(200);
 }
 return true;
}
void bleTask(void*){
 NimBLEDevice::init("THR Button");
 NimBLEDevice::setMTU(247);
 NimBLEDevice::setSecurityIOCap(BLE_HS_IO_NO_INPUT_OUTPUT);
 // Bonding, no MITM; SC permitted when peer supports it, legacy negotiated otherwise.
 NimBLEDevice::setSecurityAuth(true,false,true);
 auto scan=NimBLEDevice::getScan();scan->setActiveScan(true);scan->setInterval(80);scan->setWindow(60);
 auto client=NimBLEDevice::createClient();client->setConnectTimeout(8);
 client->setConnectionParams(12,24,0,400);
 for(;;){
  state=SCAN;slot=0;pending=false;xQueueReset(buttonQueue);
  auto results=scan->start(4,false);bool have=false;
  NimBLEAddress peer("00:00:00:00:00:00");
  for(int i=0;i<results.getCount();i++){
   auto d=results.getDevice(i);
   if(d.getName()=="LE_THRII" && d.isAdvertisingService(NimBLEUUID(SERVICE))){peer=d.getAddress();have=true;break;}
  }
  scan->clearResults();
  if(!have){delay(500);continue;}
  state=LINK;errorCode=0;
  if(!client->connect(peer,true)){errorCode=1;state=ERROR_STATE;delay(2000);continue;}
  auto service=client->getService(SERVICE);
  auto chr=service?service->getCharacteristic(CHARACTERISTIC):nullptr;
  if(!chr){errorCode=3;}
  if(!chr||!activate(client,chr)){
   state=ERROR_STATE;thrDiagnostic[8]=errorCode.load();client->disconnect();delay(3000);continue;
  }
  state=READY;thrDiagnostic[8]=0;
  while(client->isConnected()){
   uint8_t click;
   if(!xQueueReceive(buttonQueue,&click,pdMS_TO_TICKS(100)))continue;
   uint8_t next=slot.load()%5+1;
   uint8_t command[]={0x80,0x80,0xf0,0,1,0x0c,0x24,0,0x4d,1,0,0,0,0x0b,0,0x0e,0,0,0,4,0,0,0,0,0,0,0,0,0,0,0x80,0xf7};
   command[24]=next-1;
   if(chr->writeValue(command,sizeof(command),false)){slot=next;thrDiagnostic[6]++;delay(250);}
   else {errorCode=20;state=ERROR_STATE;client->disconnect();}
   pending=false;
  }
  pending=false;delay(1000);
 }
}
void setup(){
 for(int i=0;i<12;i++)thrDiagnostic[i]=0;
 thrDiagnostic[0]=0x54485243;
 pinMode(BUTTON_PIN,INPUT_PULLUP);pinMode(LED_PIN,OUTPUT);digitalWrite(LED_PIN,HIGH);
 Serial.begin(115200);displayBegin();
 rxQueue=xQueueCreate(12,sizeof(Rx));buttonQueue=xQueueCreate(1,sizeof(uint8_t));
 if(!rxQueue||!buttonQueue){state=ERROR_STATE;errorCode=30;return;}
 if(xTaskCreate(bleTask,"thr-ble",8192,nullptr,1,nullptr)!=pdPASS){state=ERROR_STATE;errorCode=31;}
}
void loop(){
 uint32_t now=millis();
 static bool raw=HIGH,stable=HIGH,armed=false;
 static uint32_t changed=0,render=0;
 bool current=digitalRead(BUTTON_PIN);
 if(current!=raw){raw=current;changed=now;}
 // Require a stable release, including after boot; holding does not repeat.
 if(now-changed>=35){
  if(raw==HIGH)armed=true;
  if(stable!=raw){stable=raw;
   if(stable==LOW&&armed){armed=false;thrDiagnostic[5]++;
    if(state==READY&&!pending.exchange(true)){uint8_t click=1;if(xQueueSend(buttonQueue,&click,0)!=pdTRUE)pending=false;}
   }
  }
 }
 const char* names[]={"SCAN","LINK","INIT","READY","ERROR"};
 int st=state.load();
 digitalWrite(LED_PIN,st==READY?LOW:((now%1000)<150?LOW:HIGH));
 if(now-render>=100){render=now;displayStatus(names[st],slot.load(),pending.load());}
 thrDiagnostic[1]=st;thrDiagnostic[3]=slot.load();thrDiagnostic[4]=now;thrDiagnostic[8]=errorCode.load();thrDiagnostic[10]=current;thrDiagnostic[11]++;
 delay(5);
}
