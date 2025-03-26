#include <Adafruit_NeoPixel.h>

#define LED_PIN    6
#define LED_COUNT  160

Adafruit_NeoPixel strip(LED_COUNT, LED_PIN, NEO_RGBW + NEO_KHZ800);

void setup() {
  Serial.begin(250000);
  strip.begin();
  strip.show(); 
}

void loop() {
  if (Serial.available() > 0) {
    int brightnessVal = Serial.read();
    for (int i = 0; i < LED_COUNT; i++) {
      // RGBW !!! change if needed
      strip.setPixelColor(i, strip.Color(255, brightnessVal, 0, 0)); //gold
    }
    strip.show();
  }
}