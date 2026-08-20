#include <Wire.h> 
#include <Adafruit_PWMServoDriver.h> 
#include <WiFiS3.h> 

// --- WiFi Configuration ---
const char* WIFI_SSID     = "YourWIFIName"; 
const char* WIFI_PASSWORD = "YourWIFIPassword"; 
const int   SERVER_PORT   = 8888; 

// --- Static IP (optional) ---
// DHCP (default) can hand this board a NEW address after a reboot, which is
// why the app sometimes cannot find it. To make the address permanent either:
//   A) Set a DHCP reservation on your router for this board's MAC (no reflash),
//      or
//   B) set USE_STATIC_IP to 1 and edit LOCAL_IP/GATEWAY_IP below. Reflash once
//      and the IP never changes again.
#define USE_STATIC_IP 1
#if USE_STATIC_IP
IPAddress LOCAL_IP(192, 168, 4, 73);
IPAddress GATEWAY_IP(192, 168, 4, 1);
IPAddress SUBNET_MASK(255, 255, 252, 0);
#endif

// --- PCA9685 Servo Driver ---
Adafruit_PWMServoDriver pca = Adafruit_PWMServoDriver(0x40); 

#define CH_YAW      0 
#define CH_SHOULDER 1 
#define CH_ELBOW    2 
#define CH_CLAW     3 

#define PULSE_MIN_US 500 
#define PULSE_MAX_US 2400 

const float ANGLE_MIN[4] = { 0.0f,   0.0f,   0.0f,   0.0f   }; 
const float ANGLE_MAX[4] = { 180.0f, 260.0f, 180.0f, 180.0f }; 
const float HOME_POS[4]  = { 90.0f,  70.0f,  90.0f,  0.0f   }; // matches GUI HOME_POSITION
float targetAngles[4]    = { 90.0f,  70.0f,  90.0f,  0.0f   }; // last commanded angles (GET reports these)
float servoAngles[4]     = { 90.0f,  70.0f,  90.0f,  0.0f   }; // eased physical position servos actually hold
uint16_t lastWrittenPulse[4] = {0, 0, 0, 0};

// Motion: one servo eases toward its target per 20ms tick (round-robin).
// Moving a single joint at a time keeps peak current low so a saggy 5V supply
// does not drop every joint at once - slow, smooth, and strong. It also makes
// the arm immune to bursty WiFi command delivery.
#define SLEW_TICK_MS 20
#define SLEW_EPS 0.5f
const float SLEW_STEP_DEG[4] = { 3.0f, 3.0f, 3.0f, 1.5f };  // per 20ms tick
#define REASSERT_MS 500        // re-drive all channels periodically (glitch recovery)
#define TEST_STEP_DEG 2.0f     // TEST sweep speed per 20ms tick

WiFiServer server(SERVER_PORT); 
WiFiClient client; 
String cmdBuffer = ""; 
String serialCmdBuffer = "";
unsigned long lastActivityMs = 0; 
unsigned long lastWifiPollMs = 0;
unsigned long lastWifiRetryMs = 0;
bool wifiReady = false;
#define CLIENT_TIMEOUT_MS 8000 
#define WIFI_RETRY_MS 10000   // how often to (re)try WiFi when not connected

// Servo test / diagnostics
bool testActive = false;
int  testChannel = -1;
float testPos = 0.0f;
int  testPhase = 0;

// Forward declarations
void homeServos();
void setTargets(const float vals[]);
void writeServoPulse(uint8_t channel, float angle);
void updateMotion();
void reassertServos();
void processSerialInput();
void handleCommand(const String& cmd, Print& out, bool replyToSetAll);

void setup() { 
  Serial.begin(115200); 
  delay(500); 

  Wire.begin(); 
  Wire.setWireTimeout(50000, true);  // never hang on a stuck/bad I2C bus
  if (!pca.begin()) {
    Serial.println("[ERROR] PCA9685 servo driver NOT found on I2C (address 0x40).");
    Serial.println("        Check SDA/SCL wiring, VCC, and that address jumpers = 0x40.");
  } else {
    pca.setPWMFreq(50); 
    Serial.println("[OK] PCA9685 servo driver detected.");
  }
  delay(100); 

  // Move servos to initial home position
  homeServos(); 
  Serial.println("Servos initialized at home position."); 

  // Connect to Wi-Fi
  Serial.print("Connecting to WiFi network: "); 
  Serial.println(WIFI_SSID); 
#if USE_STATIC_IP
  WiFi.config(LOCAL_IP, GATEWAY_IP, SUBNET_MASK);
  Serial.println("Using static IP address.");
#endif
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD); 

  int tries = 0; 
  while (WiFi.status() != WL_CONNECTED) { 
    processSerialInput();
    delay(500); 
    Serial.print("."); 
    if (++tries > 16) { 
      Serial.println("\n[WARN] WiFi failed. Continuing in USB serial mode."); 
      break;
    } 
  } 

  if (WiFi.status() == WL_CONNECTED) {
    wifiReady = true;
    delay(1000); 

    Serial.println("\n==========================================");
    Serial.print("Connected successfully! IP Address: "); 
    Serial.println(WiFi.localIP()); 
    Serial.print("Signal Strength (RSSI): "); 
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm"); 
    Serial.println("==========================================");

    server.begin(); 
    Serial.println("Server listening on port 8888..."); 
  }
  Serial.println("USB serial command mode ready at 115200 baud.");
} 

void loop() { 
  processSerialInput();

  // Smooth, power-friendly motion. updateMotion() eases servos one at a time
  // (tick-throttled), and reassertServos() periodically re-drives every
  // channel so a sagged/reset servo driver recovers and keeps holding.
  updateMotion();
  reassertServos();

  // WiFi auto-reconnect. If the network was slow/unavailable at boot, or the
  // link drops later, keep retrying instead of giving up until reboot. USB
  // serial stays fully usable the whole time.
  if (!wifiReady) {
    if (WiFi.status() == WL_CONNECTED) {
      wifiReady = true;
      server.begin();
      Serial.println("\n[OK] WiFi (re)connected. IP: " + String(WiFi.localIP()));
    } else if (millis() - lastWifiRetryMs >= WIFI_RETRY_MS) {
      lastWifiRetryMs = millis();
      Serial.println("[WIFI] Connecting to " + String(WIFI_SSID) + "...");
      WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    }
    return;
  }

  // Runtime link watchdog: if WiFi drops mid-run, fall back to reconnecting.
  if (WiFi.status() != WL_CONNECTED) {
    wifiReady = false;
    if (client) {
      client.stop();
      client = WiFiClient();
    }
    Serial.println("[WIFI] Link lost - auto-reconnect enabled.");
    return;
  }

  // Throttle WiFi polling so a slow/wedged ESP32-S3 stack can never
  // starve USB serial command processing (USB is the primary path).
  if (millis() - lastWifiPollMs < 2) {
    return;
  }
  lastWifiPollMs = millis();

  // Handle client connections
  if (!client || !client.connected()) { 
    if (client) { 
      client.stop(); 
      Serial.println("Client disconnected."); 
    } 
    WiFiClient incoming = server.available(); 
    if (incoming) { 
      client = incoming; 
      cmdBuffer = ""; 
      lastActivityMs = millis(); 
      Serial.print("Client connected from IP: "); 
      Serial.println(client.remoteIP()); 
    } 
  } 

  // Process incoming data from client
  if (client && client.connected()) { 
    if (millis() - lastActivityMs > CLIENT_TIMEOUT_MS) { 
      Serial.println("Client inactive. Connection timed out."); 
      client.stop(); 
      return; 
    } 
    while (client.available()) { 
      char c = client.read(); 
      lastActivityMs = millis(); 
      if (c == '\n') { 
        cmdBuffer.trim(); 
        if (cmdBuffer.length() > 0) {
          handleCommand(cmdBuffer, client, false); 
        }
        cmdBuffer = ""; 
      } else if (c != '\r') { 
        cmdBuffer += c; 
        if (cmdBuffer.length() > 256) cmdBuffer = ""; 
      } 
    } 
  } 
} 

void processSerialInput() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      serialCmdBuffer.trim();
      if (serialCmdBuffer.length() > 0) {
        handleCommand(serialCmdBuffer, Serial, false);
      }
      serialCmdBuffer = "";
    } else if (c != '\r') {
      serialCmdBuffer += c;
      if (serialCmdBuffer.length() > 256) serialCmdBuffer = "";
    }
  }
}

void handleCommand(const String& cmd, Print& out, bool replyToSetAll) { 
  if (cmd == "PING") { 
    out.println("PONG"); 
  }  
  else if (cmd == "STATUS") { 
    if (wifiReady) {
      out.print("IP:"); 
      out.println(WiFi.localIP()); 
    } else {
      out.println("USB:READY");
    }
  }  
  else if (cmd == "GET") { 
    out.print(targetAngles[0]); out.print(","); 
    out.print(targetAngles[1]); out.print(","); 
    out.print(targetAngles[2]); out.print(","); 
    out.println(targetAngles[3]); 
  }  
  else if (cmd.startsWith("TEST:")) { 
    int ch = cmd.substring(5).toInt(); 
    if (ch >= 0 && ch < 4) { 
      testActive = true; 
      testChannel = ch; 
      testPos = servoAngles[ch]; 
      testPhase = 0; 
      out.println("OK TESTING:" + String(ch)); 
    } else { 
      out.println("ERR:CHANNEL"); 
    } 
  }  
  else if (cmd == "STOP") {
    testActive = false;
    testChannel = -1;
    out.println("OK");
  }
  else if (cmd.startsWith("SETALL:")) { 
    String data = cmd.substring(7); 
    float vals[4]; 
    int found = 0; 
    int startIdx = 0; 

    // Parse comma-separated angles
    for (int i = 0; i < data.length(); i++) { 
      if (data.charAt(i) == ',' || i == data.length() - 1) { 
        int endIdx = (i == data.length() - 1) ? i + 1 : i; 
        vals[found] = data.substring(startIdx, endIdx).toFloat(); 
        found++; 
        startIdx = i + 1; 
        if (found >= 4) break; 
      } 
    } 

    if (found == 4) { 
      setTargets(vals); 
      if (replyToSetAll) out.println("OK");
    } else { 
      out.println("ERR:BAD_FORMAT"); 
    } 
  }  
  else { 
    out.println("ERR:UNKNOWN"); 
  } 
} 

void writeServoPulse(uint8_t channel, float angle) { 
  float t = constrain((angle - ANGLE_MIN[channel]) / (ANGLE_MAX[channel] - ANGLE_MIN[channel]), 0.0f, 1.0f); 
  float pulseUs = PULSE_MIN_US + t * (PULSE_MAX_US - PULSE_MIN_US); 
  uint16_t targetPulse = (uint16_t)constrain(pulseUs, 400, 2600); 
  if (abs((int)targetPulse - (int)lastWrittenPulse[channel]) >= 2) {
    pca.writeMicroseconds(channel, targetPulse); 
    lastWrittenPulse[channel] = targetPulse;
  }
}

void homeServos() { 
  for (int i = 0; i < 4; i++) { 
    targetAngles[i] = HOME_POS[i]; 
    servoAngles[i]  = HOME_POS[i]; 
    writeServoPulse(i, HOME_POS[i]); 
  } 
}

void setTargets(const float vals[]) { 
  for (int i = 0; i < 4; i++) { 
    targetAngles[i] = constrain(vals[i], ANGLE_MIN[i], ANGLE_MAX[i]); 
  } 
}

void updateMotion() { 
  static unsigned long lastSlewMs = 0; 
  static int slewCursor = 0; 
  unsigned long now = millis(); 

  // TEST sweep mode (diagnose a single servo channel)
  if (testActive && testChannel >= 0 && testChannel < 4) { 
    if (now - lastSlewMs >= SLEW_TICK_MS) { 
      lastSlewMs = now; 
      if (testPhase == 0) { 
        testPos += TEST_STEP_DEG; 
        if (testPos >= ANGLE_MAX[testChannel]) { testPos = ANGLE_MAX[testChannel]; testPhase = 1; } 
      } else { 
        testPos -= TEST_STEP_DEG; 
        if (testPos <= ANGLE_MIN[testChannel]) { testPos = ANGLE_MIN[testChannel]; testPhase = 0; } 
      } 
      servoAngles[testChannel] = testPos; 
      writeServoPulse(testChannel, testPos); 
    } 
    return; 
  } 

  if (now - lastSlewMs < SLEW_TICK_MS) return; 
  lastSlewMs = now; 

  // Ease ONE servo toward its target per tick (round-robin scan). Moving a 
  // single joint at a time limits simultaneous surge current so a saggy 5V 
  // supply doesn't drop every joint at once - each servo keeps more power. 
  for (int i = 0; i < 4; i++) { 
    int ch = (slewCursor + i) % 4; 
    float diff = targetAngles[ch] - servoAngles[ch]; 
    if (fabsf(diff) > SLEW_EPS) { 
      float step = SLEW_STEP_DEG[ch]; 
      servoAngles[ch] += (diff > 0 ? step : -step); 
      if (fabsf(targetAngles[ch] - servoAngles[ch]) < step) servoAngles[ch] = targetAngles[ch]; 
      writeServoPulse(ch, servoAngles[ch]); 
      slewCursor = (ch + 1) % 4; 
      return; 
    } 
  } 
  slewCursor = (slewCursor + 1) % 4; 
} 

void reassertServos() { 
  static unsigned long lastReassertMs = 0; 
  unsigned long now = millis(); 
  if (now - lastReassertMs < REASSERT_MS) return; 
  lastReassertMs = now; 
  // Force-write every channel so a glitched/reset PCA9685 or sagged servo 
  // recovers and keeps holding its position. 
  for (int i = 0; i < 4; i++) { 
    float t = constrain((servoAngles[i] - ANGLE_MIN[i]) / (ANGLE_MAX[i] - ANGLE_MIN[i]), 0.0f, 1.0f); 
    uint16_t p = (uint16_t)constrain(PULSE_MIN_US + t * (PULSE_MAX_US - PULSE_MIN_US), 400, 2600); 
    pca.writeMicroseconds(i, p); 
    lastWrittenPulse[i] = p; 
  } 
}
