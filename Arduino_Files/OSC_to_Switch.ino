#include <WiFi.h>
#include <WiFiUdp.h>
#include <OSCMessage.h>

char ssid[] = "sandbox370";
char pass[] = "-------------";

WiFiUDP udp;
OSCErrorCode error;
const unsigned int localPort = 8000;

const int relayPin = A1;

void setup() {
  pinMode(relayPin, OUTPUT);
  digitalWrite(relayPin, LOW);

  Serial.begin(9600);

  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, pass);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");

  Serial.println("WiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());

  Serial.println("Starting UDP");
  udp.begin(localPort);
  Serial.print("Local port: ");
  Serial.println(localPort);
  Serial.println("------------------------------------------");
  Serial.println("Ready to receive OSC commands at /relay/state (int: 0 or 1)");
}

void relayControlHandler(OSCMessage &msg) {
  if (msg.isInt(0)) {
    int relayState = msg.getInt(0);

    if (relayState == 1) {
        digitalWrite(relayPin, HIGH);
        Serial.println("/relay/state: 1 (ON)");
    } else if (relayState == 0) {
        digitalWrite(relayPin, LOW);
        Serial.println("/relay/state: 0 (OFF)");
    } else {
        Serial.print("/relay/state: Received invalid integer ");
        Serial.println(relayState);
    }
  } else {
      Serial.println("/relay/state: Received non-integer argument");
  }
}

void loop() {
  OSCMessage msg;
  int size = udp.parsePacket();

  if (size > 0) {
    while (size--) {
      msg.fill(udp.read());
    }
    if (!msg.hasError()) {
      msg.dispatch("/relay/state", relayControlHandler);
    } else {
      error = msg.getError();
      Serial.print("OSC Error: ");
      Serial.println(error);
    }
  }
}