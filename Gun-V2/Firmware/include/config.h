#pragma once

#include <stdint.h>

#include "geometry.h"

namespace config {

// Pins for an ESP32-WROOM-32 dev board, as wired in the Gun-V2 schematic.
// Avoided for future additions: GPIO 6-11 (flash), 0/2/12/15 (strapping),
// 16/17 (PSRAM on WROVER modules), 34-39 (input only, no pull-ups).
constexpr int kPinSda = 21;
constexpr int kPinScl = 22;
constexpr int kPinTrigger = 18;   // microswitch COM, NO to ground
constexpr int kPinSolenoid = 27;  // IRLZ44N gate via 100 ohm, 10 kohm pull-down

// LED positions in normalised screen coordinates, measured from the edge of
// the visible image. Values outside 0..1 are on the bezel.
constexpr Point2 kLedScreen[kLedCount] = {
    {0.500f, -0.059f},  // top
    {1.033f, 0.500f},   // right
    {0.500f, 1.059f},   // bottom
    {-0.033f, 0.500f},  // left
};

// True if the camera image is mirrored relative to the barrel on that axis.
constexpr bool kCameraFlipX = false;
constexpr bool kCameraFlipY = false;

// Radio. Channel and gun ID must match the receiver.
constexpr uint8_t kRadioChannel = 1;
constexpr uint8_t kGunId = 1;
constexpr uint32_t kKeepAliveMs = 5;

// Feedback and input timing.
constexpr uint32_t kSolenoidPulseMs = 35;
constexpr uint32_t kDebounceMs = 15;

// Exponential smoothing factor for the cursor; 1.0 disables smoothing.
constexpr float kSmoothing = 1.0f;

constexpr bool kSerialDebug = true;
constexpr uint32_t kDebugIntervalMs = 100;

}  // namespace config
