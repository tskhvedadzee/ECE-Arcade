#pragma once

#include <Arduino.h>

// Active-low push button with leading-edge debounce: a change is reported on
// the first sample, then further changes are ignored for the lockout period.
// This adds no latency to the trigger, unlike a wait-until-stable debounce.
//
// The initial state is sampled in begin(), so a button held at power-on
// reports its release rather than a press.
class Button {
 public:
  Button(int pin, uint32_t lockoutMs) : pin_(pin), lockoutMs_(lockoutMs) {}

  void begin() {
    pinMode(pin_, INPUT_PULLUP);
    delay(1);  // pull-up settling time before the first sample
    pressed_ = digitalRead(pin_) == LOW;
  }

  // Samples the pin. Returns true if the pressed state changed.
  bool update(uint32_t nowMs) {
    const bool raw = digitalRead(pin_) == LOW;
    if (raw == pressed_ || static_cast<int32_t>(nowMs - lockedUntilMs_) < 0) return false;
    pressed_ = raw;
    lockedUntilMs_ = nowMs + lockoutMs_;
    return true;
  }

  bool pressed() const { return pressed_; }

 private:
  int pin_;
  uint32_t lockoutMs_;
  bool pressed_ = false;
  uint32_t lockedUntilMs_ = 0;
};
