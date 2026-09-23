#include "usb_gun_device.h"

#include <string.h>

namespace {

constexpr uint8_t kReportId = 1;

// clang-format off
const uint8_t kReportDescriptor[] = {
    0x05, 0x01,        // Usage Page (Generic Desktop)
    0x09, 0x02,        // Usage (Mouse)
    0xA1, 0x01,        // Collection (Application)
    0x85, kReportId,   //   Report ID
    0x09, 0x01,        //   Usage (Pointer)
    0xA1, 0x00,        //   Collection (Physical)
    0x05, 0x09,        //     Usage Page (Button)
    0x19, 0x01,        //     Usage Minimum (1)
    0x29, 0x05,        //     Usage Maximum (5)
    0x15, 0x00,        //     Logical Minimum (0)
    0x25, 0x01,        //     Logical Maximum (1)
    0x95, 0x05,        //     Report Count (5)
    0x75, 0x01,        //     Report Size (1)
    0x81, 0x02,        //     Input (Data, Variable, Absolute)
    0x95, 0x01,        //     Report Count (1)
    0x75, 0x03,        //     Report Size (3)
    0x81, 0x03,        //     Input (Constant) - padding
    0x05, 0x01,        //     Usage Page (Generic Desktop)
    0x09, 0x30,        //     Usage (X)
    0x09, 0x31,        //     Usage (Y)
    0x16, 0x00, 0x00,  //     Logical Minimum (0)
    0x26, 0xFF, 0x7F,  //     Logical Maximum (32767)
    0x75, 0x10,        //     Report Size (16)
    0x95, 0x02,        //     Report Count (2)
    0x81, 0x02,        //     Input (Data, Variable, Absolute)
    0xC0,              //   End Collection
    0xC0,              // End Collection
};
// clang-format on

}  // namespace

UsbGunDevice::UsbGunDevice(USBHID& hid) : hid_(hid) {
  hid_.addDevice(this, sizeof(kReportDescriptor));
}

bool UsbGunDevice::ready() const { return hid_.ready(); }

bool UsbGunDevice::send(uint8_t buttons, uint16_t x, uint16_t y) {
  const uint8_t report[5] = {buttons, static_cast<uint8_t>(x), static_cast<uint8_t>(x >> 8),
                             static_cast<uint8_t>(y), static_cast<uint8_t>(y >> 8)};
  return hid_.SendReport(kReportId, report, sizeof(report));
}

uint16_t UsbGunDevice::_onGetDescriptor(uint8_t* buffer) {
  memcpy(buffer, kReportDescriptor, sizeof(kReportDescriptor));
  return sizeof(kReportDescriptor);
}
