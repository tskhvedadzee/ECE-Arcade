# Gun-V2

A wireless IR light gun for the arcade cabinet: a 3D-printed split shell, an IR camera that
tracks LED markers around the screen, a solenoid that kicks on every shot, and an ESP32 that
ties it together. It talks to a receiver in the cabinet, which the Raspberry Pi sees as an
ordinary USB light gun.

| Folder      | Contents                                                              |
| ----------- | --------------------------------------------------------------------- |
| `CAD/`      | The parametric shell: source script, STLs, STEPs, fit tests, printing |
| `Scripts/`  | Supporting scripts                                                    |
| `Firmware/` | The ESP32 code: tracking, trigger, recoil, radio link                 |

The cabinet side is in [`Cabinet/Receiver-Firmware`](../Cabinet/Receiver-Firmware/README.md).

---

## How it works

Four groups of three infrared LEDs sit at the midpoints of the screen's edges, three in
series per group and the four groups in parallel, powered from the cabinet. The camera in the
muzzle sees only IR and reports the position of each group over I2C. From how that pattern is
shifted, scaled and rotated in its view, the ESP32 works out where the gun is pointing and
sends it to the cabinet, which passes it to the Pi as pointer movement. Pulling the trigger
closes a microswitch. the ESP32 registers the shot and fires the solenoid, whose plunger
slams back into a stop to produce the recoil.

```
IR markers --> camera --I2C--> ESP32 (gun) --ESP-NOW--> receiver --USB--> Raspberry Pi
```

The maths behind the tracking, and the three modes the gun can start in, are described in the
[firmware README](Firmware/README.md).

---

## Hardware

| Part           | Detail                                                                          |
| -------------- | ------------------------------------------------------------------------------- |
| Camera         | DFRobot SEN0158 IR positioning camera, M18 thread, I2C, 33° × 23° field of view |
| Controller     | ESP32 DevKit (WROOM-32)                                                         |
| Recoil         | JF-1039B solenoid, 6 V, 10 mm stroke, 25 N                                      |
| Battery        | 4 × 18650 in 2S2P (7.4 V) with a protection board                               |
| Charging       | Z-6732-V4.0, USB-C in, charges 2S to 8.4 V at up to 1.5 A                       |
| Regulation     | Buck module set to 3.3 V, feeding the ESP32 and the camera                      |
| Switching      | IRL540N logic-level MOSFET, 1N5404 flyback diode                                |
| Trigger        | Roller-lever microswitch with a torsion spring return                           |
| Screen markers | 12 × IR LEDs, powered from the cabinet                                          |

Printed in PETG on a Bambu Lab P2S. The halves join with 6 × M3 heat-set inserts and M3×12
screws. everything else inside is held by printed features. Print settings, fit tests and the
shell's design are in the [CAD README](CAD/README.md).

---

## Wiring

| ESP32 pin       | Connects to                                                      |
| --------------- | ---------------------------------------------------------------- |
| 3V3             | Buck converter output (the camera's VCC comes off the same rail) |
| GND             | Ground, including the camera's black wire                        |
| GPIO21 / GPIO22 | Camera SDA (yellow) / SCL (green)                                |
| GPIO18          | Trigger microswitch COM, with `INPUT_PULLUP`. NO goes to ground  |
| GPIO33          | MOSFET gate, through a 100 Ω resistor                            |
| VIN             | **nothing**                                                      |

The converter is set to 3.3 V and feeds the ESP32's 3V3 pin directly, bypassing the board's
own regulator. Output should be measured before connecting anything: the 3V3 pin has no
protection.

Four details that protect the hardware:

1. **Flyback diode across the solenoid**, band toward the positive side. Without it, the
   collapsing coil spikes the MOSFET.
2. **10 kΩ gate pulldown**, from gate to source. The ESP32's pins float at boot, and without
   it the solenoid can fire at power-up.
3. **The MOSFET must be logic-level.** A standard IRF520 or IRFZ44N barely conducts at 3.3 V
   and overheats.
4. **The solenoid's ground runs on its own wire** from the MOSFET's source to the BMS, not
   shared with the ESP32's ground. Its 2.8 A pulses would otherwise disturb the logic.

---

## Using it

| Action              | How                                                                         |
| ------------------- | --------------------------------------------------------------------------- |
| Play                | Switch on. the receiver picks the gun up within a second                    |
| Calibrate           | Hold the trigger while switching on, release, aim at the centre, pull       |
| Update the firmware | Hold the trigger through power-on for 5 s, then upload over the gun's Wi-Fi |
| Charge              | USB-C at the back. the gun can be used while charging                       |

Calibration is stored in flash and survives power cycles and firmware updates. It needs
redoing only if the camera moves or the marker positions change.

The camera needs to see all four markers to start tracking, which sets a minimum playing
distance of roughly 70 cm for a 19-inch screen.

---

## Tools and process

The CAD is a Python library where geometry is code, so the whole shell is a script written
with AI assistance (Claude) and then remodeled after printing and checking the fitting and
measurements. The firmware was written the same way and then corrected on the hardware.

---

## Notes

The design is specific to the parts listed above. Dimensions live at the top of the CAD
script and the firmware's `config.h` rather than in the exported files, so a corrected
measurement is a one-line change in both.
