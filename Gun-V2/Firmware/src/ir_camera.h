#pragma once
#include <Wire.h>
#include "geometry.h"

// Driver for the DFRobot SEN0158 (PixArt sensor from the Wii Remote). The
// sensor does blob detection itself and reports up to four IR points over I2C.
class IrCamera {
 public:
  static constexpr uint8_t kDefaultAddress = 0x58;

  void begin(TwoWire& wire, bool flipX, bool flipY, uint8_t address = kDefaultAddress);

  // Fills blobs[] with the visible points in normalised camera coordinates
  // (pixel / 1024). Returns the number of points, or -1 on a bus error.
  int read(Point2 blobs[4]);

 private:
  void writeRegister(uint8_t reg, uint8_t value);

  TwoWire* wire_ = nullptr;
  uint8_t address_ = kDefaultAddress;
  bool flipX_ = false;
  bool flipY_ = false;
};
