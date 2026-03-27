#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>
#include <WiFiS3.h>

const char* WIFI_SSID     = "YOUR_WIFI_NAME";      // <-- change this
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";   // <-- change this
const int   SERVER_PORT   = 8888;

Adafruit_PWMServoDriver pca = Adafruit_PWMServoDriver(0x40);   // 0x40 = default I2C address (all addr pins to GND)

#define CH_YAW      0   // PCA9685 channel for base rotation
#define CH_SHOULDER 1   // PCA9685 channel for first pitch joint
#define CH_ELBOW    2   // PCA9685 channel for second pitch joint
#define CH_CLAW     3   // PCA9685 channel for claw

#define PULSE_MIN_US  500    // pulse width in microseconds at 0 degrees
#define PULSE_MAX_US  2500   // pulse width in microseconds at 180 degrees

// servo angle limits — must match SERVO_LIMITS in the Python file
const float ANGLE_MIN[4] = {  0.0f,  30.0f,   0.0f,  0.0f };
const float ANGLE_MAX[4] = {180.0f, 150.0f, 170.0f, 90.0f };

float currentAngles[4] = { 90.0f, 90.0f, 90.0f, 0.0f };   // start at home position

#define CLAW_GEAR_RATIO 2.0f   // 2:1 gear — python sends 0-90, servo only moves 0-45

WiFiServer server(SERVER_PORT);
WiFiClient client;         // only one connection at a time

String cmdBuffer = "";                            // accumulates incoming bytes until \n
unsigned long lastActivityMs = 0;
#define CLIENT_TIMEOUT_MS 8000   // drop client if no data for 8 seconds


void setup() {
    Serial.begin(115200);
    delay(500);

    Wire.begin();
    pca.begin();
    pca.setPWMFreq(50);   // MG995 servos need 50Hz (20ms period)
    delay(100);

    moveAllServos(currentAngles);   // drive to home so arm doesn't flail on startup
    Serial.println("Servos at home");

    Serial.print("Connecting to WiFi: ");
    Serial.println(WIFI_SSID);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    int tries = 0;
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
        if (++tries > 40) {   // give up after 20 seconds
            Serial.println("\nERROR: WiFi failed. Check SSID/password at top of sketch.");
            while (true) {
                digitalWrite(LED_BUILTIN, HIGH); delay(200);   // blink LED to signal failure
                digitalWrite(LED_BUILTIN, LOW);  delay(200);
            }
        }
    }

    Serial.println();
    Serial.print("Connected! IP: ");
    Serial.println(WiFi.localIP());    // <-- copy this IP into the Python GUI
    Serial.print("RSSI: ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm");

    server.begin();
    Serial.println("Server listening on port 8888");
}


void loop() {
    // if the current client disconnected, clean it up
    if (!client || !client.connected()) {
        if (client) {
            client.stop();
            Serial.println("Client disconnected");
        }
        WiFiClient incoming = server.available();   // check if a new client is waiting
        if (incoming) {
            client = incoming;
            cmdBuffer = "";
            lastActivityMs = millis();
            Serial.print("Client connected: ");
            Serial.println(client.remoteIP());
        }
    }

    if (client && client.connected()) {
        if (millis() - lastActivityMs > CLIENT_TIMEOUT_MS) {   // drop idle connections
            Serial.println("Client timeout");
            client.stop();
            return;
        }

        while (client.available()) {
            char c = client.read();
            lastActivityMs = millis();

            if (c == '\n') {                  // newline = end of command
                cmdBuffer.trim();
                if (cmdBuffer.length() > 0)
                    handleCommand(cmdBuffer);
                cmdBuffer = "";
            } else if (c != '\r') {
                cmdBuffer += c;
                if (cmdBuffer.length() > 256)   // safety: clear runaway buffer
                    cmdBuffer = "";
            }
        }
    }
}


void handleCommand(const String& cmd) {

    if (cmd == "PING") {                          // alive check
        client.println("PONG");
    }

    else if (cmd == "STATUS") {                   // returns JSON with IP, RSSI, and all angles
        String json = "{";
        json += "\"ip\":\""   + WiFi.localIP().toString() + "\",";
        json += "\"rssi\":"   + String(WiFi.RSSI()) + ",";
        json += "\"yaw\":"    + String(currentAngles[0], 1) + ",";
        json += "\"pitch1\":" + String(currentAngles[1], 1) + ",";
        json += "\"pitch2\":" + String(currentAngles[2], 1) + ",";
        json += "\"claw\":"   + String(currentAngles[3], 1);
        json += "}";
        client.println(json);
    }

    else if (cmd == "GET") {                      // returns just the four angles as CSV
        client.println(
            String(currentAngles[0],1) + "," +
            String(currentAngles[1],1) + "," +
            String(currentAngles[2],1) + "," +
            String(currentAngles[3],1)
        );
    }

    else if (cmd.startsWith("SETALL:")) {         // move all four servos at once
        String data = cmd.substring(7);           // strip the "SETALL:" prefix
        float vals[4];
        int found = 0, start = 0;

        for (int i = 0; i <= (int)data.length() && found < 4; i++) {
            if (i == (int)data.length() || data.charAt(i) == ',') {
                vals[found++] = data.substring(start, i).toFloat();   // parse each comma-separated float
                start = i + 1;
            }
        }

        if (found == 4) {
            moveAllServos(vals);
            client.println("OK");
        } else {
            client.println("ERR:BAD_FORMAT");
        }
    }

    else if (cmd == "STOP") {                     // emergency stop — just hold current position
        client.println("OK");
        Serial.println("STOP");
    }

    else {
        client.println("ERR:UNKNOWN");
    }
}


void moveAllServos(float angles[]) {
    for (int i = 0; i < 4; i++) {
        float a = constrain(angles[i], ANGLE_MIN[i], ANGLE_MAX[i]);   // clamp to safe range
        currentAngles[i] = a;

        if (i == CH_CLAW) {
            float servoAngle = constrain(a / CLAW_GEAR_RATIO, 0.0f, 45.0f);   // 2:1 ratio: halve the input angle
            setPWMAngle(i, servoAngle, 0.0f, 45.0f);
        } else {
            setPWMAngle(i, a, ANGLE_MIN[i], ANGLE_MAX[i]);   // all other servos map directly
        }
    }
}


void setPWMAngle(uint8_t channel, float angle, float minDeg, float maxDeg) {
    float t       = constrain((angle - minDeg) / (maxDeg - minDeg), 0.0f, 1.0f);   // normalize to 0.0-1.0
    float pulseUs = PULSE_MIN_US + t * (PULSE_MAX_US - PULSE_MIN_US);              // map to microseconds
    uint16_t ticks = (uint16_t)(pulseUs * 4096.0f / 20000.0f);                     // convert to 12-bit PCA9685 ticks (20000us period)
    pca.setPWM(channel, 0, ticks);                                                  // send to PCA9685
}
