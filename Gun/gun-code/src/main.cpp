#include <Wire.h>
#include <Arduino.h>

int IRsensorAddress = 0x58; // Standard I2C address for SEN0158
byte data_buf[16];
int Ix[4], Iy[4];

void Write_2bytes(byte d1, byte d2) {
  Wire.beginTransmission(IRsensorAddress);
  Wire.write(d1);
  Wire.write(d2);
  Wire.endTransmission();
}

void setup() {
  Serial.begin(19200);
  Wire.begin(21, 22); // ESP32 pins: SDA=21, SCL=22
  
  // Initialize IR Camera registers
  Write_2bytes(0x30, 0x01); delay(10);
  Write_2bytes(0x30, 0x08); delay(10);
  Write_2bytes(0x06, 0x90); delay(10);
  Write_2bytes(0x08, 0xC0); delay(10);
  Write_2bytes(0x1A, 0x40); delay(10);
  Write_2bytes(0x33, 0x33); delay(10);
  delay(100);
}

void loop() {
  // Command to read data
  Wire.beginTransmission(IRsensorAddress);
  Wire.write(0x36);
  Wire.endTransmission();
  
  Wire.requestFrom(IRsensorAddress, 16); 
  for (int i = 0; i < 16; i++) {
    data_buf[i] = Wire.read();
  }
  
  // Parse coordinates for 4 dots
  for(int i = 0; i < 4; i++) {
    int index = i * 3 + 1; // 1, 4, 7, 10
    Ix[i] = data_buf[index];
    Iy[i] = data_buf[index + 1];
    int s = data_buf[index + 2];
    Ix[i] += (s & 0x30) << 4;
    Iy[i] += (s & 0xC0) << 2;
  }

  // Print format: x1,y1,x2,y2,x3,y3,x4,y4
  for(int i = 0; i < 4; i++) {
    Serial.print(Ix[i]);
    Serial.print(",");
    Serial.print(Iy[i]);
    if(i < 3) Serial.print(",");
  }
  Serial.println("");
  delay(30); // ~30fps refresh rate
}