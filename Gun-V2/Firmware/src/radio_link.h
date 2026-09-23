#pragma once

#include <stdint.h>

#include "gun_packet.h"

// Broadcasts GunPackets over ESP-NOW. Broadcast avoids pairing, so any
// receiver on the same channel that accepts this gun ID will pick them up.
class RadioLink {
 public:
  bool begin(uint8_t channel);
  bool send(const GunPacket& packet);
};
