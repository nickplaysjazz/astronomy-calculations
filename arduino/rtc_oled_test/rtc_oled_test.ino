#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SH110X.h>
#include <RTClib.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1

Adafruit_SH1106G display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);
RTC_DS3231 rtc;

const int TIMEZONE_OFFSET_HOURS = 0;

const char* daysOfTheWeek[7] = {
  "SUN",
  "MON",
  "TUE",
  "WED",
  "THU",
  "FRI",
  "SAT"
};

void setup() {
  // DS3231 rtc module
  Serial.begin(9600);

  if (! rtc.begin()) {
    Serial.println("Couldn't find RTC");
    Serial.flush();
    while (1);
  }

  if (rtc.lostPower()) {
    // sets the RTC to the date & time this sketch was compiled
    // you should run this once outside the "if" block when you replace the battery
    DateTime localCompileTime = DateTime(F(__DATE__), F(__TIME__));
    uint32_t utcTimestamp = localCompileTime.unixtime() - (TIMEZONE_OFFSET_HOURS * 3600);
    rtc.adjust(DateTime(utcTimestamp));
  }

  // SH1106 oled module
  display.begin(0x3C, true);
  display.clearDisplay();
  display.setTextSize(2);
  display.setTextColor(SH110X_WHITE);
}

void loop () {
  DateTime now = rtc.now();

  display.clearDisplay();
  display.setTextSize(1);
  display.setCursor(0, 0);
  display.print(daysOfTheWeek[now.dayOfTheWeek()]);
  display.print(" ");
  display.print(now.year());
  display.print("-");
  if (now.month() < 10) display.print("0");
  display.print(now.month());
  display.print("-");
  if (now.day() < 10) display.print("0");
  display.print(now.day());
  display.print(" ");
  if (now.hour() < 10) display.print("0");
  display.print(now.hour());
  display.print(":");
  if (now.minute() < 10) display.print("0");
  display.print(now.minute());
  //display.print(":");
  //if (now.second() < 10) display.print("0");
  //display.print(now.second());
  
  display.display();

  // update once every 30 seconds
  delay(30*1000); 
}