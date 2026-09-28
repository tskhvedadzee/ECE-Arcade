#include "ir_camera.h"

#include <Arduino.h>

namespace {

constexpr uint8_t kRegisterReport = 0x36;
constexpr int kReportLength = 16;
constexpr int kMaxValidY = 767;  // empty slots read back as 1023

// Consecutive failed reads before the bus is restarted. At the loop rate this
// is well under a tenth of a second.
constexpr int kErrorsBeforeRestart = 10;

}  // namespace

void IrCamera::begin(TwoWire& wire, int sdaPin, int sclPin, uint32_t clockHz, bool flipX,
                     bool flipY, uint8_t address) {
  wire_ = &wire;
  sdaPin_ = sdaPin;
  sclPin_ = sclPin;
  clockHz_ = clockHz;
  address_ = address;
  flipX_ = flipX;
  flipY_ = flipY;

  wire_->begin(sdaPin_, sclPin_, clockHz_);
  configureSensor();
}

void IrCamera::configureSensor() {
  // Initialisation sequence from the DFRobot SEN0158 example code
  // (sensitivity block settings and extended report mode).
  writeRegister(0x30, 0x01);
  writeRegister(0x30, 0x08);
  writeRegister(0x06, 0x90);
  writeRegister(0x08, 0xC0);
  writeRegister(0x1A, 0x40);
  writeRegister(0x33, 0x33);
  delay(100);
}

// A transfer cut short by a glitch or a reset can leave the sensor holding the
// data line low, which wedges the bus permanently. Clocking the bus manually
// lets the sensor finish that transfer, after which the driver is restarted.
void IrCamera::restartBus() {
  wire_->end();

  pinMode(sdaPin_, INPUT_PULLUP);
  pinMode(sclPin_, OUTPUT);
  for (int i = 0; i < 9 && digitalRead(sdaPin_) == LOW; ++i) {
    digitalWrite(sclPin_, LOW);
    delayMicroseconds(5);
    digitalWrite(sclPin_, HIGH);
    delayMicroseconds(5);
  }

  wire_->begin(sdaPin_, sclPin_, clockHz_);
  configureSensor();
  Serial.println("camera bus restarted");
}

int IrCamera::read(Point2 blobs[4]) {
  wire_->beginTransmission(address_);
  wire_->write(kRegisterReport);
  const bool addressed = wire_->endTransmission() == 0;
  if (!addressed || wire_->requestFrom(static_cast<int>(address_), kReportLength) != kReportLength) {
    if (++consecutiveErrors_ >= kErrorsBeforeRestart) {
      consecutiveErrors_ = 0;
      restartBus();
    }
    return -1;
  }
  consecutiveErrors_ = 0;

  uint8_t data[kReportLength];
  for (int i = 0; i < kReportLength; ++i) data[i] = wire_->read();

  // Byte 0 is a header; each point is 3 bytes: x low, y low, then the high
  // bits of x (bits 4-5) and y (bits 6-7).
  int count = 0;
  for (int i = 0; i < 4; ++i) {
    const uint8_t* p = &data[1 + 3 * i];
    const int x = p[0] | ((p[2] & 0x30) << 4);
    const int y = p[1] | ((p[2] & 0xC0) << 2);
    if (y > kMaxValidY) continue;

    float fx = x / 1024.0f;
    float fy = y / 1024.0f;
    if (flipX_) fx = 1.0f - fx;
    if (flipY_) fy = 0.75f - fy;
    blobs[count++] = {fx, fy};
  }
  return count;
}

void IrCamera::writeRegister(uint8_t reg, uint8_t value) {
  wire_->beginTransmission(address_);
  wire_->write(reg);
  wire_->write(value);
  wire_->endTransmission();
  delay(10);
}
