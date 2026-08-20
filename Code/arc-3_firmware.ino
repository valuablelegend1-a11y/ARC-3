#include <Wire.h> 
#include <Adafruit_PWMServoDriver.h> 
#include <WiFiS3.h> 


const char* WIFI_SSID     = "YourWIFIName"; 
const char* WIFI_PASSWORD = "YourWIFIPassword"; 
const int   SERVER_PORT   = 8888; 


#define USE_STATIC_IP 1
#if USE_STATIC_IP
IPAddress LOCAL_IP(YourAvailableDesiredIP);
IPAddress GATEWAY_IP(YourRoutersIP);
IPAddress SUBNET_MASK(YourSubnetMask);
#endif


Adafruit_PWMServoDriver pca = Adafruit_PWMServoDriver(0x40); 

#define CH_YAW      0 
#define CH_SHOULDER 1 
#define CH_ELBOW    2 
#define CH_CLAW     3 

#define PULSE_MIN_US 500 
#define PULSE_MAX_US 2400 

const float ANGLE_MIN[4] = { 0.0f,   0.0f,   0.0f,   0.0f   }; 
const float ANGLE_MAX[4] = { 180.0f, 260.0f, 180.0f, 180.0f }; 
const float HOME_POS[4]  = { 90.0f,  70.0f,  90.0f,  0.0f   }; 
float targetAngles[4]    = { 90.0f,  70.0f,  90.0f,  0.0f   }; 
float servoAngles[4]     = { 90.0f,  70.0f,  90.0f,  0.0f   }; 
uint16_t lastWrittenPulse[4] = {0, 0, 0, 0};


#define SLEW_TICK_MS 20
#define SLEW_EPS 0.5f
const float SLEW_STEP_DEG[4] = { 3.0f, 3.0f, 3.0f, 1.5f };  
#define REASSERT_MS 500        
#define TEST_STEP_DEG 2.0f    

WiFiServer server(SERVER_PORT); 
WiFiClient client; 
String cmdBuffer = ""; 
String serialCmdBuffer = "";
unsigned long lastActivityMs = 0; 
unsigned long lastWifiPollMs = 0;
unsigned long lastWifiRetryMs = 0;
bool wifiReady = false;
#define CLIENT_TIMEOUT_MS 8000 
#define WIFI_RETRY_MS 10000   


bool testActive = false;
int  testChannel = -1;
float testPos = 0.0f;
int  testPhase = 0;


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
  Wire.setWireTimeout(50000, true);  
  if (!pca.begin()) {
    Serial.println("[ERROR] PCA9685 servo driver NOT found on I2C (address 0x40).");
    Serial.println("        Check SDA/SCL wiring, VCC, and that address jumpers = 0x40.");
  } else {
    pca.setPWMFreq(50); 
    Serial.println("[OK] PCA9685 servo driver detected.");
  }
  delay(100); 

  
  homeServos(); 
  Serial.println("Servos initialized at home position."); 

 
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

  
  updateMotion();
  reassertServos();

  
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

  
  if (WiFi.status() != WL_CONNECTED) {
    wifiReady = false;
    if (client) {
      client.stop();
      client = WiFiClient();
    }
    Serial.println("[WIFI] Link lost - auto-reconnect enabled.");
    return;
  }

  
  if (millis() - lastWifiPollMs < 2) {
    return;
  }
  lastWifiPollMs = millis();

  
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
  for (int i = 0; i < 4; i++) { 
    float t = constrain((servoAngles[i] - ANGLE_MIN[i]) / (ANGLE_MAX[i] - ANGLE_MIN[i]), 0.0f, 1.0f); 
    uint16_t p = (uint16_t)constrain(PULSE_MIN_US + t * (PULSE_MAX_US - PULSE_MIN_US), 400, 2600); 
    pca.writeMicroseconds(i, p); 
    lastWrittenPulse[i] = p; 
  } 
}
