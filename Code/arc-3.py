import tkinter as tk
from tkinter import filedialog, simpledialog
import socket
import threading
import json
import math
import time
import os
import csv
import ctypes
from ctypes import wintypes
from datetime import datetime
try:
    import winreg
except ImportError:
    winreg = None

DEFAULT_USB_PORT = "AUTO"
PREFERRED_USB_PORT = "COM10"
DEFAULT_WIFI_IP  = "PutYourIPHere"  # fallback WiFi IP from serial monitor
DEFAULT_IP       = DEFAULT_USB_PORT
DEFAULT_PORT = 8888

UPDATES_PER_SECOND    = 50    # 50 Hz control loop
DEADBAND_DEGREES      = 0.10  # Keep sending useful small target changes
DEGREES_PER_STEP      = 4.0   # Fixed-rate arm motion per 20ms tick
CLAW_DEGREES_PER_STEP = 0.9   # Slower claw motion per 20ms tick

UPPER_ARM_LENGTH = 130.0  # shoulder to elbow in mm
LOWER_ARM_LENGTH = 125.0  # elbow to wrist in mm

SERVO_LIMITS = {         # [min_angle, max_angle] for each servo
    0: [0,   180],       # yaw
    1: [0,   260],       # shoulder (270°-type MG995; measured ~260° physical)
    2: [0,   180],       # elbow
    3: [0,   180],       # claw 
}

HOME_POSITION      = [90.0, 70.0, 90.0, 0.0]  # starting angles
POSITIONS_FILE     = "arc3_positions.json"      # saved positions persist here
CONFIG_FILE        = "arc3_config.json"         # GUI settings persist here (last WiFi IP/port)

def load_app_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_app_config(cfg):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass

BG       = "#000000"   # black background
PANEL    = "#041008"   # black-green panel background
PANEL2   = "#071A0D"   # slightly lighter panel
BORDER   = "#176B36"   # green panel borders
ORANGE   = "#37D67A"   # primary green accent
ORANGE_L = "#8FF0B2"   # lighter green highlight
ORANGE_D = "#0B4D25"   # dark green button background
WHITE    = "#D9FFE4"
GREY     = "#5BA66F"
DGREY    = "#245C34"
GREEN    = "#37D67A"   # connected / success
RED      = "#1FA85A"   # stop/error uses green to keep the theme strict
YELLOW   = "#A6EFB7"   # warning uses light green to keep the theme strict
GRID     = "#0C2D16"   # canvas grid lines
SHADOW   = "#000000"

RECORDING_FILETYPES = [
    ("ARC-3 motion JSON", "*.arc3"),
    ("CSV motion", "*.csv"),
    ("All files", "*.*"),
]

FONT_HEAD = ("Courier New", 15, "bold")
FONT_MED  = ("Courier New", 10, "bold")
FONT_NORM = ("Courier New", 9)
FONT_SM   = ("Courier New", 8)
FONT_XS   = ("Courier New", 7)

# inverse kinematics
# given a target 3D position, solve what joint angles are needed.
# uses law of cosines on the two-link arm triangle.

class InverseKinematics:
    def __init__(self):
        self.upper    = UPPER_ARM_LENGTH
        self.lower    = LOWER_ARM_LENGTH
        self.elbow_up = True   # which of the two valid IK solutions to prefer

    def solve(self, reach, height, yaw):
        reach    = max(0.0, float(reach))
        height   = float(height)
        yaw      = max(SERVO_LIMITS[0][0], min(SERVO_LIMITS[0][1], float(yaw)))
        dist     = math.sqrt(reach**2 + height**2)
        max_dist = self.upper + self.lower
        min_dist = abs(self.upper - self.lower)

        result = {"can_reach": False, "yaw": yaw,
                  "shoulder": HOME_POSITION[1], "elbow": HOME_POSITION[2]}
        if dist > max_dist or dist < min_dist or dist < 0.001:
            return result

        # q1 and q2 match get_endpoint(): shoulder = 90-q1,
        # elbow servo = 180 - bend angle. Higher elbow values are straighter.
        cos_e = (dist**2 - self.upper**2 - self.lower**2) / (2 * self.upper * self.lower)
        cos_e = max(-1.0, min(1.0, cos_e))
        elbow_mag = math.acos(cos_e)
        preferred = [elbow_mag, -elbow_mag] if self.elbow_up else [-elbow_mag, elbow_mag]

        candidates = []
        for q2 in preferred:
            k1 = self.upper + self.lower * math.cos(q2)
            k2 = self.lower * math.sin(q2)
            q1 = math.atan2(height, reach) - math.atan2(k2, k1)
            sh = 90.0 - math.degrees(q1)
            el = 180.0 - abs(math.degrees(q2))
            sh = self._clamp_servo(1, sh)
            el = self._clamp_servo(2, el)
            x, y = self.get_endpoint(sh, el)
            error = math.hypot(x - reach, y - height)
            candidates.append((error, sh, el))

        if not candidates:
            return result

        _, sh, el = min(candidates, key=lambda item: item[0])
        result.update({"shoulder": sh, "elbow": el, "can_reach": True})
        return result

    def _within_servo_limits(self, idx, angle):
        lo, hi = SERVO_LIMITS[idx]
        return lo <= angle <= hi

    def _clamp_servo(self, idx, angle):
        lo, hi = SERVO_LIMITS[idx]
        return max(lo, min(hi, angle))

    def get_endpoint(self, sh_deg, el_deg):
        # forward kinematics: given angles, where is the tip? (used for visualizer)
        q1 = math.radians(90.0 - sh_deg)
        bend = 180.0 - el_deg
        q2 = math.radians(bend if self.elbow_up else -bend)
        x  = self.upper * math.cos(q1) + self.lower * math.cos(q1 + q2)
        y  = self.upper * math.sin(q1) + self.lower * math.sin(q1 + q2)
        return x, y


class WindowsSerialPort:
    GENERIC_READ  = 0x80000000
    GENERIC_WRITE = 0x40000000
    OPEN_EXISTING = 3
    INVALID_HANDLE_VALUE = wintypes.HANDLE(-1).value
    PURGE_RXCLEAR = 0x0008
    PURGE_TXCLEAR = 0x0004

    class COMMTIMEOUTS(ctypes.Structure):
        _fields_ = [
            ("ReadIntervalTimeout", wintypes.DWORD),
            ("ReadTotalTimeoutMultiplier", wintypes.DWORD),
            ("ReadTotalTimeoutConstant", wintypes.DWORD),
            ("WriteTotalTimeoutMultiplier", wintypes.DWORD),
            ("WriteTotalTimeoutConstant", wintypes.DWORD),
        ]

    def __init__(self, port, baud=115200):
        if os.name != "nt":
            raise RuntimeError("USB serial fallback only supports Windows")
        self.kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self.kernel32.CreateFileW.restype = wintypes.HANDLE
        self.kernel32.CreateFileW.argtypes = [
            wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID,
            wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE
        ]
        self.kernel32.ReadFile.argtypes = [
            wintypes.HANDLE, wintypes.LPVOID, wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID
        ]
        self.kernel32.WriteFile.argtypes = [
            wintypes.HANDLE, wintypes.LPCVOID, wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID
        ]
        self.kernel32.EscapeCommFunction.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        self.handle = None
        self.port = port.strip()
        if not self.port.upper().startswith("COM"):
            raise ValueError("serial port must look like COM3")
        name = "\\\\.\\" + self.port.upper()
        handle = self.kernel32.CreateFileW(
            name, self.GENERIC_READ | self.GENERIC_WRITE, 0, None,
            self.OPEN_EXISTING, 0, None
        )
        if handle == self.INVALID_HANDLE_VALUE:
            raise OSError(ctypes.get_last_error(), f"Could not open {self.port}")
        self.handle = handle
        self._configure(baud)

    def _configure(self, baud):
        dcb = ctypes.create_string_buffer(28)
        ctypes.memset(dcb, 0, ctypes.sizeof(dcb))
        ctypes.cast(dcb, ctypes.POINTER(wintypes.DWORD))[0] = ctypes.sizeof(dcb)
        config = f"baud={baud} parity=N data=8 stop=1"
        if not self.kernel32.BuildCommDCBA(config.encode("ascii"), dcb):
            raise OSError(ctypes.get_last_error(), "BuildCommDCB failed")
        if not self.kernel32.SetCommState(self.handle, dcb):
            raise OSError(ctypes.get_last_error(), "SetCommState failed")
        timeouts = self.COMMTIMEOUTS(20, 0, 20, 0, 200)
        if not self.kernel32.SetCommTimeouts(self.handle, ctypes.byref(timeouts)):
            raise OSError(ctypes.get_last_error(), "SetCommTimeouts failed")
        self.kernel32.PurgeComm(self.handle, self.PURGE_RXCLEAR | self.PURGE_TXCLEAR)
        # Uno R4 (TinyUSB CDC) only activates the serial link when DTR is set;
        # without this the board silently ignores all writes and never sends.
        if not self.kernel32.EscapeCommFunction(self.handle, 5):  # SETDTR
            raise OSError(ctypes.get_last_error(), "SetDTR failed")

    def write(self, data):
        if isinstance(data, str):
            data = data.encode()
        written = wintypes.DWORD(0)
        buf = ctypes.create_string_buffer(data)
        ok = self.kernel32.WriteFile(self.handle, buf, len(data), ctypes.byref(written), None)
        if not ok:
            raise OSError(ctypes.get_last_error(), "Serial write failed")

    def read(self, size=256):
        buf = ctypes.create_string_buffer(size)
        read = wintypes.DWORD(0)
        ok = self.kernel32.ReadFile(self.handle, buf, size, ctypes.byref(read), None)
        if not ok:
            raise OSError(ctypes.get_last_error(), "Serial read failed")
        return bytes(buf.raw[:read.value])

    def close(self):
        if self.handle:
            self.kernel32.CloseHandle(self.handle)
            self.handle = None


class ArmConnection:
    def __init__(self):
        self.socket     = None
        self.serial     = None
        self.mode       = "wifi"
        self.active_target = ""
        self.lock       = threading.Lock()
        self.connected  = False
        self.last_error = ""

    def connect(self, ip, port):
        self.disconnect()
        ip = ip.strip()
        if self._is_serial_target(ip):
            port_name = self._serial_port_name(ip)
            if port_name.upper() == "AUTO":
                return self.connect_serial_auto()
            return self.connect_serial(port_name)
        last_err = None
        for attempt in range(3):
            s = None
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                s.settimeout(8.0)
                s.connect((ip, port))
                s.settimeout(5.0)
                with self.lock:
                    self.socket    = s
                    self.serial    = None
                    self.mode      = "wifi"
                    self.active_target = ip
                    self.connected = True
                return True
            except Exception as e:
                last_err = e
                try: s.close()
                except: pass
                time.sleep(0.8)
        self.last_error = str(last_err)
        self.connected  = False
        return False

    def _is_serial_target(self, target):
        t = target.lower()
        return t in ("auto", "usb") or t.startswith("serial:") or t.startswith("com")

    def _serial_port_name(self, target):
        if target.lower().startswith("serial:"):
            name = target.split(":", 1)[1].strip()
            return name or "AUTO"
        if target.lower() == "usb":
            return "AUTO"
        return target.strip()

    def connect_serial_auto(self):
        errors = []
        for port_name in self._candidate_serial_ports():
            if self.connect_serial(port_name, ping_timeout=2.0):
                return True
            errors.append(f"{port_name}: {self.last_error}")
        self.last_error = "No USB Arduino answered PING. " + "; ".join(errors[:6])
        if errors:
            self.last_error += "  -> Close Arduino Serial Monitor/IDE, check cable, or type the exact COM port."
        self.connected = False
        return False

    def _candidate_serial_ports(self):
        ports = [PREFERRED_USB_PORT]
        ports.extend(self._arduino_preference_ports())
        ports.extend(self._windows_serial_ports())
        seen = set()
        ordered = []
        for port in ports:
            port = port.strip().upper()
            if port.startswith("COM") and port not in seen:
                seen.add(port)
                ordered.append(port)
        return sorted(ordered, key=self._serial_sort_key)

    def _serial_sort_key(self, port):
        if port == PREFERRED_USB_PORT:
            return (-1, 0)
        try:
            return (0, int(port[3:]))
        except:
            return (1, port)

    def _arduino_preference_ports(self):
        paths = [
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Arduino15", "preferences.txt"),
            os.path.join(os.environ.get("APPDATA", ""), "Arduino15", "preferences.txt"),
        ]
        ports = []
        for path in paths:
            if not path or not os.path.exists(path):
                continue
            try:
                with open(path, errors="ignore") as f:
                    for line in f:
                        if "serial.port=" in line or "upload.port=" in line:
                            value = line.split("=", 1)[1].strip()
                            if value.upper().startswith("COM"):
                                ports.append(value)
            except:
                pass
        return ports

    def _windows_serial_ports(self):
        if winreg is None:
            return []
        ports = []
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DEVICEMAP\SERIALCOMM") as key:
                i = 0
                while True:
                    try:
                        _, value, _ = winreg.EnumValue(key, i)
                        if str(value).upper().startswith("COM"):
                            ports.append(str(value))
                        i += 1
                    except OSError:
                        break
        except:
            pass
        return ports

    def connect_serial(self, port_name, ping_timeout=4.0):
        last_error = ""
        for attempt in range(2):
            serial_port = None
            try:
                serial_port = WindowsSerialPort(port_name, 115200)
                time.sleep(1.5)  # Arduino resets when the USB serial port opens.
                with self.lock:
                    self.socket = None
                    self.serial = serial_port
                    self.mode = "serial"
                    self.active_target = port_name
                    self.connected = True
                    self._drain_pending_locked()
                    serial_port.write(b"PING\n")
                    reply = self._read_serial_response_locked("PING", timeout=ping_timeout)
                    if reply != b"PONG":
                        raise RuntimeError(f"{port_name} opened, but Arduino did not answer PING")
                return True
            except Exception as e:
                last_error = str(e)
                try:
                    serial_port.close()
                except:
                    pass
                self.serial = None
                self.connected = False
                # The Uno R4 WiFi re-enumerates its USB when the port opens
                # (reset-on-open), which kills the first handle with an
                # "invalid handle" write/read error. Reopen once it settles.
                msg = str(e).lower()
                stale_handle = ("write failed" in msg or "read failed" in msg or "invalid handle" in msg)
                if not stale_handle:
                    break
                time.sleep(2.0)   # let the board boot & re-enumerate
        self.last_error = last_error
        return False

    def disconnect(self):
        with self.lock:
            if self.socket:
                try: self.socket.close()
                except: pass
                self.socket = None
            if self.serial:
                try: self.serial.close()
                except: pass
                self.serial = None
            self.connected = False

    def send_command(self, cmd):
        """ Blocking send for status queries (PING/GET) """
        with self.lock:
            if not self.connected: return ""
            try:
                self._drain_pending_locked()
                line = (cmd.strip() + "\n").encode()
                if self.mode == "serial":
                    self.serial.write(line)
                    data = self._read_serial_response_locked(cmd)
                else:
                    self.socket.sendall(line)
                    data = b""
                    while not data.endswith(b"\n"):
                        chunk = self.socket.recv(256)
                        if not chunk: break
                        data += chunk
                return data.decode().strip()
            except socket.timeout:
                self.last_error = "timeout"
                return ""
            except Exception as e:
                self.last_error = str(e)
                self.connected  = False
                return ""

    def _drain_pending_locked(self):
        if self.mode == "serial" and self.serial:
            deadline = time.time() + 0.15
            while time.time() < deadline:
                if not self.serial.read(256):
                    break
            return
        if self.socket:
            old_timeout = self.socket.gettimeout()
            self.socket.setblocking(False)
            try:
                while True:
                    try:
                        if not self.socket.recv(512):
                            break
                    except BlockingIOError:
                        break
            finally:
                self.socket.settimeout(old_timeout)

    def _read_serial_response_locked(self, cmd, timeout=2.0):
        deadline = time.time() + timeout
        cmd = cmd.strip().upper()
        data = b""
        while time.time() < deadline:
            chunk = self.serial.read(256)
            if chunk:
                data += chunk
                while b"\n" in data:
                    line, data = data.split(b"\n", 1)
                    line = line.strip()
                    if self._is_protocol_reply(cmd, line):
                        return line
        return b""

    def _is_protocol_reply(self, cmd, line):
        if not line:
            return False
        if cmd == "PING":
            return line == b"PONG"
        if cmd == "STATUS":
            return line.startswith((b"IP:", b"USB:", b"{"))
        if cmd == "GET":
            return line.count(b",") >= 3
        return line in (b"OK", b"ERR:BAD_FORMAT", b"ERR:UNKNOWN")

    def send_command_nowait(self, cmd):
        """ Streaming non-blocking send (eliminates movement lag) """
        with self.lock:
            if not self.connected: return
            try:
                line = (cmd.strip() + "\n").encode()
                if self.mode == "serial":
                    self.serial.write(line)
                else:
                    self.socket.sendall(line)
            except socket.timeout:
                pass
            except Exception as e:
                self.last_error = str(e)
                self.connected  = False

    def ping(self):
        return self.send_command("PING") == "PONG"


class AISocket:
    def __init__(self, app, port=9999):
        self.app     = app
        self.port    = port
        self.running = False
        self.server  = None

    def start(self):
        self.running = True
        threading.Thread(target=self._run, daemon=True).start()

    def stop(self):
        self.running = False
        if self.server:
            try: self.server.close()
            except: pass

    def _run(self):
        self.server = None
        for port in (self.port, self.port + 1, self.port + 2):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(("127.0.0.1", port))
                s.listen(2)
                s.settimeout(1.0)
                self.server = s
                self.port   = port
                break
            except OSError as e:
                print(f"[ARC-3] AI socket bind {port} failed: {e}")
                try: s.close()
                except: pass
        if self.server is None:
            print("[ARC-3] WARNING: could not bind AI socket. Another ARC-3 instance may already be running.")
            return
        while self.running:
            try:
                conn, _ = self.server.accept()
                threading.Thread(target=self._handle, args=(conn,), daemon=True).start()
            except socket.timeout:
                pass

    def _handle(self, conn):
        buf = ""
        try:
            conn.settimeout(10.0)
            while self.running:
                chunk = conn.recv(512).decode(errors="ignore")
                if not chunk: break
                buf += chunk
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    line = line.strip()
                    if line:
                        conn.sendall((self._process(line) + "\n").encode())
        except: pass
        finally: conn.close()

    def _process(self, raw):
        try: data = json.loads(raw)
        except: return json.dumps({"error": "invalid json"})

        if "angles" in data:
            a = data["angles"]
            if isinstance(a, list) and len(a) == 4:
                for i in range(4):
                    lo, hi = SERVO_LIMITS[i]
                    self.app.target_angles[i] = max(lo, min(hi, float(a[i])))
                self.app.update_sliders()
                return json.dumps({"ok": True})
            return json.dumps({"error": "need list of 4 floats"})

        if data.get("home"):
            self.app.go_home()
            return json.dumps({"ok": True})
        if data.get("stop"):
            self.app.emergency_stop()
            return json.dumps({"ok": True})
        if data.get("status"):
            return json.dumps({
                "current": self.app.current_angles,
                "target":  self.app.target_angles,
                "ik_reach":  self.app.ik_reach,
                "ik_height": self.app.ik_height,
                "connected": self.app.connection.connected,
            })
        return json.dumps({"error": "unknown command"})


# --- MAIN APP ---

class ARC3App:
    def __init__(self):
        self.connection     = ArmConnection()
        self.ik             = InverseKinematics()
        self.current_angles = list(HOME_POSITION)   # actual position (animated toward target)
        self.target_angles  = list(HOME_POSITION)   # desired position set by user input
        self.ik_reach       = 150.0  # mm
        self.ik_height      = 80.0   # mm
        self.ik_yaw         = 90.0   # degrees
        self.ik_mode        = True
        self.speed          = 1.0
        self.space_held     = False
        self.ctrl_held      = False
        self.last_drag_x    = None
        self.last_drag_y    = None
        self.saved_positions   = {}
        self.is_recording      = False
        self.recorded_frames   = []
        self.is_playing        = False
        self.last_record_frame_ts = 0.0
        self.updating_sliders  = False
        self.dragging_slider   = None
        self.last_error_text   = ""
        self.logging_enabled   = False
        self.log_buffer        = []
        self.connecting        = False
        self.app_running       = True

        self.load_positions_from_file()

        threading.Thread(target=self.smooth_motion_loop, daemon=True).start()   # 50Hz motion thread

        self.ai_socket = AISocket(self, port=9999)
        self.ai_socket.start()   # AI control server on localhost:9999

        self.window = tk.Tk()
        self.build_window()
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        self.poll_arduino()   # start periodic 5s sync

    def build_window(self):
        w = self.window
        w.title("ARC-3")
        w.configure(bg=BG)
        w.resizable(True, True)
        w.minsize(1100, 720)
        w.bind("<KeyPress>",   self.key_pressed)
        w.bind("<KeyRelease>", self.key_released)

        # top bar
        hdr = tk.Frame(w, bg=PANEL, height=48)
        hdr.pack(fill="x", side="top")
        hdr.pack_propagate(False)

        tk.Frame(hdr, bg=ORANGE, width=4).pack(side="left", fill="y")   # orange left edge stripe
        tk.Label(hdr, text="ARC-3", font=FONT_HEAD, bg=PANEL, fg=ORANGE).pack(side="left", padx=14)
        tk.Label(hdr, text="ROBOTIC ARM CONTROLLER", font=("Courier New", 9), bg=PANEL, fg=GREY).pack(side="left", padx=2)

        # status indicators in top right
        self.status_dot  = tk.Label(hdr, text="●", font=FONT_MED, bg=PANEL, fg=RED)
        self.status_dot.pack(side="right", padx=8)
        self.status_text = tk.Label(hdr, text="OFFLINE", font=FONT_SM, bg=PANEL, fg=GREY)
        self.status_text.pack(side="right", padx=2)
        tk.Label(hdr, text="STATUS", font=FONT_XS, bg=PANEL, fg=DGREY).pack(side="right", padx=(12, 0))

        # thin orange line below header
        tk.Frame(w, bg=ORANGE, height=1).pack(fill="x")

        # main 3-col layout
        content = tk.Frame(w, bg=BG)
        content.pack(fill="both", expand=True, padx=5, pady=5)
        content.columnconfigure(0, weight=3)
        content.columnconfigure(1, weight=4)
        content.columnconfigure(2, weight=3)
        content.rowconfigure(0, weight=3)
        content.rowconfigure(1, weight=2)

        self.make_arm_visualizer(content, 0, 0)
        self.make_touchpad(content, 0, 1)
        self.make_joint_controls(content, 0, 2)
        self.make_positions_panel(content, 1, 0)
        self.make_recording_panel(content, 1, 1)
        self.make_connection_panel(content, 1, 2)

        # bottom status bar
        bar = tk.Frame(w, bg=PANEL, height=24)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        tk.Frame(bar, bg=ORANGE, width=3).pack(side="left", fill="y")   # orange left stripe
        self.bottom_status = tk.Label(bar, text="READY", font=FONT_XS, bg=PANEL, fg=GREEN, anchor="w")
        self.bottom_status.pack(side="left", padx=10)
        self.angle_display = tk.Label(bar, text="", font=FONT_XS, bg=PANEL, fg=GREY, anchor="e")
        self.angle_display.pack(side="right", padx=10)

    # --- PANEL BUILDER ---
    def make_panel(self, parent, title, row, col, **opts):
        outer = tk.Frame(parent, bg=BORDER)   # 1px border via outer frame color
        outer.grid(row=row, column=col, **opts)
        # panel header bar
        hdr = tk.Frame(outer, bg=PANEL, height=20)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Frame(hdr, bg=ORANGE, width=3).pack(side="left", fill="y")   # orange left accent
        tk.Label(hdr, text=title, font=FONT_XS, bg=PANEL, fg=ORANGE).pack(side="left", padx=6)
        body = tk.Frame(outer, bg=PANEL, pady=0)
        body.pack(fill="both", expand=True)
        return body

    def make_btn(self, parent, text, cmd, bg, fg, **grid):
        b = tk.Button(parent, text=text, command=cmd, font=FONT_XS,
                      bg=bg, fg=fg, activebackground=ORANGE_D, activeforeground=WHITE,
                      relief="flat", bd=0, cursor="hand2", padx=8, pady=5)
        if "pack" in grid:
            b.pack(grid.pop("pack"), **{k: v for k, v in grid.items()
                                         if k in ("side","padx","pady","fill","expand")})
        else:
            b.grid(**grid)
        return b

    # --- ARM VISUALIZER ---

    def make_arm_visualizer(self, parent, row, col):
        frame = self.make_panel(parent, "VISUALIZATION", row, col, sticky="nsew", padx=(0, 3))
        frame.rowconfigure(0, weight=1)
        frame.rowconfigure(2, weight=1)
        frame.columnconfigure(0, weight=1)

        tk.Label(frame, text="SIDE", font=FONT_XS, bg=PANEL, fg=GREY).grid(row=0, column=0, sticky="nw", padx=6, pady=(3,0))
        self.side_canvas = tk.Canvas(frame, bg=PANEL, highlightthickness=0)
        self.side_canvas.grid(row=0, column=0, sticky="nsew", padx=5, pady=(14,2))

        tk.Frame(frame, bg=BORDER, height=1).grid(row=1, column=0, sticky="ew", padx=5)

        tk.Label(frame, text="TOP", font=FONT_XS, bg=PANEL, fg=GREY).grid(row=2, column=0, sticky="nw", padx=6, pady=(3,0))
        self.top_canvas = tk.Canvas(frame, bg=PANEL, highlightthickness=0)
        self.top_canvas.grid(row=2, column=0, sticky="nsew", padx=5, pady=(14,2))

        self.coord_label = tk.Label(frame, text="", font=FONT_XS, bg=PANEL, fg=ORANGE)
        self.coord_label.grid(row=3, column=0, sticky="w", padx=6, pady=(0,4))

        self.side_canvas.bind("<Configure>", lambda e: self.redraw_arm())
        self.top_canvas.bind("<Configure>",  lambda e: self.redraw_arm())

    def redraw_arm(self):
        self.draw_side_view()
        self.draw_top_view()

    def draw_side_view(self):
        c = self.side_canvas
        W, H = c.winfo_width(), c.winfo_height()
        if W < 10 or H < 10: return
        c.delete("all")
        angles = self.target_angles

        for x in range(0, W, 20): c.create_line(x, 0, x, H, fill=GRID)   # vertical grid
        for y in range(0, H, 20): c.create_line(0, y, W, y, fill=GRID)   # horizontal grid

        scale = (H * 0.38) / (UPPER_ARM_LENGTH + LOWER_ARM_LENGTH)   # mm to pixel scale
        ox, oy = W // 2, int(H * 0.82)   # base pivot point on canvas

        c.create_line(0, oy, W, oy, fill=DGREY)   # ground line
        col_h = int(20 * scale)
        c.create_rectangle(ox-4, oy, ox+4, oy-col_h, fill=DGREY, outline=BORDER)   # base column

        q1 = math.radians(90 - angles[1])
        bend = 180.0 - angles[2]
        q2 = math.radians(bend if self.ik.elbow_up else -bend)
        ex = UPPER_ARM_LENGTH * math.cos(q1)
        ey = UPPER_ARM_LENGTH * math.sin(q1)
        wx = ex + LOWER_ARM_LENGTH * math.cos(q1 + q2)
        wy = ey + LOWER_ARM_LENGTH * math.sin(q1 + q2)

        base  = (ox,                     oy - col_h)
        elbow = (int(base[0] + ex * scale),   int(base[1] - ey * scale))
        wrist = (int(base[0] + wx * scale),   int(base[1] - wy * scale))

        r_max = int((UPPER_ARM_LENGTH + LOWER_ARM_LENGTH) * scale)
        r_min = int(abs(UPPER_ARM_LENGTH - LOWER_ARM_LENGTH) * scale)
        bx, by = base
        c.create_oval(bx-r_max, by-r_max, bx+r_max, by+r_max, outline=DGREY, dash=(3,7))   # max reach circle
        c.create_oval(bx-r_min, by-r_min, bx+r_min, by+r_min, outline=DGREY, dash=(3,7))   # min reach circle

        # shadow pass (offset by 2px)
        c.create_line(base[0]+2,  base[1]+2,  elbow[0]+2, elbow[1]+2, fill=SHADOW, width=8, capstyle="round")
        c.create_line(elbow[0]+2, elbow[1]+2, wrist[0]+2, wrist[1]+2, fill=SHADOW, width=6, capstyle="round")
        # actual arm segments
        c.create_line(base[0],  base[1],  elbow[0], elbow[1], fill=ORANGE,   width=5, capstyle="round")
        c.create_line(elbow[0], elbow[1], wrist[0], wrist[1], fill=ORANGE_L, width=4, capstyle="round")

        # claw fingers (open/close based on angle)
        claw_t = angles[3] / 90.0                               # 0=open, 1=closed
        arm_ang = math.atan2(wy - ey, wx - ex)
        perp    = arm_ang + math.pi / 2
        csize   = int(12 * scale * (1.0 - claw_t * 0.5))
        for side in (-1, 1):
            fx = int(wrist[0] + side * math.cos(perp) * csize * (1 - claw_t * 0.6))
            fy = int(wrist[1] + side * math.sin(perp) * csize * (1 - claw_t * 0.6))
            c.create_line(wrist[0], wrist[1], fx, fy, fill=WHITE, width=2, capstyle="round")

        for pt, col, r in [(base, WHITE, 5), (elbow, ORANGE_L, 4), (wrist, GREEN, 3)]:
            px, py = pt
            c.create_oval(px-r, py-r, px+r, py+r, fill=col, outline="")   # joint dots

        c.create_text(elbow[0]+8, elbow[1]-8, text=f"{angles[1]:.0f}°", font=FONT_XS, fill=GREY, anchor="w")
        c.create_text(wrist[0]+8, wrist[1]-8, text=f"{angles[2]:.0f}°", font=FONT_XS, fill=GREY, anchor="w")

        self.coord_label.config(text=f"TARGET R {wx:5.0f}mm  H {wy:5.0f}mm  Y {angles[0]:5.1f}°")

    def draw_top_view(self):
        c = self.top_canvas
        W, H = c.winfo_width(), c.winfo_height()
        if W < 10 or H < 10: return
        c.delete("all")

        for x in range(0, W, 20): c.create_line(x, 0, x, H, fill=GRID)
        for y in range(0, H, 20): c.create_line(0, y, W, y, fill=GRID)

        cx, cy = W // 2, H // 2
        scale = (min(W, H) * 0.38) / (UPPER_ARM_LENGTH + LOWER_ARM_LENGTH)
        r_max = int((UPPER_ARM_LENGTH + LOWER_ARM_LENGTH) * scale)
        c.create_oval(cx-r_max, cy-r_max, cx+r_max, cy+r_max, outline=DGREY, dash=(3,7))

        angles = self.target_angles
        reach, _ = self.ik.get_endpoint(angles[1], angles[2])
        yaw_rad  = math.radians(angles[0])
        tip_x    = int(cx + reach * scale * math.cos(yaw_rad - math.pi/2))
        tip_y    = int(cy + reach * scale * math.sin(yaw_rad - math.pi/2))

        c.create_line(cx+2, cy+2, tip_x+2, tip_y+2, fill=SHADOW, width=6)   # shadow
        c.create_line(cx,   cy,   tip_x,   tip_y,   fill=ORANGE,    width=3)   # arm projection
        c.create_oval(cx-5,    cy-5,    cx+5,    cy+5,    fill=WHITE,    outline="")
        c.create_oval(tip_x-4, tip_y-4, tip_x+4, tip_y+4, fill=GREEN, outline="")
        c.create_text(cx, cy+r_max+11, text=f"TARGET YAW {angles[0]:.1f}°", font=FONT_XS, fill=GREY)

    # --- TOUCHPAD ---

    def make_touchpad(self, parent, row, col):
        frame = self.make_panel(parent, "TOUCHPAD", row, col, sticky="nsew", padx=3)
        frame.rowconfigure(1, weight=1)
        frame.columnconfigure(0, weight=1)

        mode_row = tk.Frame(frame, bg=PANEL)
        mode_row.grid(row=0, column=0, sticky="ew", padx=6, pady=(4,2))
        tk.Label(mode_row, text="MODE:", font=FONT_XS, bg=PANEL, fg=GREY).pack(side="left")

        self.ik_mode_var = tk.BooleanVar(value=True)
        for label, val in [("SMART IK", True), ("DIRECT", False)]:
            tk.Radiobutton(mode_row, text=label, variable=self.ik_mode_var, value=val,
                           font=FONT_XS, bg=PANEL, fg=WHITE, selectcolor=ORANGE_D,
                           activebackground=PANEL, command=self.mode_changed
                           ).pack(side="left", padx=5)

        self.touchpad = tk.Canvas(frame, bg=BG, highlightthickness=1,
                                  highlightbackground=BORDER, cursor="crosshair")
        self.touchpad.grid(row=1, column=0, sticky="nsew", padx=6, pady=3)

        self.touchpad.bind("<ButtonPress-1>",   self.touchpad_press)
        self.touchpad.bind("<B1-Motion>",       self.touchpad_drag)
        self.touchpad.bind("<ButtonRelease-1>", self.touchpad_release)
        self.touchpad.bind("<MouseWheel>",      self.touchpad_scroll)
        self.touchpad.bind("<Button-4>",        self.touchpad_scroll)   # linux scroll up
        self.touchpad.bind("<Button-5>",        self.touchpad_scroll)   # linux scroll down
        self.touchpad.bind("<Configure>",       self.redraw_touchpad)

        hints = tk.Frame(frame, bg=PANEL)
        hints.grid(row=2, column=0, sticky="ew", padx=6, pady=1)
        for txt, col in [
            ("drag X = reach  |  drag Y = height (IK) or shoulder (direct)", GREY),
            ("scroll = reach fine adjust (IK) or elbow (direct)", GREY),
            ("SPACE = open claw   CTRL = close claw   H = home   ESC = stop", ORANGE),
        ]:
            tk.Label(hints, text=txt, font=FONT_XS, bg=PANEL, fg=col).pack(anchor="w")

        self.ik_readout = tk.Label(frame, text="", font=FONT_XS, bg=PANEL, fg=ORANGE_L, anchor="w")
        self.ik_readout.grid(row=3, column=0, sticky="w", padx=6, pady=(1,5))

    def mode_changed(self):
        self.ik_mode = self.ik_mode_var.get()
        self.redraw_touchpad()

    def redraw_touchpad(self, event=None):
        c = self.touchpad
        W, H = c.winfo_width(), c.winfo_height()
        if W < 10 or H < 10: return
        c.delete("all")

        for x in range(0, W, 30): c.create_line(x, 0, x, H, fill=GRID)
        for y in range(0, H, 30): c.create_line(0, y, W, y, fill=GRID)
        c.create_line(W//2, 0, W//2, H, fill=BORDER, dash=(2, 10))   # center vertical
        c.create_line(0, H//2, W, H//2, fill=BORDER, dash=(2, 10))   # center horizontal

        lbl = "SMART MODE — IK" if self.ik_mode else "DIRECT MODE"
        c.create_text(W//2, H-12, text=lbl, font=FONT_XS, fill=DGREY)
        c.create_text(8,    H//2, text="↑", font=FONT_XS, fill=DGREY, anchor="w")
        c.create_text(W//2, 10,  text="← YAW →", font=FONT_XS, fill=DGREY)
        self.draw_touchpad_cursor()

    def draw_touchpad_cursor(self):
        c = self.touchpad
        W, H = c.winfo_width(), c.winfo_height()
        if W < 10: return

        if self.ik_mode:
            yaw_frac = min(1.0, max(0.0, self.ik_reach / (UPPER_ARM_LENGTH + LOWER_ARM_LENGTH)))
            h_frac = 1.0 - min(1.0, max(0.0, self.ik_height / ((UPPER_ARM_LENGTH + LOWER_ARM_LENGTH) * 0.8)))
        else:
            yaw_frac = (self.target_angles[0] - SERVO_LIMITS[0][0]) / (SERVO_LIMITS[0][1] - SERVO_LIMITS[0][0])
            h_frac = 1.0 - (self.target_angles[1] - SERVO_LIMITS[1][0]) / (SERVO_LIMITS[1][1] - SERVO_LIMITS[1][0])

        cx = int(yaw_frac * W)
        cy = int(h_frac   * H)
        c.delete("cursor")

        c.create_line(cx-16, cy, cx+16, cy, fill=ORANGE,   width=2, tags="cursor")   # horizontal crosshair
        c.create_line(cx, cy-16, cx, cy+16, fill=ORANGE,   width=2, tags="cursor")   # vertical crosshair
        c.create_oval(cx-5, cy-5, cx+5, cy+5, fill=ORANGE, outline=ORANGE_L, width=2, tags="cursor")   # center dot

        reach, height = self.ik.get_endpoint(self.target_angles[1], self.target_angles[2])
        self.ik_readout.config(text=f"R:{reach:.0f}mm  H:{height:.0f}mm  Y:{self.target_angles[0]:.1f} deg")

    def touchpad_press(self, event):
        self.last_drag_x = event.x
        self.last_drag_y = event.y

    def touchpad_drag(self, event):
        if self.last_drag_x is None: return
        dx = event.x - self.last_drag_x
        dy = event.y - self.last_drag_y
        self.last_drag_x, self.last_drag_y = event.x, event.y

        W, H = self.touchpad.winfo_width(), self.touchpad.winfo_height()
        if W < 1 or H < 1: return

        if self.ik_mode:
            max_reach = UPPER_ARM_LENGTH + LOWER_ARM_LENGTH - 1
            self.ik_reach = max(0, min(max_reach, self.ik_reach + dx * (max_reach / max(W, 1))))
            self.ik_height = max(0, self.ik_height - dy * (max_reach / max(H, 1)))   # drag up = increase height
            res = self.ik.solve(self.ik_reach, self.ik_height, self.ik_yaw)
            if res["can_reach"]:
                self.target_angles[1] = res["shoulder"]
                self.target_angles[2] = res["elbow"]
            else:
                self.show_status("out of reach", YELLOW)
        else:
            new_yaw = self.target_angles[0] + dx * (180.0 / W)   # direct mode uses X for yaw
            new_yaw = max(SERVO_LIMITS[0][0], min(SERVO_LIMITS[0][1], new_yaw))
            self.target_angles[0] = new_yaw
            sh = self.target_angles[1] - dy * (120.0 / H)   # drag up = raise shoulder
            self.target_angles[1] = max(SERVO_LIMITS[1][0], min(SERVO_LIMITS[1][1], sh))

        self.update_sliders()
        self.draw_touchpad_cursor()
        self.redraw_arm()
        if self.is_recording:
            self.recorded_frames.append((list(self.target_angles), time.time()))

    def touchpad_release(self, event):
        self.last_drag_x = self.last_drag_y = None

    def touchpad_scroll(self, event):
        d = 1 if (getattr(event, "delta", 0) > 0 or getattr(event, "num", 0) == 4) else -1

        if self.ik_mode:
            self.ik_reach = max(20, min(UPPER_ARM_LENGTH + LOWER_ARM_LENGTH - 5, self.ik_reach + d * 8))
            res = self.ik.solve(self.ik_reach, self.ik_height, self.ik_yaw)
            if res["can_reach"]:
                self.target_angles[1] = res["shoulder"]
                self.target_angles[2] = res["elbow"]
        else:
            el = self.target_angles[2] + d * 4
            self.target_angles[2] = max(SERVO_LIMITS[2][0], min(SERVO_LIMITS[2][1], el))

        self.update_sliders()
        self.draw_touchpad_cursor()
        self.redraw_arm()

    # --- JOINT SLIDERS ---

    def make_joint_controls(self, parent, row, col):
        frame = self.make_panel(parent, "JOINTS", row, col, sticky="nsew", padx=(3, 0))
        frame.columnconfigure(0, weight=1)

        self.sliders    = []
        self.val_labels = []

        for i, name in enumerate(["YAW", "SHOULDER", "ELBOW", "CLAW"]):
            row_f = tk.Frame(frame, bg=PANEL)
            row_f.grid(row=i*2, column=0, sticky="ew", padx=8, pady=(6,0))
            row_f.columnconfigure(1, weight=1)

            tk.Label(row_f, text=name, font=FONT_XS, bg=PANEL, fg=GREY).grid(row=0, column=0, sticky="w")

            vl = tk.Label(row_f, text=f"{HOME_POSITION[i]:.1f}°",
                          font=FONT_NORM, bg=PANEL, fg=ORANGE, width=7, anchor="e")
            vl.grid(row=0, column=2, sticky="e")
            self.val_labels.append(vl)

            sl = tk.Scale(frame, from_=SERVO_LIMITS[i][0], to=SERVO_LIMITS[i][1],
                          orient="horizontal", bg=PANEL, fg=WHITE, troughcolor=DGREY,
                          activebackground=ORANGE, highlightthickness=0,
                          sliderlength=12, showvalue=False,
                          command=lambda v, idx=i: self.slider_moved(idx, float(v)))
            sl.bind("<ButtonPress-1>",   lambda e, idx=i: setattr(self, "dragging_slider", idx))
            sl.bind("<ButtonRelease-1>", lambda e: setattr(self, "dragging_slider", None))
            sl.set(HOME_POSITION[i])
            sl.grid(row=i*2+1, column=0, sticky="ew", padx=8, pady=(1,0))
            self.sliders.append(sl)

        tk.Label(frame, bg=PANEL, height=1).grid(row=8, column=0)

        tk.Label(frame, text="SPEED", font=FONT_XS, bg=PANEL, fg=GREY).grid(row=9, column=0, sticky="w", padx=8)
        spd = tk.Scale(frame, from_=0.15, to=4.0, resolution=0.1,
                       orient="horizontal", bg=PANEL, fg=WHITE, troughcolor=DGREY,
                       activebackground=ORANGE, highlightthickness=0,
                       sliderlength=12, showvalue=False,
                       command=lambda v: setattr(self, "speed", float(v)))
        spd.set(1.0)
        spd.grid(row=10, column=0, sticky="ew", padx=8, pady=2)

        tk.Label(frame, bg=PANEL, height=1).grid(row=11, column=0)

        btns = tk.Frame(frame, bg=PANEL)
        btns.grid(row=12, column=0, padx=8, pady=4, sticky="ew")
        btns.columnconfigure(0, weight=1)
        btns.columnconfigure(1, weight=1)
        self.make_btn(btns, "HOME", self.go_home,       DGREY,    WHITE, row=0, column=0, sticky="ew", padx=(0,2))
        self.make_btn(btns, "STOP", self.emergency_stop, ORANGE_D, RED,  row=0, column=1, sticky="ew", padx=(2,0))

        el_row = tk.Frame(frame, bg=PANEL)
        el_row.grid(row=13, column=0, padx=8, pady=(4,6), sticky="w")
        tk.Label(el_row, text="ELBOW:", font=FONT_XS, bg=PANEL, fg=GREY).pack(side="left")
        self.elbow_var = tk.BooleanVar(value=True)
        for label, val in [("UP", True), ("DOWN", False)]:
            tk.Radiobutton(el_row, text=label, variable=self.elbow_var, value=val,
                           font=FONT_XS, bg=PANEL, fg=WHITE, selectcolor=ORANGE_D,
                           activebackground=PANEL, command=self.elbow_changed
                           ).pack(side="left", padx=3)

    def slider_moved(self, idx, val):
        if self.updating_sliders:
            return
        self.target_angles[idx] = val
        self.val_labels[idx].config(text=f"{val:.1f}°")
        if self.is_recording:
            self.recorded_frames.append((list(self.target_angles), time.time()))

    def update_sliders(self):
        self.updating_sliders = True
        try:
            for i, s in enumerate(self.sliders):
                s.set(self.target_angles[i])
                self.val_labels[i].config(text=f"{self.target_angles[i]:.1f} deg")
        finally:
            self.updating_sliders = False

    def update_servo_display(self, idx, value):
        self.updating_sliders = True
        try:
            self.sliders[idx].set(value)
            self.val_labels[idx].config(text=f"{value:.1f} deg")
        finally:
            self.updating_sliders = False

    def elbow_changed(self):
        self.ik.elbow_up = self.elbow_var.get()
        if self.ik_mode:
            res = self.ik.solve(self.ik_reach, self.ik_height, self.ik_yaw)
            if res["can_reach"]:
                self.target_angles[1] = res["shoulder"]
                self.target_angles[2] = res["elbow"]
            self.update_sliders()

    # --- SAVED POSITIONS ---

    def make_positions_panel(self, parent, row, col):
        frame = self.make_panel(parent, "SAVED POSITIONS", row, col, sticky="nsew", padx=(0,3))
        frame.rowconfigure(1, weight=1)
        frame.columnconfigure(0, weight=1)

        btn_row = tk.Frame(frame, bg=PANEL)
        btn_row.grid(row=0, column=0, sticky="ew", padx=6, pady=4)
        self.make_btn(btn_row, "SAVE", self.save_position, ORANGE_D, ORANGE, padx=5, pack={"side": "left"})
        self.make_btn(btn_row, "DEL", self.delete_position, DGREY, RED, padx=5, pack={"side": "left"})


        lf = tk.Frame(frame, bg=PANEL)
        lf.grid(row=1, column=0, sticky="nsew", padx=6)
        lf.rowconfigure(0, weight=1)
        lf.columnconfigure(0, weight=1)

        self.positions_list = tk.Listbox(lf, bg=BG, fg=WHITE, font=FONT_SM,
                                          selectbackground=ORANGE_D, selectforeground=GREEN,
                                          highlightthickness=0, borderwidth=0, activestyle="none")
        self.positions_list.grid(row=0, column=0, sticky="nsew")
        sb = tk.Scrollbar(lf, orient="vertical", command=self.positions_list.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.positions_list.configure(yscrollcommand=sb.set)
        self.positions_list.bind("<Double-Button-1>", self.go_to_position)

        self.make_btn(frame, "GO TO SELECTED", self.go_to_position,
                      DGREY, ORANGE, row=2, column=0, sticky="ew", padx=6, pady=(2,6))
        self.refresh_positions_list()

    def save_position(self):
        name = simpledialog.askstring("Save", "Position name:", parent=self.window)
        if not name or not name.strip(): return
        name = name.strip()
        self.saved_positions[name] = {
            "angles": list(self.current_angles),
            "timestamp": datetime.now().isoformat(),
            "ik_reach": self.ik_reach,
            "ik_height": self.ik_height,
        }
        self.save_positions_to_file()
        self.refresh_positions_list()
        self.show_status(f"Saved: {name}", GREEN)

    def delete_position(self):
        sel = self.positions_list.curselection()
        if not sel: return
        name = self.positions_list.get(sel[0]).split("  ")[0]
        if name in self.saved_positions:
            del self.saved_positions[name]
            self.save_positions_to_file()
            self.refresh_positions_list()

    def go_to_position(self, event=None):
        sel = self.positions_list.curselection()
        if not sel: return
        name = self.positions_list.get(sel[0]).split("  ")[0]
        if name not in self.saved_positions: return
        d = self.saved_positions[name]
        for i in range(4): self.target_angles[i] = d["angles"][i]
        if "ik_reach" in d:
            self.ik_reach  = d["ik_reach"]
            self.ik_height = d["ik_height"]
        self.update_sliders()
        self.show_status(f"→ {name}", ORANGE)

    def refresh_positions_list(self):
        self.positions_list.delete(0, "end")
        for name, d in self.saved_positions.items():
            a = d["angles"]
            self.positions_list.insert("end", f"{name}  [{a[0]:.0f} {a[1]:.0f} {a[2]:.0f} {a[3]:.0f}]")

    def load_positions_from_file(self):
        if os.path.exists(POSITIONS_FILE):
            try:
                with open(POSITIONS_FILE) as f:
                    self.saved_positions = json.load(f)
            except: pass

    def save_positions_to_file(self):
        try:
            with open(POSITIONS_FILE, "w") as f:
                json.dump(self.saved_positions, f, indent=2)
        except: pass

    # --- RECORDING ---

    def make_recording_panel(self, parent, row, col):
        frame = self.make_panel(parent, "MOTION RECORD", row, col, sticky="nsew", padx=3)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

        self.rec_status_label = tk.Label(frame, text="IDLE", font=FONT_MED, bg=PANEL, fg=GREY)
        self.rec_status_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=8, pady=(5,2))

        self.make_btn(frame, "● REC",  self.toggle_recording, ORANGE_D, RED,   row=1, column=0, sticky="ew", padx=(8,2), pady=3)
        self.make_btn(frame, "▶ PLAY", self.play_recording,   DGREY,     GREEN, row=1, column=1, sticky="ew", padx=(2,8), pady=3)

        self.make_btn(frame, "SAVE FILE", self.save_recording_file, DGREY, GREEN, row=2, column=0, sticky="ew", padx=(8,2), pady=3)
        self.make_btn(frame, "LOAD FILE", self.load_recording_file, DGREY, GREEN, row=2, column=1, sticky="ew", padx=(2,8), pady=3)

        self.frame_count_label = tk.Label(frame, text="0 frames", font=FONT_XS, bg=PANEL, fg=GREY)
        self.frame_count_label.grid(row=3, column=0, columnspan=2, sticky="w", padx=8, pady=2)

        self.loop_var = tk.BooleanVar(value=False)
        tk.Checkbutton(frame, text="Loop", variable=self.loop_var,
                       font=FONT_XS, bg=PANEL, fg=WHITE, selectcolor=ORANGE_D,
                       activebackground=PANEL).grid(row=4, column=0, sticky="w", padx=8, pady=2)

        self.log_var = tk.BooleanVar(value=False)
        tk.Checkbutton(frame, text="Log CSV", variable=self.log_var,
                       font=FONT_XS, bg=PANEL, fg=WHITE, selectcolor=DGREY,
                       activebackground=PANEL,
                       command=lambda: setattr(self, "logging_enabled", self.log_var.get())
                       ).grid(row=5, column=0, sticky="w", padx=8, pady=2)

        # AI integration hook note
        tk.Label(frame, text="AI port 9999 active\n{\"angles\":[y,s,e,c]}\n{\"home\":true}  {\"stop\":true}",
                 font=FONT_XS, bg=PANEL, fg=ORANGE_D, justify="left"
                 ).grid(row=6, column=0, columnspan=2, sticky="sw", padx=8, pady=(8,6))

    def toggle_recording(self):
        if not self.is_recording:
            self.is_recording    = True
            self.recorded_frames = []
            self.last_record_frame_ts = time.time()
            self.recorded_frames.append((list(self.current_angles), self.last_record_frame_ts))
            self.rec_status_label.config(text="● REC", fg=RED)
            self.show_status("Recording...", RED)
        else:
            self.is_recording = False
            self.recorded_frames.append((list(self.current_angles), time.time()))
            n = len(self.recorded_frames)
            self.rec_status_label.config(text=f"DONE ({n}f)", fg=GREEN)
            self.frame_count_label.config(text=f"{n} frames")
            self.show_status(f"Recorded {n} frames", GREEN)
            self.save_recording_file()

    def play_recording(self):
        if not self.recorded_frames:
            self.show_status("Nothing recorded", YELLOW)
            return
        if self.is_playing: return

        def playback():
            self.is_playing = True
            self.rec_status_label.config(text="▶ PLAY", fg=GREEN)
            frames = self.recorded_frames
            while self.is_playing:
                t0  = time.time()
                t_0 = frames[0][1]
                for angles, ts in frames:
                    if not self.is_playing: break
                    for i in range(4): self.target_angles[i] = angles[i]
                    self.window.after_idle(self.update_sliders)
                    elapsed = ts - t_0                          # how far into the recording this frame is
                    wait    = elapsed - (time.time() - t0)     # how long to sleep to match original timing
                    if wait > 0: time.sleep(wait)
                if not self.loop_var.get(): break
            self.is_playing = False
            self.rec_status_label.config(text="IDLE", fg=GREY)

        threading.Thread(target=playback, daemon=True).start()

    def save_recording_file(self):
        if not self.recorded_frames:
            self.show_status("Nothing recorded", YELLOW)
            return

        path = filedialog.asksaveasfilename(
            parent=self.window,
            title="Save ARC-3 recording",
            defaultextension=".arc3",
            filetypes=RECORDING_FILETYPES,
        )
        if not path:
            return

        try:
            if path.lower().endswith(".csv"):
                self._save_recording_csv(path)
            else:
                self._save_recording_arc3(path)
            self.show_status(f"Saved recording: {os.path.basename(path)}", GREEN)
        except Exception as e:
            self.show_status(f"Save failed: {e}", YELLOW)

    def load_recording_file(self):
        path = filedialog.askopenfilename(
            parent=self.window,
            title="Load ARC-3 recording",
            filetypes=RECORDING_FILETYPES,
        )
        if not path:
            return

        try:
            if path.lower().endswith(".csv"):
                frames = self._load_recording_csv(path)
            else:
                frames = self._load_recording_arc3(path)
        except Exception as e:
            self.show_status(f"Load failed: {e}", YELLOW)
            return

        if not frames:
            self.show_status("No frames in file", YELLOW)
            return

        self.is_recording = False
        self.is_playing = False
        self.recorded_frames = frames
        self.frame_count_label.config(text=f"{len(frames)} frames")
        self.rec_status_label.config(text=f"LOADED ({len(frames)}f)", fg=GREEN)
        self.show_status(f"Loaded recording: {os.path.basename(path)}", GREEN)
        self.play_recording()

    def _save_recording_arc3(self, path):
        first_ts = self.recorded_frames[0][1]
        data = {
            "format": "ARC-3 motion",
            "version": 1,
            "created": datetime.now().isoformat(),
            "servo_limits": SERVO_LIMITS,
            "frames": [
                {"t": ts - first_ts, "angles": [float(a) for a in angles]}
                for angles, ts in self.recorded_frames
            ],
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def _load_recording_arc3(self, path):
        with open(path) as f:
            data = json.load(f)
        base = time.time()
        frames = []
        for frame in data.get("frames", []):
            angles = self._clean_recording_angles(frame.get("angles", []))
            frames.append((angles, base + float(frame.get("t", 0.0))))
        return frames

    def _save_recording_csv(self, path):
        first_ts = self.recorded_frames[0][1]
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["time_seconds", "yaw", "shoulder", "elbow", "claw"])
            for angles, ts in self.recorded_frames:
                w.writerow([f"{ts - first_ts:.4f}", *[f"{float(a):.2f}" for a in angles]])

    def _load_recording_csv(self, path):
        base = time.time()
        frames = []
        with open(path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                angles = self._clean_recording_angles([
                    row.get("yaw", 0), row.get("shoulder", 0),
                    row.get("elbow", 0), row.get("claw", 0),
                ])
                frames.append((angles, base + float(row.get("time_seconds", 0.0))))
        return frames

    def _clean_recording_angles(self, angles):
        if len(angles) != 4:
            raise ValueError("recording frame needs 4 angles")
        cleaned = []
        for i, value in enumerate(angles):
            lo, hi = SERVO_LIMITS[i]
            cleaned.append(max(lo, min(hi, float(value))))
        return cleaned

    # --- CONNECTION PANEL ---

    def make_connection_panel(self, parent, row, col):
        frame = self.make_panel(parent, "CONNECTION", row, col, sticky="nsew", padx=(3, 0))
        frame.columnconfigure(1, weight=1)

        tk.Label(frame, text="Arduino IP / COM", font=FONT_XS, bg=PANEL, fg=GREY).grid(row=0, column=0, sticky="w", padx=8, pady=(8,2))
        tk.Label(frame, text="AUTO finds USB Arduino, then WiFi fallback", font=FONT_XS, bg=PANEL, fg=DGREY).grid(row=1, column=0, columnspan=2, sticky="w", padx=8)

        self.config = load_app_config()
        self.ip_input = tk.StringVar(value=self.config.get("wifi_ip") or DEFAULT_IP)
        tk.Entry(frame, textvariable=self.ip_input, font=FONT_NORM,
                 bg=BG, fg=WHITE, insertbackground=ORANGE,
                 highlightcolor=ORANGE, highlightthickness=1,
                 relief="flat", width=18
                 ).grid(row=2, column=0, columnspan=2, sticky="ew", padx=8, pady=(2,4))

        tk.Label(frame, text="Port", font=FONT_XS, bg=PANEL, fg=GREY).grid(row=3, column=0, sticky="w", padx=8, pady=(4,2))
        self.port_input = tk.StringVar(value=str(self.config.get("port") or DEFAULT_PORT))
        tk.Entry(frame, textvariable=self.port_input, font=FONT_NORM,
                 bg=BG, fg=WHITE, insertbackground=ORANGE,
                 highlightcolor=ORANGE, highlightthickness=1,
                 relief="flat", width=8
                 ).grid(row=4, column=0, sticky="w", padx=8, pady=(0,6))

        self.connect_button = tk.Button(frame, text="CONNECT", command=self.toggle_connection,
                                        font=FONT_XS, bg=ORANGE_D, fg=ORANGE,
                                        activebackground=ORANGE_D, activeforeground=WHITE,
                                        relief="flat", bd=0, cursor="hand2", padx=8, pady=5)
        self.connect_button.grid(row=5, column=0, columnspan=2, sticky="ew", padx=8, pady=4)

        self.info_label = tk.Label(frame, text="", font=FONT_XS, bg=PANEL, fg=GREY,
                                    wraplength=180, justify="left")
        self.info_label.grid(row=6, column=0, columnspan=2, sticky="w", padx=8, pady=3)

        self.make_btn(frame, "PING", self.ping_arduino, DGREY, WHITE,
                      row=7, column=0, sticky="w", padx=8, pady=2)
        self.make_btn(frame, "COPY ERR", self.copy_error_to_clipboard, DGREY, YELLOW,
                      row=7, column=1, sticky="e", padx=8, pady=2)

        tk.Frame(frame, bg=BORDER, height=1).grid(row=8, column=0, columnspan=2, sticky="ew", padx=8, pady=6)

        tk.Label(frame, text="Servo test (channel 0-3)", font=FONT_XS, bg=PANEL, fg=GREY).grid(row=9, column=0, columnspan=2, sticky="w", padx=8, pady=(6,0))
        self.test_ch_input = tk.StringVar(value="3")
        tk.Entry(frame, textvariable=self.test_ch_input, font=FONT_NORM,
                 bg=BG, fg=WHITE, insertbackground=ORANGE,
                 highlightcolor=ORANGE, highlightthickness=1,
                 relief="flat", width=5
                 ).grid(row=10, column=0, sticky="w", padx=8)
        self.make_btn(frame, "TEST SERVO", self.servo_test, DGREY, YELLOW,
                      row=10, column=1, sticky="e", padx=8)

        tk.Label(frame,
                 text="AUTO = USB first, then WiFi fallback.\nThe last WiFi IP is saved automatically.\nConnect via USB once and the app grabs the\nboard's current WiFi IP for next time.\nOr type a COM port (e.g. COM5) or the IP\nthe board prints to Serial.",
                 font=FONT_XS, bg=PANEL, fg=DGREY, justify="left", wraplength=180
                 ).grid(row=11, column=0, columnspan=2, sticky="w", padx=8)

    def toggle_connection(self):
        if self.connection.connected:
            self.connection.disconnect()
            self.update_connection_display(False)
            self.show_status("Disconnected", GREY)
        else:
            if getattr(self, "connecting", False):
                return
            self.connecting = True
            self.show_status("Connecting...", YELLOW)
            self.connect_button.config(text="CONNECTING", state="disabled")
            ip = self.ip_input.get().strip()
            try:    port = int(self.port_input.get())
            except: port = DEFAULT_PORT
            threading.Thread(target=self._connect_worker, args=(ip, port), daemon=True).start()

    def _connect_worker(self, ip, port):
        ok = False
        used_target = ip
        try:
            ok = self.connection.connect(ip, port)
            if not ok and self.connection._is_serial_target(ip):
                serial_error = self.connection.last_error or "unknown USB error"
                self.last_error_text = f"USB failed: {serial_error}"
                self.window.after(0, lambda e=serial_error: self.info_label.config(text=f"USB failed: {e}"))
                self.window.after(0, lambda: self.show_status("USB failed, trying WiFi...", YELLOW))
                wifi_ip = self.config.get("wifi_ip") or DEFAULT_WIFI_IP
                ok = self.connection.connect(wifi_ip, port)
                used_target = wifi_ip
                if not ok:
                    wifi_error = self.connection.last_error or "unknown WiFi error"
                    self.connection.last_error = f"USB: {serial_error}  |  WiFi {wifi_ip}: {wifi_error}"
                    self.last_error_text = self.connection.last_error
        except Exception as e:
            self.connection.last_error = str(e)
        finally:
            self.window.after(0, lambda ok=ok, used_target=used_target: self._connect_finished(ok, used_target))

    def _connect_finished(self, ok, used_target):
        self.connecting = False
        self.connect_button.config(state="normal")
        self.update_connection_display(ok)
        if ok:
            mode = "USB" if self.connection.mode == "serial" else "WiFi"
            self.show_status(f"Connected {mode} {self.connection.active_target or used_target}", GREEN)
            if self.connection.mode == "wifi":
                self._persist_wifi(self.connection.active_target or used_target)
            self.sync_with_arduino()
        else:
            self.last_error_text = self.connection.last_error
            self.info_label.config(text=self.connection.last_error)
            self.show_status(f"Failed: {self.connection.last_error}", RED)

    def update_connection_display(self, connected):
        if connected:
            self.status_dot.config(fg=GREEN)
            self.status_text.config(text="ONLINE", fg=GREEN)
            self.connect_button.config(text="DISCONNECT", bg=ORANGE_D, fg=RED)
        else:
            self.status_dot.config(fg=RED)
            self.status_text.config(text="OFFLINE", fg=GREY)
            self.connect_button.config(text="CONNECT", bg=ORANGE_D, fg=ORANGE)

    def ping_arduino(self):
        if not self.connection.connected:
            self.show_status("Not connected", YELLOW)
            return
        t0 = time.time()
        ok = self.connection.ping()
        ms = (time.time() - t0) * 1000
        if ok: self.show_status(f"Ping {ms:.1f}ms", GREEN)
        else:
            self.show_status("No response", RED)
            self.update_connection_display(False)

    def servo_test(self):
        if not self.connection.connected:
            self.show_status("Not connected", YELLOW)
            return
        try: ch = int(self.test_ch_input.get())
        except: ch = 3
        if not (0 <= ch <= 3):
            self.show_status("Channel must be 0-3", YELLOW)
            return
        reply = self.connection.send_command(f"TEST:{ch}")
        if reply == f"OK TESTING:{ch}":
            self.show_status(f"Sweeping servo {ch} (press STOP to cancel)", GREEN)
        else:
            self.show_status(f"TEST:{ch} failed: {self.connection.last_error}", RED)

    def copy_error_to_clipboard(self):
        text = self.last_error_text or ""
        if not text:
            try:    text = self.info_label.cget("text") or ""
            except: text = ""
        if not text:
            text = self.connection.last_error or ""
        if not text:
            self.show_status("Nothing to copy yet", YELLOW)
            return
        try:
            self.window.clipboard_clear()
            self.window.clipboard_append(text)
            self.show_status("Error copied to clipboard", GREEN)
        except Exception as e:
            self.show_status(f"Copy failed: {e}", YELLOW)

    def sync_with_arduino(self):
        if not self.connection.connected: return
        reply = self.connection.send_command("STATUS")   # ask arduino for current state
        if not reply:
            self.last_error_text = f"No STATUS reply: {self.connection.last_error}"
            self.info_label.config(text=self.last_error_text)
            return
        if reply.startswith("IP:"):
            self.info_label.config(text=reply)
            ip = reply[3:].strip()
            if self.connection.mode == "serial" and self._valid_ip(ip):
                self._persist_wifi(ip)
                self.ip_input.set(ip)
            return
        if reply.startswith("USB:"):
            self.info_label.config(text=reply)
            return
        if reply.startswith("{"):
            try:
                d = json.loads(reply)
                self.info_label.config(text=f"IP:{d.get('ip','?')}  RSSI:{d.get('rssi','?')}dBm")
                for key, idx in [("yaw",0),("pitch1",1),("pitch2",2),("claw",3)]:
                    if key in d:
                        self.current_angles[idx] = float(d[key])
                        self.target_angles[idx]  = float(d[key])
                self.update_sliders()
            except: pass

    def _valid_ip(self, s):
        parts = s.split(".")
        if len(parts) != 4:
            return False
        try:
            return all(0 <= int(p) <= 255 for p in parts)
        except ValueError:
            return False

    def _persist_wifi(self, ip):
        cfg = load_app_config()
        cfg["wifi_ip"] = ip
        try:
            cfg["port"] = int(self.port_input.get())
        except Exception:
            pass
        save_app_config(cfg)

    # --- KEYBOARD ---

    def key_pressed(self, event):
        k = event.keysym.lower()
        if k == "space" and not self.space_held:
            self.space_held = True
        elif k in ("control_l","control_r") and not self.ctrl_held:
            self.ctrl_held = True
        elif k == "h": self.go_home()
        elif k == "escape": self.emergency_stop()
        elif k == "left":  self.target_angles[0] = max(SERVO_LIMITS[0][0], self.target_angles[0]-2); self.update_sliders()
        elif k == "right": self.target_angles[0] = min(SERVO_LIMITS[0][1], self.target_angles[0]+2); self.update_sliders()
        elif k == "up":    self.target_angles[1] = max(SERVO_LIMITS[1][0], self.target_angles[1]-2); self.update_sliders()
        elif k == "down":  self.target_angles[1] = min(SERVO_LIMITS[1][1], self.target_angles[1]+2); self.update_sliders()

    def key_released(self, event):
        k = event.keysym.lower()
        if k == "space":
            self.space_held = False
            self.target_angles[3] = self.current_angles[3]
            self.update_sliders()
        elif k in ("control_l","control_r"):
            self.ctrl_held = False
            self.target_angles[3] = self.current_angles[3]
            self.update_sliders()

    # --- ARM COMMANDS ---

    def go_home(self):
        for i in range(4): self.target_angles[i] = HOME_POSITION[i]
        self.ik_reach = 150.0; self.ik_height = 80.0; self.ik_yaw = 90.0
        self.update_sliders()
        self.show_status("Home", ORANGE)

    def emergency_stop(self):
        self.is_playing = self.is_recording = False
        for i in range(4): self.target_angles[i] = self.current_angles[i]   # freeze in place
        if self.connection.connected: self.connection.send_command("STOP")
        self.update_sliders()
        self.show_status("STOP", RED)

    # --- SMOOTH MOTION LOOP (runs in background thread at 50Hz) ---

    def smooth_motion_loop(self):
        """ Smoothly interpolates current_angles toward target_angles and sends commands """
        if not hasattr(self, 'last_sent_angles'):
            self.last_sent_angles = [-999.0] * 4

        while self.app_running:
            t0 = time.perf_counter()

            # Handle keyboard hotkeys for claw (Space / Ctrl) if active
            if getattr(self, 'space_held', False) and not getattr(self, 'ctrl_held', False):
                self.target_angles[3] = SERVO_LIMITS[3][0]
            elif getattr(self, 'ctrl_held', False) and not getattr(self, 'space_held', False):
                self.target_angles[3] = SERVO_LIMITS[3][1]

            # Move at a fixed rate toward target angles. This avoids exponential
            # easing that makes servos slow down before they arrive.
            speed = getattr(self, "speed", 1.0)
            for i in range(4):
                diff = self.target_angles[i] - self.current_angles[i]
                step = (CLAW_DEGREES_PER_STEP if i == 3 else DEGREES_PER_STEP) * speed
                if abs(diff) > step:
                    self.current_angles[i] += math.copysign(step, diff)
                else:
                    self.current_angles[i] = self.target_angles[i]

            # Deadband Check: Only transmit if at least one joint moved > DEADBAND_DEGREES
            if self.connection.connected:
                needs_send = False
                for i in range(4):
                    if abs(self.current_angles[i] - self.last_sent_angles[i]) >= DEADBAND_DEGREES:
                        needs_send = True
                        break

                if needs_send:
                    cmd = f"SETALL:{self.current_angles[0]:.1f},{self.current_angles[1]:.1f},{self.current_angles[2]:.1f},{self.current_angles[3]:.1f}"
                    self.connection.send_command_nowait(cmd)
                    self.last_sent_angles = list(self.current_angles)

            elapsed = time.perf_counter() - t0
            time.sleep(max(0.001, (1.0 / UPDATES_PER_SECOND) - elapsed))

    def update_visuals(self):
        try:
            self.redraw_arm()
            self.draw_touchpad_cursor()
            if hasattr(self, "sliders"):
                self.updating_sliders = True
                try:
                    for i, s in enumerate(self.sliders):
                        if i == self.dragging_slider:
                            continue   # don't fight the user while they drag
                        s.set(self.current_angles[i])
                        self.val_labels[i].config(text=f"{self.current_angles[i]:.1f} deg")
                finally:
                    self.updating_sliders = False
            self.angle_display.config(
                text=f"Y {self.current_angles[0]:5.1f}°  S {self.current_angles[1]:5.1f}°  "
                     f"E {self.current_angles[2]:5.1f}°  C {self.current_angles[3]:4.1f}°"
            )
        except: pass
        if self.app_running:
            self.window.after(20, self.update_visuals)

    # Add this line at the bottom of your __init__() method:
    # self.update_visualization_loop()

    def update_visualization_loop(self):
        """ Redraws canvas at ~30 FPS and syncs sliders during file playback """
        self.draw_arm()

        # Keep UI sliders aligned with live angle position during file playback
        if getattr(self, 'is_playing', False):
            for i in range(4):
                if hasattr(self, 'sliders') and i < len(self.sliders):
                    self.sliders[i].set(self.current_angles[i])

        if self.app_running:
            self.window.after(33, self.update_visualization_loop)

    def poll_arduino(self):
        if self.connection.connected:
            reply = self.connection.send_command("GET")   # periodic sync every 5s
            if reply:
                try:
                    for i, v in enumerate(reply.split(",")[:4]):
                        self.current_angles[i] = float(v)
                except: pass
            else:
                self.update_connection_display(False)
        self.window.after(5000, self.poll_arduino)

    def flush_log(self):
        if not self.log_buffer: return
        exists = os.path.exists("arc3_telemetry.csv")
        try:
            with open("arc3_telemetry.csv", "a", newline="") as f:
                w = csv.writer(f)
                if not exists: w.writerow(["timestamp","yaw","shoulder","elbow","claw"])
                w.writerows(self.log_buffer)
            self.log_buffer.clear()
        except: pass

    def show_status(self, msg, color=WHITE):
        try: self.bottom_status.config(text=f"  {msg}", fg=color)
        except: pass

    def on_close(self):
        self.app_running = False
        self.is_playing  = False
        self.flush_log()
        self.ai_socket.stop()
        self.connection.disconnect()
        self.window.destroy()

    def run(self):
        self.window.update_idletasks()
        sw, sh = self.window.winfo_screenwidth(), self.window.winfo_screenheight()
        w, h = 1200, 780
        self.window.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.redraw_arm()
        self.window.after(20, self.update_visuals)   # refresh visuals on the Tk thread (~50 FPS)
        self.window.mainloop()


if __name__ == "__main__":
    app = ARC3App()
    app.run()
