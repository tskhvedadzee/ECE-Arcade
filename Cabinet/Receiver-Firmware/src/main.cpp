// Receiver firmware: ESP32-S3 plugged into the Raspberry Pi. Receives gun
// packets over ESP-NOW and presents them to the Pi as a USB pointing device.

#include <Arduino.h>

#if !defined(ARDUINO_USB_MODE) || ARDUINO_USB_MODE != 0
#error "Requires native USB in USB-OTG (TinyUSB) mode; see platformio.ini"
#endif

#include <USB.h>
#include <USBHID.h>
#include <WiFi.h>
#include <esp_now.h>
#include <esp_wifi.h>
#include <FS.h>
#include <string.h>

#include "gun_packet.h"
#include "usb_gun_device.h"

namespace {

// Must match the gun.
constexpr uint8_t kRadioChannel = 1;
constexpr uint8_t kAcceptedGunId = 1;

// Release all buttons if the gun goes quiet (battery, range) so the trigger
// can never stay held down.
constexpr uint32_t kLinkTimeoutMs = 100;

USBHID hid;
UsbGunDevice gunDevice(hid);

// Written from the Wi-Fi task in onReceive(), read from loop().
portMUX_TYPE rxLock = portMUX_INITIALIZER_UNLOCKED;
GunPacket rxPacket;
bool rxPending = false;
uint32_t rxTimeMs = 0;

struct GunState {
  uint8_t buttons = 0;
  uint16_t x = 16384;
  uint16_t y = 16384;
};
GunState state;
bool reportPending = false;
bool linkUp = false;

void onReceive(const esp_now_recv_info_t*, const uint8_t* data, int length) {
  if (length != static_cast<int>(sizeof(GunPacket))) return;
  GunPacket p;
  memcpy(&p, data, sizeof(p));
  if (p.magic != kGunPacketMagic || p.version != kGunPacketVersion) return;
  if (p.gunId != kAcceptedGunId) return;

  const uint32_t now = millis();
  portENTER_CRITICAL(&rxLock);
  rxPacket = p;
  rxPending = true;
  rxTimeMs = now;
  portEXIT_CRITICAL(&rxLock);
}

}  // namespace

void setup() {
  Serial.begin(115200);

  USB.manufacturerName("ECE-Arcade");
  USB.productName("DIY Lightgun");  // matched by Cabinet/Batocera/99-diy-gun.rules
  hid.begin();
  USB.begin();

  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  esp_wifi_set_ps(WIFI_PS_NONE);
  esp_wifi_set_channel(kRadioChannel, WIFI_SECOND_CHAN_NONE);
  if (esp_now_init() != ESP_OK) {
    Serial.println("ESP-NOW init failed");
    return;
  }
  esp_now_register_recv_cb(onReceive);
}

void loop() {
  GunPacket p;
  bool received = false;
  uint32_t lastRxMs;

  portENTER_CRITICAL(&rxLock);
  if (rxPending) {
    p = rxPacket;
    rxPending = false;
    received = true;
  }
  lastRxMs = rxTimeMs;
  portEXIT_CRITICAL(&rxLock);

  const uint32_t now = millis();
  if (received) {
    if (p.buttons != state.buttons || p.x != state.x || p.y != state.y) reportPending = true;
    state.buttons = p.buttons;
    state.x = p.x;
    state.y = p.y;
    if (!linkUp) {
      linkUp = true;
      Serial.println("gun connected");
    }
  } else if (linkUp && now - lastRxMs > kLinkTimeoutMs) {
    linkUp = false;
    if (state.buttons != 0) {
      state.buttons = 0;
      reportPending = true;
    }
    Serial.println("gun link lost");
  }

  if (reportPending && gunDevice.ready()) {
    if (gunDevice.send(state.buttons, state.x, state.y)) reportPending = false;
  }
}
