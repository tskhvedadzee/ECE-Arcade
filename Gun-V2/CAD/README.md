# IR Light Gun for an Arcade Cabinet

A wireless light gun built from scratch for an arcade cabinet: a 3D-printed split shell,
an IR camera that tracks LEDs placed around the screen (3 IR leds wired in series in the
middle of each side and all four groups wired in parallel), a solenoid, and an ESP32.

The shell is generated from a parametric CAD script written around the exact parts in hand,
every internal holder sized from measured dimensions and checked for collisions before
printing. The script was written with AI assistance; the measuring, test printing and
design decisions behind it were mine.
See [Tools and process](#tools-and-process).

---

## How it works

Four groups of three infrared LEDs sit at the midpoints of the screen's edges.
The camera in the muzzle sees only IR and reports the positions of those four
points over I2C. From how that pattern is shifted, scaled and rotated in its view,
the ESP32 works out where the gun is pointing and sends it to the cabinet as pointer
movement. Pulling the trigger closes a microswitch. the ESP32 registers the shot and fires
the solenoid, whose plunger slams back into a stop to produce the recoil.

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

Printed in PETG on a Bambu lab P2S. The halves join with 6 × M3 heat-set inserts
and M3×12 screws. everything else inside is held by printed features.

---

## The shell

Roughly 187 mm long, 145 mm tall, 44 mm wide, in two halves split down the centreline.

Every component sits in a holder shaped for it.

A channel runs over the top of the solenoid, notched through both of its cradle ribs,
carrying wires from the back of the gun to the electronics at the front.

### Printing

Each half lies on its flat outside face, inside facing up. Supports are needed
**only under the trigger guard**; everything else is shaped to avoid them.

| Setting      | Value              |
| ------------ | ------------------ |
| Nozzle       | 0.4 mm             |
| Layer height | 0.2 mm             |
| Walls        | 3–4                |
| Infill       | 15–20%             |
| Supports     | trigger guard only |

Trigger is printed solid (100% infill).

### Test pieces

Small sections for checking fits cheaply, each well under an hour:

| File                   | Checks                                    |
| ---------------------- | ----------------------------------------- |
| `fit_test_front_*`     | camera nut pocket, bore, insert holes     |
| `fit_test_trigger_*`   | pivot, switch mount, spring post, stops   |
| `fit_test_butt_*`      | charger cradle and the USB-C opening      |
| `fit_test_esp32_*`     | ESP32 side guides                         |
| `fit_test_buck.stl`    | buck converter pocket                     |
| `fit_test_mosfet.stl`  | MOSFET pin and rails                      |
| `test_mosfet_clip.stl` | pin, dummy tab and clip, to test the snap |
| `test_insert.stl`      | one boss, to test a heat-set insert       |

---

## Wiring

| ESP32 pin       | Connects to                                                      |
| --------------- | ---------------------------------------------------------------- |
| 3V3             | Buck converter output (the camera's VCC comes off the same rail) |
| GND             | Ground, including the camera's black wire                        |
| GPIO21 / GPIO22 | Camera SDA (yellow) / SCL (green)                                |
| GPIO18          | Trigger microswitch COM, with `INPUT_PULLUP`; NO goes to ground  |
| GPIO33          | MOSFET gate, through a 100 Ω resistor                            |
| VIN             | **nothing**                                                      |

The converter is set to 3.3 V and feeds the ESP32's 3V3 pin directly, bypassing the
board's own regulator. Output should be measured before connecting anything: the 3V3 pin has
no protection.

Four details that protect the hardware:

1. **Flyback diode across the solenoid**, band toward the positive side. Without it,
   the collapsing coil spikes the MOSFET.
2. **10 kΩ gate pulldown**, from gate to source. The ESP32's pins float at boot, and
   without it the solenoid can fire at power-up.
3. **The MOSFET must be logic-level.** A standard IRF520 or IRFZ44N barely conducts
   at 3.3 V and overheats.
4. **The solenoid's ground runs on its own wire** from the MOSFET's source to the BMS,
   ot shared with the ESP32's ground. Its 2.8 A pulses would otherwise disturb the logic.

---

## Build order

1. Press the 6 heat-set inserts into the left half.
2. Screw a nut onto the camera
3. Fit the battery pack, charger, solenoid, ESP32, buck converter, microswitch, trigger and
   spring into the left half.
4. Fit the MOSFET at the rear of the right half: tab over the pin, then slide the
   clip into the pin's groove. Solder its resistors onto the legs.
5. Run the wires, using the channel over the solenoid for the three that cross front to
   back.
6. Close with the right half and its 6 screws, checking no wire is trapped in the seam.
7. Feed the power switch's wires out the back, solder, and snap it in.
8. Lock the camera with the second nut from the front.

---

## Design decisions

**Printed trigger instead of the bought one.** A trigger kit was ordered first, but
its pivot pegs sit in a corner, which forces the switch into awkward positions in
this layout. Designing the trigger alongside the shell let the pivot, arm, stops
and spring all be positioned together.

**The click doesn't depend on knowing where the switch clicks.** Rather than measuring
the microswitch's operating point, the trigger drives the roller to 0.5 mm short of the
lever lying flat. Every switch of this type clicks before that point, so the mechanism
works without a spec sheet.

**The spring anchors are adjustable by design.** The torsion spring's free leg angle was
unknown, so instead of guessing one anchor position, four fins cover a range of angles so
whichever gives the tension can be picked.

**The empty space was mapped, not eyeballed.** Late in the design the inside was
searched for routes between every pair of components. That turned up a problem:
the solenoid's cradle walled the back of the gun off from the front,
leaving room for no wire where three were needed. Hence the channel over the
solenoid.

**Measure, then move.** Several parts moved after measurements of test prints
contradicted estimates.

**Everything is parametric.** `gun.py` regenerates all geometry from named dimensions.
Correcting a measurement is a one-line change, and every revision was re-checked for
collisions across the trigger's full travel before export.

---

## Tools and process

The CAD is a Python library where geometry is code, so the whole shell is a script
written with AI assistance (Claude) and then remodeled after printing and checking
the fitting and measurements.

---

## Repository layout

```
cad/          gun.py, the parametric source
stl/          printable files
step/         CAD-editable files
fit_tests/    small sections for checking fits
electronics/  schematic
firmware/     ESP32 code
photos/       photos of prints and assembly
```

---

## Notes

The design is specific to the parts listed above.
