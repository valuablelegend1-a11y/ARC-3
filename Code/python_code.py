import tkinter as tk
from tkinter import simpledialog
import socket
import threading
import json
import math
import time
import os
import csv
from datetime import datetime

DEFAULT_IP   = "192.168.1.100"  # change to your arduino's IP from serial monitor
DEFAULT_PORT = 8888

UPPER_ARM_LENGTH = 150.0  # shoulder to elbow in mm
LOWER_ARM_LENGTH = 130.0  # elbow to wrist in mm

SERVO_LIMITS = {         # [min_angle, max_angle] for each servo
    0: [0,   180],       # yaw
    1: [30,  150],       # shoulder
    2: [0,   170],       # elbow
    3: [0,    90],       # claw (0=open, 90=closed)
}

HOME_POSITION      = [90.0, 90.0, 90.0, 0.0]  # starting angles
DEGREES_PER_STEP   = 3.5                        # how far arm moves per 20ms tick
UPDATES_PER_SECOND = 50                         # motion loop frequency
POSITIONS_FILE     = "arc3_positions.json"      # saved positions persist here

BG       = "#080808"   # near-black background
PANEL    = "#0f0f0f"   # panel background
PANEL2   = "#141414"   # slightly lighter panel
BORDER   = "#1f1f1f"   # subtle panel borders
ORANGE   = "#FF6200"   # primary accent
ORANGE_L = "#FF8533"   # lighter orange for highlights
ORANGE_D = "#6b2900"   # dark orange for button backgrounds
WHITE    = "#FFFFFF"
GREY     = "#707070"
DGREY    = "#2a2a2a"
GREEN    = "#00E676"   # connected / success
RED      = "#FF1744"   # error / stop
YELLOW   = "#FFD600"   # warning
GRID     = "#181818"   # canvas grid lines

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
        dist     = math.sqrt(reach**2 + height**2)   # straight-line distance to target
        max_dist = self.upper + self.lower            # arm fully extended
        min_dist = abs(self.upper - self.lower)       # arm fully folded

        result = {"can_reach": False, "yaw": yaw,
                  "shoulder": HOME_POSITION[1], "elbow": HOME_POSITION[2]}

        if dist > max_dist * 0.99:              # too far — stretch toward target
            ang = math.atan2(height, reach)
            result["shoulder"] = 90.0 - math.degrees(ang)
            result["elbow"]    = 180.0
            return result

        if dist < min_dist + 1.0:              # too close — can't reach
            return result

        # law of cosines gives the elbow interior angle
        cos_e = (dist**2 - self.upper**2 - self.lower**2) / (2 * self.upper * self.lower)
        cos_e = max(-1.0, min(1.0, cos_e))     # clamp to valid acos range

        elbow_a = math.acos(cos_e) if self.elbow_up else -math.acos(cos_e)

        # use elbow angle to back-solve the shoulder angle
        k1 = self.upper + self.lower * math.cos(elbow_a)
        k2 = self.lower * math.sin(elbow_a)
        shoulder_a = math.atan2(height, reach) - math.atan2(k2, k1)

        # convert from math radians to servo degree convention (90 = straight up)
        sh = max(SERVO_LIMITS[1][0], min(SERVO_LIMITS[1][1], 90.0 - math.degrees(shoulder_a)))
        el = max(SERVO_LIMITS[2][0], min(SERVO_LIMITS[2][1], 90.0 - math.degrees(elbow_a)))

        result.update({"shoulder": sh, "elbow": el, "can_reach": True})
        return result

    def get_endpoint(self, sh_deg, el_deg):
        # forward kinematics: given angles, where is the tip? (used for visualizer)
        q1 = math.radians(90.0 - sh_deg)
        q2 = math.radians(90.0 - el_deg)
        x  = self.upper * math.cos(q1) + self.lower * math.cos(q1 + q2)
        y  = self.upper * math.sin(q1) + self.lower * math.sin(q1 + q2)
        return x, y


# --- WIFI CONNECTION ---
# wraps a plain TCP socket with a threading lock so the motion thread
# and GUI thread can't both write to it at the same time.

class ArmConnection:
    def __init__(self):
        self.socket     = None
        self.lock       = threading.Lock()  # prevents concurrent writes corrupting the stream
        self.connected  = False
        self.last_error = ""

    def connect(self, ip, port):
        self.disconnect()
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3.0)              # 3s to establish connection
            s.connect((ip, port))
            s.settimeout(2.0)              # 2s for individual send/receive
            with self.lock:
                self.socket    = s
                self.connected = True
            return True
        except Exception as e:
            self.last_error = str(e)
            self.connected  = False
            return False

    def disconnect(self):
        with self.lock:
            if self.socket:
                try: self.socket.close()
                except: pass
                self.socket = None
            self.connected = False

    def send_command(self, cmd):
        with self.lock:
            if not self.socket:
                return ""
            try:
                self.socket.sendall((cmd.strip() + "\n").encode())   # arduino reads until \n
                data = b""
                while not data.endswith(b"\n"):                      # read until newline reply
                    chunk = self.socket.recv(256)
                    if not chunk: break
                    data += chunk
                return data.decode().strip()
            except Exception as e:
                self.last_error = str(e)
                self.connected  = False
                return ""

    def ping(self):
        return self.send_command("PING") == "PONG"


# --- AI ASSISTANT SOCKET ---
# listens on localhost:9999 for JSON commands from an external program.
# send {"angles":[y,s,e,c]} to move the arm, {"home":true}, {"stop":true},
# or {"status":true}. completely separate from the arduino socket.

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
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server.bind(("127.0.0.1", self.port))
            self.server.listen(2)
            self.server.settimeout(1.0)
            while self.running:
                try:
                    conn, _ = self.server.accept()
                    threading.Thread(target=self._handle, args=(conn,), daemon=True).start()
                except socket.timeout:
                    pass
        except: pass

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
        self.logging_enabled   = False
        self.log_buffer        = []
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

        for x in range(0, W, 20): c.create_line(x, 0, x, H, fill=GRID)   # vertical grid
        for y in range(0, H, 20): c.create_line(0, y, W, y, fill=GRID)   # horizontal grid

        scale = (H * 0.38) / (UPPER_ARM_LENGTH + LOWER_ARM_LENGTH)   # mm to pixel scale
        ox, oy = W // 2, int(H * 0.82)   # base pivot point on canvas

        c.create_line(0, oy, W, oy, fill=DGREY)   # ground line
        col_h = int(20 * scale)
        c.create_rectangle(ox-4, oy, ox+4, oy-col_h, fill=DGREY, outline=BORDER)   # base column

        # forward kinematics: convert servo angles to joint positions
        q1 = math.radians(90 - self.current_angles[1])
        q2 = math.radians(90 - self.current_angles[2])
        ex = UPPER_ARM_LENGTH * math.cos(q1)                          # elbow x in mm
        ey = UPPER_ARM_LENGTH * math.sin(q1)                          # elbow y in mm
        wx = ex + LOWER_ARM_LENGTH * math.cos(q1 + q2)               # wrist x in mm
        wy = ey + LOWER_ARM_LENGTH * math.sin(q1 + q2)               # wrist y in mm

        base  = (ox,                     oy - col_h)
        elbow = (int(ox + ex * scale),   int(oy - ey * scale))
        wrist = (int(ox + wx * scale),   int(oy - wy * scale))

        r_max = int((UPPER_ARM_LENGTH + LOWER_ARM_LENGTH) * scale)
        r_min = int(abs(UPPER_ARM_LENGTH - LOWER_ARM_LENGTH) * scale)
        bx, by = base
        c.create_oval(bx-r_max, by-r_max, bx+r_max, by+r_max, outline=DGREY, dash=(3,7))   # max reach circle
        c.create_oval(bx-r_min, by-r_min, bx+r_min, by+r_min, outline=DGREY, dash=(3,7))   # min reach circle

        # shadow pass (offset by 2px)
        c.create_line(base[0]+2,  base[1]+2,  elbow[0]+2, elbow[1]+2, fill="#030303", width=8, capstyle="round")
        c.create_line(elbow[0]+2, elbow[1]+2, wrist[0]+2, wrist[1]+2, fill="#030303", width=6, capstyle="round")
        # actual arm segments
        c.create_line(base[0],  base[1],  elbow[0], elbow[1], fill=ORANGE,   width=5, capstyle="round")
        c.create_line(elbow[0], elbow[1], wrist[0], wrist[1], fill=ORANGE_L, width=4, capstyle="round")

        # claw fingers (open/close based on angle)
        claw_t = self.current_angles[3] / 90.0                               # 0=open, 1=closed
        arm_ang = math.atan2(wy - ey, wx - ex)
        perp    = arm_ang + math.pi / 2
        csize   = int(12 * scale * (1.0 - claw_t * 0.5))
        for side in (-1, 1):
            fx = int(wrist[0] + side * math.cos(perp) * csize * (1 - claw_t * 0.6))
            fy = int(wrist[1] + side * math.sin(perp) * csize * (1 - claw_t * 0.6))
            c.create_line(wrist[0], wrist[1], fx, fy, fill=WHITE, width=2, capstyle="round")

        for pt, col, r in [(base, WHITE, 5), (elbow, ORANGE_L, 4), (wrist, "#ff9944", 3)]:
            px, py = pt
            c.create_oval(px-r, py-r, px+r, py+r, fill=col, outline="")   # joint dots

        c.create_text(elbow[0]+8, elbow[1]-8, text=f"{self.current_angles[1]:.0f}°", font=FONT_XS, fill=GREY, anchor="w")
        c.create_text(wrist[0]+8, wrist[1]-8, text=f"{self.current_angles[2]:.0f}°", font=FONT_XS, fill=GREY, anchor="w")

        self.coord_label.config(text=f"R {wx:5.0f}mm  H {wy:5.0f}mm  Y {self.current_angles[0]:5.1f}°")

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

        reach, _ = self.ik.get_endpoint(self.current_angles[1], self.current_angles[2])
        yaw_rad  = math.radians(self.current_angles[0])
        tip_x    = int(cx + reach * scale * math.cos(yaw_rad - math.pi/2))
        tip_y    = int(cy + reach * scale * math.sin(yaw_rad - math.pi/2))

        c.create_line(cx+2, cy+2, tip_x+2, tip_y+2, fill="#030303", width=6)   # shadow
        c.create_line(cx,   cy,   tip_x,   tip_y,   fill=ORANGE,    width=3)   # arm projection
        c.create_oval(cx-5,    cy-5,    cx+5,    cy+5,    fill=WHITE,    outline="")
        c.create_oval(tip_x-4, tip_y-4, tip_x+4, tip_y+4, fill="#ff9944", outline="")
        c.create_text(cx, cy+r_max+11, text=f"YAW {self.current_angles[0]:.1f}°", font=FONT_XS, fill=GREY)

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

        self.touchpad = tk.Canvas(frame, bg="#0a0a0a", highlightthickness=1,
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
            ("drag X = yaw  |  drag Y = height (IK) or shoulder (direct)", GREY),
            ("scroll = reach (IK) or elbow (direct)", GREY),
            ("SPACE = close claw   CTRL = open claw   H = home   ESC = stop", ORANGE),
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

        yaw_frac = (self.current_angles[0] - SERVO_LIMITS[0][0]) / (SERVO_LIMITS[0][1] - SERVO_LIMITS[0][0])
        if self.ik_mode:
            h_frac = 1.0 - min(1.0, max(0.0, self.ik_height / ((UPPER_ARM_LENGTH + LOWER_ARM_LENGTH) * 0.8)))
        else:
            h_frac = 1.0 - (self.current_angles[1] - SERVO_LIMITS[1][0]) / (SERVO_LIMITS[1][1] - SERVO_LIMITS[1][0])

        cx = int(yaw_frac * W)
        cy = int(h_frac   * H)
        c.delete("cursor")

        c.create_line(cx-16, cy, cx+16, cy, fill=ORANGE,   width=2, tags="cursor")   # horizontal crosshair
        c.create_line(cx, cy-16, cx, cy+16, fill=ORANGE,   width=2, tags="cursor")   # vertical crosshair
        c.create_oval(cx-5, cy-5, cx+5, cy+5, fill=ORANGE, outline=ORANGE_L, width=2, tags="cursor")   # center dot

        reach, height = self.ik.get_endpoint(self.current_angles[1], self.current_angles[2])
        self.ik_readout.config(text=f"R:{reach:.0f}mm  H:{self.ik_height:.0f}mm  Y:{self.current_angles[0]:.1f}°")

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

        new_yaw = self.target_angles[0] + dx * (180.0 / W)   # scale drag pixels to degrees
        new_yaw = max(SERVO_LIMITS[0][0], min(SERVO_LIMITS[0][1], new_yaw))
        self.target_angles[0] = new_yaw

        if self.ik_mode:
            self.ik_yaw    = new_yaw
            self.ik_height = max(0, self.ik_height - dy * (80.0 / H))   # drag up = increase height
            res = self.ik.solve(self.ik_reach, self.ik_height, self.ik_yaw)
            if res["can_reach"]:
                self.target_angles[1] = res["shoulder"]
                self.target_angles[2] = res["elbow"]
            else:
                self.show_status("out of reach", YELLOW)
        else:
            sh = self.target_angles[1] - dy * (120.0 / H)   # drag up = raise shoulder
            self.target_angles[1] = max(SERVO_LIMITS[1][0], min(SERVO_LIMITS[1][1], sh))

        self.update_sliders()
        self.draw_touchpad_cursor()
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
            sl.set(HOME_POSITION[i])
            sl.grid(row=i*2+1, column=0, sticky="ew", padx=8, pady=(1,0))
            self.sliders.append(sl)

        tk.Label(frame, bg=PANEL, height=1).grid(row=8, column=0)

        tk.Label(frame, text="SPEED", font=FONT_XS, bg=PANEL, fg=GREY).grid(row=9, column=0, sticky="w", padx=8)
        spd = tk.Scale(frame, from_=0.1, to=3.0, resolution=0.1,
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
        self.make_btn(btns, "STOP", self.emergency_stop, "#500000", RED,  row=0, column=1, sticky="ew", padx=(2,0))

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
        self.target_angles[idx] = val
        self.val_labels[idx].config(text=f"{val:.1f}°")
        if self.is_recording:
            self.recorded_frames.append((list(self.target_angles), time.time()))

    def update_sliders(self):
        for i, s in enumerate(self.sliders):
            s.set(self.target_angles[i])
            self.val_labels[i].config(text=f"{self.target_angles[i]:.1f}°")

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
        self.make_btn(btn_row, "SAVE", self.save_position,   ORANGE_D, ORANGE, pack="pack", side="left")
        self.make_btn(btn_row, "DEL",  self.delete_position, DGREY,    RED,    pack="pack", side="left", padx=(3,0))

        lf = tk.Frame(frame, bg=PANEL)
        lf.grid(row=1, column=0, sticky="nsew", padx=6)
        lf.rowconfigure(0, weight=1)
        lf.columnconfigure(0, weight=1)

        self.positions_list = tk.Listbox(lf, bg="#0a0a0a", fg=WHITE, font=FONT_SM,
                                          selectbackground=ORANGE_D, selectforeground="#ff9944",
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

        self.make_btn(frame, "● REC",  self.toggle_recording, "#500000", RED,   row=1, column=0, sticky="ew", padx=(8,2), pady=3)
        self.make_btn(frame, "▶ PLAY", self.play_recording,   DGREY,     GREEN, row=1, column=1, sticky="ew", padx=(2,8), pady=3)

        self.frame_count_label = tk.Label(frame, text="0 frames", font=FONT_XS, bg=PANEL, fg=GREY)
        self.frame_count_label.grid(row=2, column=0, columnspan=2, sticky="w", padx=8, pady=2)

        self.loop_var = tk.BooleanVar(value=False)
        tk.Checkbutton(frame, text="Loop", variable=self.loop_var,
                       font=FONT_XS, bg=PANEL, fg=WHITE, selectcolor=ORANGE_D,
                       activebackground=PANEL).grid(row=3, column=0, sticky="w", padx=8, pady=2)

        self.log_var = tk.BooleanVar(value=False)
        tk.Checkbutton(frame, text="Log CSV", variable=self.log_var,
                       font=FONT_XS, bg=PANEL, fg=WHITE, selectcolor=DGREY,
                       activebackground=PANEL,
                       command=lambda: setattr(self, "logging_enabled", self.log_var.get())
                       ).grid(row=4, column=0, sticky="w", padx=8, pady=2)

        # AI integration hook note
        tk.Label(frame, text="AI port 9999 active\n{\"angles\":[y,s,e,c]}\n{\"home\":true}  {\"stop\":true}",
                 font=FONT_XS, bg=PANEL, fg=ORANGE_D, justify="left"
                 ).grid(row=5, column=0, columnspan=2, sticky="sw", padx=8, pady=(8,6))

    def toggle_recording(self):
        if not self.is_recording:
            self.is_recording    = True
            self.recorded_frames = []
            self.rec_status_label.config(text="● REC", fg=RED)
            self.show_status("Recording...", RED)
        else:
            self.is_recording = False
            n = len(self.recorded_frames)
            self.rec_status_label.config(text=f"DONE ({n}f)", fg=GREEN)
            self.frame_count_label.config(text=f"{n} frames")
            self.show_status(f"Recorded {n} frames", GREEN)

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
                    elapsed = ts - t_0                          # how far into the recording this frame is
                    wait    = elapsed - (time.time() - t0)     # how long to sleep to match original timing
                    if wait > 0: time.sleep(wait)
                if not self.loop_var.get(): break
            self.is_playing = False
            self.rec_status_label.config(text="IDLE", fg=GREY)

        threading.Thread(target=playback, daemon=True).start()

    # --- CONNECTION PANEL ---

    def make_connection_panel(self, parent, row, col):
        frame = self.make_panel(parent, "CONNECTION", row, col, sticky="nsew", padx=(3, 0))
        frame.columnconfigure(1, weight=1)

        tk.Label(frame, text="Arduino IP", font=FONT_XS, bg=PANEL, fg=GREY).grid(row=0, column=0, sticky="w", padx=8, pady=(8,2))
        tk.Label(frame, text="(from Serial Monitor at 115200)", font=FONT_XS, bg=PANEL, fg=DGREY).grid(row=1, column=0, columnspan=2, sticky="w", padx=8)

        self.ip_input = tk.StringVar(value=DEFAULT_IP)
        tk.Entry(frame, textvariable=self.ip_input, font=FONT_NORM,
                 bg="#0a0a0a", fg=WHITE, insertbackground=ORANGE,
                 highlightcolor=ORANGE, highlightthickness=1,
                 relief="flat", width=18
                 ).grid(row=2, column=0, columnspan=2, sticky="ew", padx=8, pady=(2,4))

        tk.Label(frame, text="Port", font=FONT_XS, bg=PANEL, fg=GREY).grid(row=3, column=0, sticky="w", padx=8, pady=(4,2))
        self.port_input = tk.StringVar(value=str(DEFAULT_PORT))
        tk.Entry(frame, textvariable=self.port_input, font=FONT_NORM,
                 bg="#0a0a0a", fg=WHITE, insertbackground=ORANGE,
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

        tk.Frame(frame, bg=BORDER, height=1).grid(row=8, column=0, columnspan=2, sticky="ew", padx=8, pady=6)

        tk.Label(frame,
                 text="1. Upload firmware\n2. Serial Monitor 115200\n3. Copy IP here\n4. CONNECT",
                 font=FONT_XS, bg=PANEL, fg=DGREY, justify="left"
                 ).grid(row=9, column=0, columnspan=2, sticky="w", padx=8)

    def toggle_connection(self):
        if self.connection.connected:
            self.connection.disconnect()
            self.update_connection_display(False)
            self.show_status("Disconnected", GREY)
        else:
            self.show_status("Connecting...", YELLOW)
            self.window.update()
            ip = self.ip_input.get().strip()
            try:    port = int(self.port_input.get())
            except: port = DEFAULT_PORT
            ok = self.connection.connect(ip, port)
            self.update_connection_display(ok)
            if ok:
                self.show_status(f"Connected {ip}:{port}", GREEN)
                self.sync_with_arduino()
            else:
                self.show_status(f"Failed: {self.connection.last_error}", RED)

    def update_connection_display(self, connected):
        if connected:
            self.status_dot.config(fg=GREEN)
            self.status_text.config(text="ONLINE", fg=GREEN)
            self.connect_button.config(text="DISCONNECT", bg="#500000", fg=RED)
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

    def sync_with_arduino(self):
        if not self.connection.connected: return
        reply = self.connection.send_command("STATUS")   # ask arduino for current state
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

    # --- KEYBOARD ---

    def key_pressed(self, event):
        k = event.keysym.lower()
        if k == "space" and not self.space_held:
            self.space_held = True
            self.target_angles[3] = SERVO_LIMITS[3][1]   # close claw fully
            self.update_sliders()
        elif k in ("control_l","control_r") and not self.ctrl_held:
            self.ctrl_held = True
            self.target_angles[3] = SERVO_LIMITS[3][0]   # open claw fully
            self.update_sliders()
        elif k == "h": self.go_home()
        elif k == "escape": self.emergency_stop()
        elif k == "left":  self.target_angles[0] = max(SERVO_LIMITS[0][0], self.target_angles[0]-2); self.update_sliders()
        elif k == "right": self.target_angles[0] = min(SERVO_LIMITS[0][1], self.target_angles[0]+2); self.update_sliders()
        elif k == "up":    self.target_angles[1] = max(SERVO_LIMITS[1][0], self.target_angles[1]-2); self.update_sliders()
        elif k == "down":  self.target_angles[1] = min(SERVO_LIMITS[1][1], self.target_angles[1]+2); self.update_sliders()

    def key_released(self, event):
        k = event.keysym.lower()
        if k == "space":                   self.space_held = False
        elif k in ("control_l","control_r"): self.ctrl_held = False

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
        interval = 1.0 / UPDATES_PER_SECOND
        while self.app_running:
            t0   = time.perf_counter()
            step = DEGREES_PER_STEP * self.speed
            moved = False

            for i in range(4):
                diff = self.target_angles[i] - self.current_angles[i]
                if abs(diff) > 0.1:                                   # ignore tiny differences
                    self.current_angles[i] += math.copysign(min(abs(diff), step), diff)   # step toward target
                    self.current_angles[i]  = max(SERVO_LIMITS[i][0],
                                                   min(SERVO_LIMITS[i][1], self.current_angles[i]))
                    moved = True

            if moved and self.connection.connected:
                cmd = "SETALL:" + ",".join(f"{a:.1f}" for a in self.current_angles)
                self.connection.send_command(cmd)   # send updated angles to arduino

            if self.logging_enabled:
                self.log_buffer.append([datetime.now().isoformat(), *self.current_angles])
                if len(self.log_buffer) >= 100: self.flush_log()   # flush every 100 rows

            if moved: self.window.after_idle(self.update_visuals)

            wait = interval - (time.perf_counter() - t0)
            if wait > 0: time.sleep(wait)

    def update_visuals(self):
        try:
            self.redraw_arm()
            self.draw_touchpad_cursor()
            self.angle_display.config(
                text=f"Y {self.current_angles[0]:5.1f}°  S {self.current_angles[1]:5.1f}°  "
                     f"E {self.current_angles[2]:5.1f}°  C {self.current_angles[3]:4.1f}°"
            )
        except: pass

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
        self.window.mainloop()


if __name__ == "__main__":
    app = ARC3App()
    app.run()