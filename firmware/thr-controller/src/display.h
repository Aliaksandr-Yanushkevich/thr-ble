#pragma once
#include <Wire.h>
static uint8_t address=0x3c;
static bool found=false;
static uint8_t pixels[360];
bool send(uint8_t control,const uint8_t* bytes,size_t count) {
  Wire.beginTransmission(address); Wire.write(control); Wire.write(bytes,count);
  return Wire.endTransmission()==0;
}
void pixel(int x,int y) { if(x>=0&&x<72&&y>=0&&y<40) pixels[x+(y/8)*72]|=1<<(y%8); }
void box(int x,int y,int w,int h) {for(int a=x;a<x+w;a++) for(int b=y;b<y+h;b++) pixel(a,b);}

void displayBegin() {
 Wire.begin(5,6,100000); Wire.setTimeOut(30);
 for(uint8_t a: {uint8_t(0x3c),uint8_t(0x3d)}) { Wire.beginTransmission(a); if(Wire.endTransmission()==0){address=a;found=true;break;} }
 if(!found)return;
 const uint8_t init[]={0xae,0xd5,0x80,0xa8,0x27,0xd3,0,0xad,0x30,0x8d,0x14,0x40,0xa6,0xa4,0x20,2,0xa1,0xc8,0xda,0x12,0x81,96,0xd9,0x22,0xdb,0x20,0x2e,0xaf};
 send(0,init,sizeof(init));
}
void displayFlush(){
 if(!found)return;
 for(int page=0;page<5;page++) {uint8_t cmd[]={uint8_t(0xb0+page),0x0c,0x11};send(0,cmd,3);for(int col=0;col<72;col+=24)send(0x40,pixels+page*72+col,24);}
}
void text(const char* s,int x,int y){
 // Five columns, bit 0 is top. Only status alphabet is needed.
 const char alphabet[]="ACDEIKLNORSTY-";
 const uint8_t font[][5]={{126,17,17,17,126},{62,65,65,65,34},{127,65,65,34,28},{127,73,73,73,65},{0,65,127,65,0},{127,8,20,34,65},{127,64,64,64,64},{127,2,4,8,127},{62,65,65,65,62},{127,9,25,41,70},{70,73,73,73,49},{1,1,127,1,1},{7,8,112,8,7},{8,8,8,8,8}};
 for(;*s;s++,x+=6){const char* p=strchr(alphabet,*s);if(!p)continue;for(int a=0;a<5;a++)for(int b=0;b<7;b++)if(font[p-alphabet][a]&(1<<b))pixel(x+a,y+b);}
}
void displayStatus(const char* status,int slot,bool busy){
 memset(pixels,0,sizeof(pixels));text(status,2,1);
 if(slot<1||slot>5)box(28,24,16,3);
 else {const uint8_t seg[]={6,0x5b,0x4f,0x66,0x6d};uint8_t b=seg[slot-1];
 if(b&1)box(28,11,16,3);if(b&2)box(43,13,3,9);if(b&4)box(43,25,3,9);if(b&8)box(28,34,16,3);if(b&16)box(25,25,3,9);if(b&32)box(25,13,3,9);if(b&64)box(28,22,16,3);}
 if(busy)box(65,34,3,3);displayFlush();
}
