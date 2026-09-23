#pragma once

#include <USBHID.h>

// USB HID absolute pointer: five buttons and 16-bit X/Y (0..32767). Linux
// exposes it as an evdev device with ABS_X/ABS_Y, which Batocera can tag as
// a light gun through a udev rule.
class UsbGunDevice : public USBHIDDevice {
 public:
  explicit UsbGunDevice(USBHID& hid);

  bool ready() const;
  bool send(uint8_t buttons, uint16_t x, uint16_t y);

  uint16_t _onGetDescriptor(uint8_t* buffer) override;

 private:
  USBHID& hid_;
};
