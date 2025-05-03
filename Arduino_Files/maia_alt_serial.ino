#include <Adafruit_NeoPixel.h>
#include <math.h>

#define LED_PIN       5 // 5 is D2 FOR THE ESP32
#define LED_COUNT     600
#define SPARKLE_COUNT 300
#define TALK_COUNT 130 

Adafruit_NeoPixel strip(LED_COUNT, LED_PIN, NEO_RGBW + NEO_KHZ800);


int sparkleIndices[SPARKLE_COUNT];
int sparkleTypes[SPARKLE_COUNT];
float sparklePhases[SPARKLE_COUNT];

unsigned long lastDataTime = 0;
const unsigned long listeningTimeout = 1000; 

void setup() {
  Serial.begin(250000);
  strip.begin();
  strip.setBrightness(80); 
  strip.show();

  randomSeed(analogRead(0));
  for (int i = 0; i < SPARKLE_COUNT; i+= 5) {
    sparkleIndices[i] = random(LED_COUNT);     
    sparkleTypes[i] = random(2);            
    sparklePhases[i] = random(0, 6283) / 1000.0;
  }
}

void loop() {
  if (Serial.available() > 0) {
    
    int talkingVal = Serial.read();
    lastDataTime = millis(); 

    for (int i = 0; i < LED_COUNT; i += 3) { 
      strip.setPixelColor(i, strip.Color(constrain(talkingVal,25,52), 255, 0, 0));// (G, R, B, W) !!!!!!!!
    }
    strip.show();
  }
  
  // MAIA listen mode
  if (millis() - lastDataTime > listeningTimeout) {
    magicalSparkleEffect();
  }
}

void magicalSparkleEffect() {
  strip.clear();
  float angularFrequency = (2 * PI) / 3000.0;
  unsigned long currentTime = millis();

  for (int i = 0; i < SPARKLE_COUNT; i++) {
    float brightnessFactor = (sin(angularFrequency * currentTime + sparklePhases[i]) + 1) / 2.0; 

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