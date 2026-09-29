# Receiver Firmware

The cabinet half of the light gun link. An ESP32-S3 sits inside the cabinet with its native
USB port plugged into the Raspberry Pi, receives packets from the gun over ESP-NOW, and
presents them to the Pi as a USB pointing device. The gun's firmware is in
[`Gun-V2/Firmware`](../../Gun-V2/Firmware/README.md).

The Pi needs no drivers and no software: it sees a mouse-like device with absolute
coordinates, which is exactly what emulators expect from a light gun.

---

## Why a receiver at all

The Pi cannot hear ESP-NOW, Espressif's direct chip-to-chip protocol, and the alternatives
are worse. Bluetooth sends in scheduled intervals, which shows up as cursor lag and stutter,
and adds pairing to lose. Wi-Fi would mean writing a program on the Pi to turn packets into
a virtual mouse, keeping it running at boot, and maintaining it through Batocera updates that
replace the system files.

---

## What it does

The firmware is deliberately small. It declares a HID device with five buttons and 16-bit X
and Y axes, listens for ESP-NOW packets, and forwards each accepted one as a HID report.
Reports are sent only when something changes, and only when the USB host is ready for one.

Packets are filtered on a magic number, a protocol version and the gun ID, so a second gun on
the same channel is ignored unless this receiver is built for it.

If nothing arrives for 100 ms the receiver releases all buttons. A gun that runs out of
battery mid-shot therefore cannot leave the trigger held down on the Pi.

Nothing travels the other way. The solenoid fires on the trigger rather than on what happens
in the game, which would need MAME's output system feeding back through this link.

---

## Configuration

At the top of `src/main.cpp`:

| Constant         | Sets                                    |
| ---------------- | --------------------------------------- |
| `kRadioChannel`  | Wi-Fi channel, matched by the gun       |
| `kAcceptedGunId` | Which gun this receiver listens to      |
| `kLinkTimeoutMs` | Silence before all buttons are released |

The USB name is set in `setup()` with `USB.productName()` and is what the Batocera rule
matches. Changing one without the other stops Batocera recognising it as a gun.

One receiver serves one gun. A second player needs a second gun built with `kGunId = 2` and a
second receiver with `kAcceptedGunId = 2`.

---

## Building

```
pio run -t upload      # build and flash
pio device monitor     # link status
```

Two details of this board matter:

**Use the UART port for flashing, the USB port for the gun.** The DevKitC-1 has two USB
sockets. The UART one drives the board through a serial chip and resets it automatically for
uploads. the native USB one is the port that becomes the light gun and goes to the Pi. If
PlatformIO auto-detects the wrong one, `upload_port` and `monitor_port` in `platformio.ini`
pin it down.

**USB CDC must stay off at boot.** With `ARDUINO_USB_CDC_ON_BOOT=1` the core starts USB
before `setup()` runs, under the board's own name and without the HID device, so the Pi sees
an Espressif dev board rather than a light gun. `platformio.ini` sets it to 0, which also
sends `Serial` output to the UART port, where it is easier to read while the native port is
busy being the gun.

The same file adds the FS library's headers to the include path. The Arduino USB library
compiles its mass-storage sources whether or not they are used, and those include `FS.h`
without declaring the dependency.

---

## Batocera

Batocera treats an input device as a light gun when udev tags it `ID_INPUT_GUN`. The rule is
in [`Cabinet/Batocera/99-diy-gun.rules`](../Batocera/99-diy-gun.rules) and matches the USB
product name:

```
cp 99-diy-gun.rules /etc/udev/rules.d/
batocera-save-overlay
reboot
```

`batocera-save-overlay` is what makes the file survive a reboot, since Batocera's system
files are reset each time. To check it took effect, find the device's event number in
`/proc/bus/input/devices` and run:

```
udevadm info /dev/input/eventN | grep ID_INPUT_GUN
```

Batocera updates replace the system, so the rule has to be reinstalled afterwards. That is
why it lives in this repository rather than only on the Pi.

---

## Layout

| Path                   | Contents                                      |
| ---------------------- | --------------------------------------------- |
| `src/main.cpp`         | ESP-NOW receive, link timeout, HID reports    |
| `src/usb_gun_device.*` | HID device and its report descriptor          |
| `src/gun_packet.h`     | Packet format, an identical copy of the gun's |
| `platformio.ini`       | Board, USB mode and the FS include path       |

---

## Limitations

- The link is unencrypted broadcast. Anything within range that knows the format could send packets, which matters little for a cabinet but is worth knowing.
- The udev rule must be reinstalled after every Batocera update.

---

## Tools and process

The firmware was written with AI assistance (Claude): the tracking maths, the drivers, the
radio link and the host-side tests. It was then corrected on the hardware.
