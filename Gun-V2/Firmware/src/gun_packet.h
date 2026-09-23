#pragma once

#include <stdint.h>

// ESP-NOW packet sent from the gun to the receiver.
// A copy of this file lives in Cabinet/Receiver-Firmware/src; keep them identical.
//
// Each packet carries the complete input state rather than events, so a lost
// packet only delays the next update and can never drop a trigger pull.

constexpr uint16_t kGunPacketMagic = 0x4C47;  // "GL"
constexpr uint8_t kGunPacketVersion = 1;

enum GunButton : uint8_t {
  kButtonLeft = 1 << 0,    // trigger, on screen
  kButtonRight = 1 << 1,   // trigger off screen (reload) or button A
  kButtonMiddle = 1 << 2,  // button B
  kButton4 = 1 << 3,       // button C
  kButton5 = 1 << 4,
};

struct __attribute__((packed)) GunPacket {
  uint16_t magic;
  uint8_t version;
  uint8_t gunId;
  uint8_t sequence;
  uint8_t buttons;  // GunButton bits
  uint16_t x;       // 0..32767 across the screen
  uint16_t y;       // 0..32767 down the screen
};

static_assert(sizeof(GunPacket) == 10, "GunPacket layout changed");
