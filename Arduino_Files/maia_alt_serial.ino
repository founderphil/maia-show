#include <Adafruit_NeoPixel.h>
#include <math.h>  

#define LED_PIN        5     // GPIO-5 (D2 on many ESP32 boards)
#define LED_COUNT    600
#define SPARKLE_COUNT 600

Adafruit_NeoPixel strip(LED_COUNT, LED_PIN, NEO_RGBW + NEO_KHZ800);

const uint16_t listeningTimeout = 1000;

enum Mode : uint8_t { MODE_OFF = 0, MODE_SPARKLE, MODE_SCANNER };
Mode mode = MODE_OFF;

bool     currentlyTalking = false;
uint8_t  talkingVal       = 0;     
unsigned long lastActivity = 0;    // time of last non-“B” byte, or not for the switch
unsigned long lastScannerUpdate = 0;

int sparkleIndices[SPARKLE_COUNT];
int sparkleTypes  [SPARKLE_COUNT];
float sparklePhases [SPARKLE_COUNT];

void setup() {
  Serial.begin(250000);
  strip.begin();
  strip.setBrightness(80);
  strip.show();

  randomSeed(analogRead(0));
  for (int i = 0; i < SPARKLE_COUNT; i += 5) {
    sparkleIndices[i] = random(LED_COUNT);
    sparkleTypes[i]   = random(2);
    sparklePhases[i]  = random(0,6283) / 1000.0;
  }
}

void loop() {

  while (Serial.available()) {
    uint8_t incoming = Serial.read();
    if (incoming == 'B') {
      if (Serial.available()) {
        char digit = Serial.read();
        if (digit >= '0' && digit <= '2') {
          mode = static_cast<Mode>(digit - '0');

          currentlyTalking = false;
          strip.clear();  strip.show();
        }
      }
      continue;
    }
    if (incoming < 32) continue; 
    talkingVal       = incoming;
    currentlyTalking = true;
    lastActivity     = millis();
  }
  if (currentlyTalking && (millis() - lastActivity > listeningTimeout)) {
    currentlyTalking = false;
  }
  if (currentlyTalking) {
    talkingLightEffect();
  } else {
    switch (mode) {
      case MODE_OFF:     strip.clear(); strip.show();        break;
      case MODE_SPARKLE: magicalSparkleEffect();             break;
      case MODE_SCANNER: thinkingScannerEffect();            break;
    }
  }
}

void talkingLightEffect() {
  strip.clear();
  for (int i = 0; i < LED_COUNT; i += 3) {
    strip.setPixelColor(
      i,
      strip.Color(constrain(talkingVal, 25, 75), 255,0,0) //GRBW
    );
  }
  strip.show();
}

void magicalSparkleEffect() {
  strip.clear();
  float angularFrequency = (2 * PI) / 3000.0;
  unsigned long t = millis();

  for (int i = 0; i < SPARKLE_COUNT; i++) {
    float brightnessFactor = (sin(angularFrequency * t + sparklePhases[i]) + 1) / 2.0;

    if (sparkleTypes[i] == 0) {
      int whiteVal = brightnessFactor * 64;
      strip.setPixelColor(sparkleIndices[i], strip.Color(0, 0, 0, whiteVal));
    } else {
      int redVal  = brightnessFactor * 64;
      int blueVal = brightnessFactor * 64;
      strip.setPixelColor(sparkleIndices[i], strip.Color(0, redVal, blueVal, 0));
    }
  }
  strip.show();
}

void thinkingScannerEffect() {
  static int beamPos[7]   = {   0,  90, 180, 270, 360, 450, 540 };
  const int beamWidth = 12;

  unsigned long now = millis();
  if (now - lastScannerUpdate < 13) return;
  lastScannerUpdate = now;

  strip.clear();

  for (int b = 0; b < 7; b++) {

    for (int i = 0; i < beamWidth; i++) {
      int pos = beamPos[b] + i;
      if (pos >= 0 && pos < LED_COUNT) {
        int intensity = map(i, 0, beamWidth, 220, 100);
        strip.setPixelColor(pos, strip.Color(0, intensity, intensity, 0));
      }
    }

    for (int j = 0; j < 4; j++) {
      int twinklePos = beamPos[b] + random(-24, -2);
      if (twinklePos >= 0 && twinklePos < LED_COUNT) {
        int w = random(30, 100);
        strip.setPixelColor(twinklePos, strip.Color(0, 0, 0, w));
      }
    }
    beamPos[b] += 2;
    if (beamPos[b] >= LED_COUNT) beamPos[b] = 0;
  }
  strip.show();
}