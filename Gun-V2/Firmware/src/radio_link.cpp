#include "radio_link.h"

#include <WiFi.h>
#include <esp_now.h>
#include <esp_wifi.h>
#include <string.h>

namespace {

const uint8_t kBroadcastAddress[6] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};

}  // namespace

bool RadioLink::begin(uint8_t channel) {
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  esp_wifi_set_ps(WIFI_PS_NONE);  // power save would delay transmissions
  esp_wifi_set_channel(channel, WIFI_SECOND_CHAN_NONE);

  if (esp_now_init() != ESP_OK) return false;

  esp_now_peer_info_t peer = {};
  memcpy(peer.peer_addr, kBroadcastAddress, sizeof(kBroadcastAddress));
  peer.channel = channel;
  peer.encrypt = false;
  return esp_now_add_peer(&peer) == ESP_OK;
}

bool RadioLink::send(const GunPacket& packet) {
  return esp_now_send(kBroadcastAddress, reinterpret_cast<const uint8_t*>(&packet),
                      sizeof(packet)) == ESP_OK;
}
