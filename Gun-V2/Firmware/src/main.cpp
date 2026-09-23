// Gun firmware: reads the IR camera, works out where the gun is aimed and
// sends the aim point and trigger state to the receiver over ESP-NOW.
//
// Calibration is armed by holding the trigger during power-on. After the
// trigger is released, the next pull stores the boresight for the centre of
// the screen instead of shooting, and the solenoid fires to confirm.

#include <Arduino.h>
#include <Preferences.h>
#include <Wire.h>

#include "aim.h"
#include "button.h"
#include "config.h"
#include "gun_packet.h"
#include "ir_camera.h"
#include "led_tracker.h"
#include "radio_link.h"

namespace {

IrCamera camera;
LedTracker tracker;
RadioLink radio;
Preferences storage;
Button trigger(config::kPinTrigger, config::kDebounceMs);

Point2 boresight = kDefaultBoresight;
Point2 cursor = {0.5f, 0.5f};
uint8_t triggerButton = 0;  // HID button held by the current trigger pull
bool calibrationArmed = false;

uint32_t solenoidOffMs = 0;
bool solenoidActive = false;

GunPacket packet = {kGunPacketMagic, kGunPacketVersion, config::kGunId, 0, 0, 0, 0};
uint32_t lastSendMs = 0;
uint32_t lastDebugMs = 0;

struct Frame {
  int blobCount = 0;
  bool tracked = false;
  bool hasAim = false;
  Point2 leds[kLedCount] = {};
  Point2 aim = {0, 0};
};

Frame readFrame() {
  Frame f;
  Point2 blobs[4];
  f.blobCount = camera.read(blobs);
  if (f.blobCount < 0) {
    tracker.reset();
    return f;
  }
  f.tracked = tracker.update(blobs, f.blobCount, f.leds);
  f.hasAim = f.tracked && computeAim(f.leds, config::kLedScreen, boresight, f.aim);
  return f;
}

void fireSolenoid(uint32_t nowMs) {
  digitalWrite(config::kPinSolenoid, HIGH);
  solenoidActive = true;
  solenoidOffMs = nowMs + config::kSolenoidPulseMs;
}

void updateSolenoid(uint32_t nowMs) {
  if (solenoidActive && static_cast<int32_t>(nowMs - solenoidOffMs) >= 0) {
    digitalWrite(config::kPinSolenoid, LOW);
    solenoidActive = false;
  }
}

bool saveBoresight(const Frame& f) {
  Point2 updated;
  if (!f.tracked) return false;
  if (!calibrateBoresight(f.leds, config::kLedScreen, {0.5f, 0.5f}, updated)) return false;
  boresight = updated;
  storage.putFloat("bore_x", boresight.x);
  storage.putFloat("bore_y", boresight.y);
  Serial.printf("calibrated: boresight %.4f %.4f\n", boresight.x, boresight.y);
  return true;
}

void handleTrigger(const Frame& f, uint32_t nowMs) {
  if (!trigger.update(nowMs)) return;

  if (!trigger.pressed()) {
    triggerButton = 0;
    return;
  }
  if (calibrationArmed) {
    // Stays armed if the LEDs were not in view, so the pull can be repeated.
    if (saveBoresight(f)) {
      calibrationArmed = false;
      fireSolenoid(nowMs);
    }
    return;
  }
  // Off-screen shots are sent as the right button, which MAME's
  // offscreen_reload option treats as a reload.
  triggerButton = (f.hasAim && isOnScreen(f.aim)) ? kButtonLeft : kButtonRight;
  fireSolenoid(nowMs);
}

uint16_t toHidAxis(float v) {
  v = constrain(v, 0.0f, 1.0f);
  return static_cast<uint16_t>(v * 32767.0f + 0.5f);
}

void sendState(uint32_t nowMs) {
  const uint8_t buttons = triggerButton;
  const uint16_t x = toHidAxis(cursor.x);
  const uint16_t y = toHidAxis(cursor.y);

  const bool changed = buttons != packet.buttons || x != packet.x || y != packet.y;
  if (!changed && nowMs - lastSendMs < config::kKeepAliveMs) return;

  packet.sequence++;
  packet.buttons = buttons;
  packet.x = x;
  packet.y = y;
  radio.send(packet);
  lastSendMs = nowMs;
}

void printDebug(const Frame& f, uint32_t nowMs) {
  if (!config::kSerialDebug || nowMs - lastDebugMs < config::kDebugIntervalMs) return;
  lastDebugMs = nowMs;

  Serial.printf("blobs=%d tracked=%d", f.blobCount, f.tracked);
  if (f.tracked) {
    Serial.printf(" T(%.3f,%.3f) R(%.3f,%.3f) B(%.3f,%.3f) L(%.3f,%.3f)",
                  f.leds[kLedTop].x, f.leds[kLedTop].y, f.leds[kLedRight].x,
                  f.leds[kLedRight].y, f.leds[kLedBottom].x, f.leds[kLedBottom].y,
                  f.leds[kLedLeft].x, f.leds[kLedLeft].y);
  }
  if (f.hasAim) {
    Serial.printf(" aim=(%.3f,%.3f)%s", f.aim.x, f.aim.y, isOnScreen(f.aim) ? "" : " off");
  }
  if (calibrationArmed) Serial.print(" [calibration armed]");
  Serial.println();
}

}  // namespace

void setup() {
  // Drive the gate low first; R2 holds the MOSFET off until this runs.
  pinMode(config::kPinSolenoid, OUTPUT);
  digitalWrite(config::kPinSolenoid, LOW);

  Serial.begin(115200);

  trigger.begin();
  calibrationArmed = trigger.pressed();

  storage.begin("gun", false);
  boresight.x = storage.getFloat("bore_x", kDefaultBoresight.x);
  boresight.y = storage.getFloat("bore_y", kDefaultBoresight.y);

  Wire.begin(config::kPinSda, config::kPinScl, 400000);
  camera.begin(Wire, config::kCameraFlipX, config::kCameraFlipY);

  if (!radio.begin(config::kRadioChannel)) Serial.println("ESP-NOW init failed");
}

void loop() {
  const uint32_t now = millis();
  const Frame frame = readFrame();

  if (frame.hasAim) {
    cursor.x += config::kSmoothing * (frame.aim.x - cursor.x);
    cursor.y += config::kSmoothing * (frame.aim.y - cursor.y);
  }

  handleTrigger(frame, now);
  updateSolenoid(now);
  sendState(now);
  printDebug(frame, now);
}
