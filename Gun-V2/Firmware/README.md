# Gun-V2 Firmware

The code that runs on the ESP32 inside the gun: it reads the IR camera, works out where the
gun is pointing, and sends that to the cabinet over ESP-NOW. The other half of the link, an
ESP32-S3 that plugs into the Raspberry Pi and appears to it as a USB light gun, is in
[`Cabinet/Receiver-Firmware`](../../Cabinet/Receiver-Firmware/README.md).

---

## How aiming works

The camera does the hard part in hardware: the sensor inside the SEN0158 finds bright IR
spots itself and reports up to four of them over I2C, in a 1024 × 768 coordinate space. No
image processing runs on the ESP32. Each group of three LEDs on the screen reads as one
point.

Each frame the firmware then:

1. **Decides which point is which.** In a diamond layout every marker lies on an axis through
   the centre of the pattern, so from the points' centroid they sit at 12, 3, 6 and 9
   o'clock. The labelling picks the assignment closest to that, which holds with the gun
   rolled up to about ±45°.
2. **Replaces markers that have left the camera's view.** With three visible it fits an
   affine transform to the last complete frame. with two, a similarity transform. Below two,
   tracking is lost and a shot counts as off-screen.
3. **Solves a homography** from the four positions in the image to the four known positions
   on the screen. Four point pairs give an exact perspective transform, so the result holds
   from any angle or distance.
4. **Maps the boresight through it.** The boresight is the camera pixel the sights line up
   with, found by calibration. mapped through the homography it gives the aim point.

A trigger pull while aiming off-screen is sent as the right mouse button, which MAME's
`offscreen_reload` option treats as a reload.

---

## Modes

| Mode        | Entered by                                       | Behaviour                                                                             |
| ----------- | ------------------------------------------------ | ------------------------------------------------------------------------------------- |
| Normal      | Power on                                         | Tracks, transmits, fires the solenoid on each shot                                    |
| Calibration | Hold the trigger while powering on, then release | The next pull stores the boresight instead of shooting. the solenoid kicks to confirm |
| Update      | Hold the trigger through power-on for 5 s        | Starts a Wi-Fi access point and waits for a firmware upload. nothing else runs        |

Calibration corrects for the camera not being mounted exactly parallel to the barrel. With
the sights on the centre of the screen, the inverse homography maps the screen centre back
into camera coordinates, and that pixel is stored in flash. If the markers are not in view
the pull is ignored and calibration stays armed. It needs redoing after the camera moves or
the marker positions change. ordinary power cycles keep it.

Update mode exists because the shell closes with six screws and heat-set inserts. The gun
hosts its own network rather than joining one, so it also works on networks that isolate
clients from each other.

---

## Configuration

Everything tunable is in `include/config.h`. Pin assignments are there too. the wiring itself
is in the [gun README](../README.md).

| Constant                        | Sets                                                                                |
| ------------------------------- | ----------------------------------------------------------------------------------- |
| `kLedScreen`                    | Marker positions in screen coordinates, measured from the edge of the visible image |
| `kCameraFlipX` / `kCameraFlipY` | Camera orientation in the shell                                                     |
| `kSolenoidPulseMs`              | Length of the kick                                                                  |
| `kRadioChannel` / `kGunId`      | Radio settings, matched by the receiver                                             |
| `kKeepAliveMs`                  | Resend interval when nothing changes                                                |
| `kSmoothing`                    | Cursor smoothing. 1.0 disables it                                                   |
| `kOtaSsid` / `kOtaPassword`     | The update-mode access point                                                        |

Measuring the marker offsets is worth doing carefully: the aim can be right at the centre of
the screen and drift at the corners if they are wrong. The values are normalised against the
visible picture, so a marker 14 mm outside a 376.3 mm wide image sits at -0.037 and 1.037.

---

## Building

VS Code with the pioarduino extension, or the PlatformIO CLI. The official PlatformIO ESP32
platform does not ship Arduino core 3.x, so `platformio.ini` points at the pioarduino fork.

```
pio run -t upload      # build and flash over USB
pio device monitor     # tracking, aim point and mode changes
pio test -e native     # tracking maths, run on the host
```

Flashing an assembled gun: put it in update mode, join `GunV2-Update` from the computer, then

```
pio run -e esp32_ota -t upload
```

---

## Tests

`test/test_tracking/` runs on the computer, not the ESP32. It models a pinhole camera with
the SEN0158's field of view, 33° × 23° over 1024 × 768, aimed at a 600 × 338 mm screen,
projects the four markers into it, and compares the computed aim point with the true one.

| Test        | Checks                                                                  |
| ----------- | ----------------------------------------------------------------------- |
| Homography  | Maps its own reference points; rejects collinear input                  |
| Labelling   | Correct marker identities with the gun rolled ±40°                      |
| Accuracy    | Aim error under 2 mm at 1.2–2.5 m, off-centre and rolled                |
| Dropouts    | Tracking survives markers leaving the view when aiming into the corners |
| Calibration | Removes a 1.5° horizontal, 1.0° vertical camera misalignment            |

The maths lives in `lib/tracking/` with no Arduino dependency, which is what makes it
testable this way.

---

## Radio link

Each packet carries the complete input state, aim position and buttons, rather than events,
and is sent on every change plus every 5 ms regardless. A dropped packet therefore delays the
cursor by one interval and can never lose a trigger pull.

The packet format is in `src/gun_packet.h`, with an identical copy in the receiver, which
also decides what happens when the gun goes quiet.

---

## Layout

| Path                  | Contents                                                     |
| --------------------- | ------------------------------------------------------------ |
| `include/config.h`    | Pins, marker positions, radio and timing settings            |
| `lib/tracking/`       | Homography, marker labelling, aim and calibration, plain C++ |
| `src/ir_camera.*`     | SEN0158 driver, including I2C bus recovery                   |
| `src/radio_link.*`    | ESP-NOW transmitter                                          |
| `src/ota_mode.*`      | Update-mode access point                                     |
| `src/gun_packet.h`    | Packet format, shared with the receiver                      |
| `src/main.cpp`        | Main loop and mode selection                                 |
| `test/test_tracking/` | Host-side tests for `lib/tracking`                           |

---

## What the hardware changed

The tracking maths worked the first time it ran on real markers. Everything that needed
fixing afterwards was electrical or physical, and none of it was visible in simulation.

**The camera's orientation is a setting, not an assumption.** Mounted in the shell it sits
rotated, so the aim moved opposite to the gun. Two flip flags handle any mounting angle.
baking an orientation into the maths would have meant reprinting.

**A stuck I2C bus used to kill the gun permanently.** A transfer interrupted by an electrical
glitch leaves the sensor holding the data line low, and every read after that fails with
`ESP_ERR_INVALID_STATE`. The driver now counts consecutive failures, clocks the bus manually
to free the line, and re-initialises the sensor, so tracking returns instead of the gun going
dead until a power cycle.

---

## Limitations

- Below about 1.8 × the screen width, the side markers fall outside the camera's field of
  view even when aiming at the centre, and tracking cannot start. For a 19-inch screen that
  is roughly 70 cm, and about a metre for the corners to track cleanly.
- Each group of three LEDs must read as a single point. Spreading a group wider, or playing
  very close to the screen, would let the camera report them separately and break the
  labelling.
- The two-marker estimate assumes the pattern's shape has not changed since the last full
  frame. In simulation the error near the corners at 1.2 m reaches about 1 cm.
- Marker labelling assumes the gun is held within about ±45° of upright.
- The solenoid is switched fully on for the length of the pulse. The pack sits above the
  solenoid's rated voltage, so the pulse is kept short rather than regulated.
- Update mode is entered with the trigger, so firmware that crashes before reaching it can
  only be recovered over USB.

---

## Tools and process

The firmware was written with AI assistance (Claude): the tracking maths, the drivers, the
radio link and the host-side tests. It was then corrected on the hardware.
