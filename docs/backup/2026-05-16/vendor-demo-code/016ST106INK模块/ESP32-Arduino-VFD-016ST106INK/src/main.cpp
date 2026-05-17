#include <Arduino.h>
#include "vfd.h"


void setup() {
  Serial.begin(115200);

  printf("Initializing VFD...\n");

  //初始化引脚IO
  pinMode(VFD_PIN_RST, OUTPUT);
  pinMode(VFD_PIN_CS, OUTPUT);
  pinMode(VFD_PIN_CP, OUTPUT);
  pinMode(VFD_PIN_DA, OUTPUT);
  pinMode(VFD_PIN_EN, OUTPUT_OPEN_DRAIN);

  //开启VFD电源
  VFD_SetPower(1);
  //初始化VFD
  VFD_Init();
  //设置亮度
  VFD_SetBrightness(0xff);

  //测试打印
  Serial.println("VFD Initialized");
  VFD_PrintString(1, "HI ESP32");
  delay(500);


  for (int i = 0; i < 7; i++) {
    VFD_SetIconNative(i, 1, 1);
    delay(50);
  }

  //亮度调整
  for (uint8_t i = 255;i > 0;i -= 5) {
    VFD_SetBrightness(i);
    delay(20);
  }
  for (uint16_t i = 5;i <= 255;i += 5) {
    VFD_SetBrightness(i);
    delay(20);
  }
  VFD_SetBrightness(0xff);
}

void loop() {
  // 主循环中第二行文字滚动显示
  static const char* message = "This is a scrolling text demo on VFD display.   ";
  static size_t msgLen = strlen(message);
  static size_t offset = 0;
  char buffer[16];

  for (int i = 0; i < 16; i++) {
    buffer[i] = message[(offset + i) % msgLen];
  }

  VFD_PrintString(2, buffer);
  offset = (offset + 1) % msgLen;
  delay(100);
}
