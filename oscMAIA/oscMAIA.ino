#include <Arduino.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include <OSCMessage.h>
#include <Adafruit_NeoPixel.h>

const char* ssid = "------";
const char* pass = "------";

WiFiUDP udp;
OSCErrorCode error;
//const IPAddress remoteIp(192, 168, 1, 186); 
const unsigned int remotePort = 12000; 
const unsigned int localPort = 8000;   

#define LED_PIN 2 //GPIO5                        
#define NUM_LEDS 16                    
Adafruit_NeoPixel strip(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

int brightness = 255;

void setup() {
     Serial.begin(115200);
     delay(1000);
  //thanks Scott F!
  while(!Serial){;;}

  // Connect to WiFi network
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, pass);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());

  Serial.println("Starting UDP Listening port");
  udp.begin(localPort);
  Serial.print("Local port: ");
  Serial.println(localPort);

  strip.begin();
  //test, led receiving?..set to red
  strip.setBrightness(255); 
  for (int i = 0; i < NUM_LEDS; i++) {
      strip.setPixelColor(i, strip.Color(255, 0, 0));
  }
  strip.show();
  delay(2000);
  strip.clear();
  //end test - i got nothing :(
  strip.show();
}

void loop() {
    int packetSize = udp.parsePacket();
    if (packetSize) {
        OSCMessage msg;
        while (packetSize--) {
            msg.fill(udp.read());
        }
        if (!msg.hasError()) {
           // Serial.print("OSC Message Received: ");
            msg.route("/brightness", storeBrightness);
        } else {
            Serial.println("OSC Message Error!");
            Serial.println(msg.getError());
        }
    }
    delay(5);
}

void storeBrightness(OSCMessage &msg, int addrOffset) {
    if (msg.isInt(0)) { 
        brightness = constrain(msg.getInt(0), 0, 255);
        //Serial.print("Received Brightness Value: ");
        Serial.println(brightness);
        updateLEDs();
        delay(50); //this fixes some chop from the data
    } else {
        Serial.println("Invalid OSC Message Format!");
    }
}

void updateLEDs() {
    strip.setBrightness(brightness);
    for (int i = 0; i < NUM_LEDS; i++) {
        strip.setPixelColor(i, strip.Color(brightness, brightness, 0)); 
    }
    strip.show();
}


