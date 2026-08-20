# ARC-3 Detailed Setup Guide

## Contents
1. [Parts List Recap](#parts-list-recap)
2. [3D Printing](#3d-printing)
3. [Assembly](#assembly)
4. [Wiring](#wiring)
5. [Power Supply](#power-supply)
6. [Firmware Upload](#firmware-upload)
7. [Firmware Configuration](#firmware-configuration)
8. [GUI Setup](#gui-setup)
9. [Connecting](#connecting)
10. [Troubleshooting](#troubleshooting)

---

## Parts List Recap

See the BOM table in [README.md](README.md) for purchase links. Key components:

| Component | Role |
|---|---|
| Arduino Uno R4 WiFi | Main controller, runs firmware, hosts WiFi |
| PCA9685 Servo Driver | PWM controller for all 4 servos via I2C |
| 4x MG995 Servos | Yaw (base), shoulder (pitch), elbow (pitch), claw |
| 9V battery + switch | Powers the Arduino (switch wired to VIN and GND) |
| 6V 10A+ regulated power supply | Powers servos through PCA9685 V+ |
| 20 AWG stranded wire | Servo power bus (carries up to ~10A) |
| Jumper wires | I2C and signal connections |

---

## 3D Printing

All STL files are in the `CAD/` folder of the repo. Print with PLA or PETG at standard settings (0.2mm layer height, 20% infill is fine). The parts are designed so all electronics sit inside the base and arm body — nothing is visible from the outside when assembled.

---

## Assembly

After printing all the parts, assemble the arm before wiring anything up:

### Gear fitting
Some of the gears may not fit perfectly between the pegs out of the printer — the tolerances are what you might call "generous." If a gear is too tight to slide between the pegs on the arm pieces, trim the gear teeth slightly with a hobby knife or flush cutters until it fits. Take your time here; a little off each tooth goes a long way. The gears need to mesh smoothly but not bind, so aim for a snug fit that still spins freely.

### Securing the gears
Once the gears are in place on the arm pieces, insert a screw and washer into each peg on the arm_top to lock the gears down. This keeps them from sliding off during movement. Tighten until the gear is held firmly but still spins without excessive friction.

### Servo positioning
The slot for the servo on the arm_top is intentionally oversized — this is so you can adjust the servo's position both in height and side-to-side before tightening it down. Slide the servo around until its gear meshes cleanly with the arm gears, then secure it. Getting this alignment right is worth the extra minute; a well-aligned servo runs quieter, cooler, and with better grip.

### Spacers between arm pieces
There is a gap between the arm pieces when assembled. To fill this, create spacers by cutting a thin slice in TinkerCAD or a similar simple CAD editor, then print that piece at the exact height needed to fill the gap. Then glue the spacer onto the bottom piece of the connection so it sits flush. This keeps the arm pieces from flexing or shifting against each other during movement, and gives the whole joint a solid, unified feel.

### Servo horns
The servo horns do not fit in the slots out of the box — even with scaling and tolerances they're too tight. The best method is to use a soldering iron to melt/cut off a significant amount of material from the fins of the servo horn until it fits into the slot. Once it fits, glue it in place and add the screw to lock it down. This is much faster than trying to widen the slots themselves.

---

## Wiring

### PCA9685 connections

| PCA9685 Pin | Connect To |
|---|---|
| VCC | Arduino 5V pin (powers the PCA9685 logic) |
| GND | Arduino GND (common ground with power supply) |
| SDA | Arduino SDA (A4 on R4) |
| SCL | Arduino SCL (A5 on R4) |
| V+ | External power supply positive (6V) |
| V- (GND) | External power supply negative (GND) |

### Servo connections to PCA9685

| PCA9685 Channel | Servo | Function |
|---|---|---|
| 0 | MG995 #1 | Yaw (base rotation) |
| 1 | MG995 #2 | Shoulder (pitch) |
| 2 | MG995 #3 | Elbow (pitch) |
| 3 | MG995 #4 | Claw (gripper) |

Each servo has a 3-pin connector (signal / VCC / GND). Plug into the PCA9685 headers matching the channel — signal wire to the PCA9685 signal pin, power and ground to the outer pins.

### Power wiring

The Arduino is powered by a 9V battery wired through a simple switch to the VIN and GND pins on the Arduino. The PCA9685 VCC is plugged into the Arduino 5V pin for its own logic power. Run 20 AWG stranded wire from the external servo power supply's positive and negative terminals to the PCA9685's V+ and V- screw terminals. Do not power the servos from the Arduino's 5V pin — the servos will draw too much current and reset the board.

### Critical: common ground

The power supply GND, PCA9685 GND, and Arduino GND must all be connected together. Without a common ground, I2C signals will be unreliable and servos will glitch.

---

## Power Supply

This is the most important hardware decision. MG995 servos draw ~0.5A holding and up to ~2.5A at stall each.

### Recommended
A 6V, 10-12A regulated supply (e.g., a 6V/10A or 6V/12A AC-to-DC adapter). Set output to 5.8-6.0V if adjustable (MG995 spec is 4.8-6V; PCA9685 V+ max is 6V).

### Why 6V instead of 5V
Running at 6V gives noticeably more torque and headroom before servos stall. At 5V, the shoulder holding the full arm weight can drop when another servo starts moving — at 6V it holds firm.

### Wire gauge
20 AWG stranded wire works fine for the servo power bus. Thin jumper wires will sag under load and defeat the purpose of a beefy supply.

---

## Firmware Upload

### Option A: Arduino IDE
1. Install the Arduino IDE (2.x).
2. Go to Tools > Board > Boards Manager, search for `Arduino UNO R4 Boards`, and install it.
3. Open `ARC3_firmware/ARC3_firmware.ino`.
4. Select Tools > Board > Arduino UNO R4 WiFi.
5. Select Tools > Port > COM10 (or whichever port your board appears on).
6. Click Upload.

### Option B: arduino-cli (command line)
```bash
# Install (one time)
arduino-cli core install arduino:renesas_uno

# Compile
arduino-cli compile --fqbn arduino:renesas_uno:unor4wifi ARC3_firmware/

# Upload (replace COM10 with your port)
arduino-cli upload -p COM10 --fqbn arduino:renesas_uno:unor4wifi ARC3_firmware/
```

After upload, the board's serial monitor (115200 baud) will print the WiFi IP address and confirm servo initialization.

---

## Firmware Configuration

Open `ARC3_firmware/ARC3_firmware.ino` and edit the following at the top of the file:

### WiFi credentials
```cpp
const char* WIFI_SSID     = "YOUR_WIFI_NAME";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
```

### Static IP (recommended)
The firmware ships with a static IP so the board's address never changes between reboots:

```cpp
#define USE_STATIC_IP 1
#if USE_STATIC_IP
IPAddress LOCAL_IP(192, 168, 4, 73);
IPAddress GATEWAY_IP(192, 168, 4, 1);
IPAddress SUBNET_MASK(255, 255, 252, 0);
#endif
```

LOCAL_IP: Set this to a free address on your network (avoid the router's DHCP range). GATEWAY_IP: Your router's IP (usually 192.168.x.1). SUBNET_MASK: Usually `255.255.255.0` (or `255.255.252.0` for /22 networks — check your PC's Wi-Fi config to confirm).

If you prefer not to set a static IP, set `#define USE_STATIC_IP 0` and the board will use DHCP (the IP can change between reboots).

After editing, recompile and reupload.

---

## GUI Setup

The GUI (`arc-3.py`) requires only Python 3.8+ with its standard library. No pip install needed — tkinter, socket, threading, json, math, and csv are all built in.

```bash
python arc-3.py
```

### What the GUI provides
- Sliders for each servo angle (yaw, shoulder, elbow, claw)
- Touchpad for XY control with inverse kinematics
- Keyboard controls: Space = claw close, Ctrl = claw open
- Position save/load (.arc3 JSON format)
- Motion recording and playback
- Connection panel: USB (auto-detect) and WiFi

### Settings
The app saves your last WiFi IP and port to `arc3_config.json` automatically — you never need to edit the IP in code after the first successful connection.

---

## Connecting

### First time (USB)
1. Connect the Arduino to your PC via USB cable.
2. Launch `arc-3.py`.
3. Leave the connection field on AUTO and click CONNECT.
4. The app scans USB ports, finds the board, and connects.
5. The app auto-detects the board's WiFi IP from the STATUS response and saves it for next time.

### Subsequent use (WiFi)
1. Launch `arc-3.py`.
2. The saved IP should already be in the connection field.
3. Click CONNECT — the app connects over WiFi. No USB cable needed.

### If WiFi fails
The firmware auto-retries WiFi connection every 10 seconds, so it will come back online on its own. Plug in USB, hit CONNECT — the app re-learns the board's current IP. Make sure your PC and the board are on the same WiFi network. Disconnect any VPN (e.g., Proton VPN) before connecting — they block local network traffic.

### Servo test
The TEST SERVO button in the connection panel sweeps a single servo channel (0–3) back and forth. Use this to diagnose a dead servo or verify wiring. The claw is channel 3.

---

## Troubleshooting

### "timed out" on connect
Board may still be booting — wait 15 seconds after power-on. WiFi link may be weak — check distance to router, reduce interference. VPN active — disable it. The app retries 3 times automatically; if it still fails, plug in USB to verify the board is alive.

### Board not found on USB
Close Arduino Serial Monitor / any other serial terminal using the port. Check the USB cable is data-capable (not charge-only). Verify the port in Device Manager (should show as `Arduino UNO R4 WiFi`).

### Servos not moving
Check power supply is on and connected to PCA9685 V+/V-. Verify the PCA9685 I2C wiring (SDA/SCL). Use the TEST SERVO button to isolate a dead channel. Ensure the servo connector is oriented correctly (signal wire to the signal pin).

### Servos jittering or glitching
Power supply too weak — upgrade to 6V/10A+ and use thicker wires. Ensure all grounds are common (PSU, PCA9685, Arduino).

### One servo drops when another moves
Classic power sag — the moving servo's surge drops voltage below the holding servo's threshold. Fix: use 6V supply, thick wires, counterweight the upper arm to reduce shoulder holding load.

### WiFi connects but IP keeps changing
Enable `USE_STATIC_IP` in the firmware (see [Firmware Configuration](#firmware-configuration)). Or set a DHCP reservation on your router for the board's MAC address.
