#include "ota_mode.h"

#include <Arduino.h>
#include <ArduinoOTA.h>
#include <WiFi.h>

#include "config.h"

void runOtaMode() {
  WiFi.mode(WIFI_AP);
  WiFi.softAP(config::kOtaSsid, config::kOtaPassword);

  ArduinoOTA.setHostname(config::kOtaHostname);
  ArduinoOTA.onStart([]() { Serial.println("update started"); });
  ArduinoOTA.onEnd([]() { Serial.println("update complete, restarting"); });
  ArduinoOTA.onError([](ota_error_t error) { Serial.printf("update failed: %u\n", error); });
  ArduinoOTA.begin();

  Serial.printf("update mode: join \"%s\", upload to %s\n", config::kOtaSsid,
                WiFi.softAPIP().toString().c_str());

  // Nothing else runs in this mode: no camera, no radio link to the receiver.
  while (true) {
    ArduinoOTA.handle();
    delay(1);
  }
}
