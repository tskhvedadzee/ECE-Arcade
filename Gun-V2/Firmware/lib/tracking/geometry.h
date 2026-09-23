#pragma once

#include <stdint.h>

// 2D point. Used for both coordinate spaces in this library:
//   camera: SEN0158 pixel / 1024, so x in [0, 1) and y in [0, 0.75), y down
//   screen: (0, 0) top-left of the visible image, (1, 1) bottom-right
struct Point2 {
  float x;
  float y;
};

// The four IR LEDs sit at the midpoints of the screen edges ("diamond").
enum LedIndex : uint8_t {
  kLedTop = 0,
  kLedRight = 1,
  kLedBottom = 2,
  kLedLeft = 3,
  kLedCount = 4,
};
