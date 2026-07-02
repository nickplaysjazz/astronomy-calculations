/*

The following code is adapted from an algorithm developed by Paul Schlyter.
For details, please see his original write-up at https://stjarnhimlen.se/comp/ppcomp.html.

*/

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SH110X.h>
#include <RTClib.h>
#include <avr/pgmspace.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1

/************** GLOBAL SCOPE **************/
Adafruit_SH1106G display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);
RTC_DS3231 rtc;

// change this to display local time in your time zone
const int TIMEZONE_OFFSET_HOURS = -5;

// planet position along the ecliptic
double obsecl[7];

// string buffer needed to print some things
char buffer[24];

// text, glyphs, etc
const char sun[] PROGMEM = "SUN";
const char mon[] PROGMEM = "MON";
const char tue[] PROGMEM = "TUE";
const char wed[] PROGMEM = "WED";
const char thu[] PROGMEM = "THU";
const char fri[] PROGMEM = "FRI";
const char sat[] PROGMEM = "SAT";

const char* const daysOfTheWeek[] PROGMEM = {
  sun,
  mon,
  tue,
  wed,
  thu,
  fri,
  sat
};

const unsigned char sol_img[] PROGMEM = {0x1c, 0x22, 0x2a, 0x22, 0x1c};
const unsigned char luna_img[] PROGMEM = {0x22, 0x5d, 0x41, 0x22, 0x1c};
const unsigned char mercury_img[] PROGMEM = {0x05, 0x2a, 0x7a, 0x2a, 0x05};
const unsigned char venus_img[] PROGMEM = {0x06, 0x29, 0x79, 0x29, 0x06};
const unsigned char mars_img[] PROGMEM = {0x30, 0x48, 0x4d, 0x33, 0x07};
const unsigned char jupiter_img[] PROGMEM = {0x19, 0x16, 0x10, 0x7c, 0x10};
const unsigned char saturn_img[] PROGMEM = {0x02, 0x1f, 0x0a, 0x68, 0x30};

const unsigned char* const planetGlyphs[] PROGMEM = {
  sol_img,
  luna_img,
  mercury_img,
  venus_img,
  mars_img,
  jupiter_img,
  saturn_img
};

const unsigned char aries_img[] PROGMEM = {0x06, 0x09, 0x01, 0x3e, 0x01, 0x09, 0x06};
const unsigned char taurus_img[] PROGMEM = {0x01, 0x3b, 0x46, 0x44, 0x46, 0x3b, 0x01};
const unsigned char gemini_img[] PROGMEM = {0x41, 0x22, 0x3e, 0x22, 0x3e, 0x22, 0x41};
const unsigned char cancer_img[] PROGMEM = {0x17, 0x25, 0x47, 0x41, 0x71, 0x52, 0x74};
const unsigned char leo_img[] PROGMEM = {0x30, 0x48, 0x48, 0x3e, 0x01, 0x3e, 0x40};
const unsigned char virgo_img[] PROGMEM = {0x1f, 0x01, 0x1f, 0x01, 0x5e, 0x24, 0x18};
const unsigned char libra_img[] PROGMEM = {0x50, 0x56, 0x49, 0x41, 0x49, 0x56, 0x50};
const unsigned char scorpio_img[] PROGMEM = {0x1f, 0x01, 0x1f, 0x01, 0x1e, 0x20, 0x10};
const unsigned char sagittarius_img[] PROGMEM = {0x40, 0x28, 0x11, 0x29, 0x05, 0x03, 0x1f};
const unsigned char capricorn_img[] PROGMEM = {0x01, 0x4e, 0x21, 0x1e, 0x28, 0x28, 0x10};
const unsigned char aquarius_img[] PROGMEM = {0x24, 0x12, 0x12, 0x24, 0x12, 0x12, 0x24};
const unsigned char pisces_img[] PROGMEM = {0x41, 0x2a, 0x1c, 0x08, 0x1c, 0x2a, 0x41};

const unsigned char* const zodiacGlyphs[] PROGMEM = {
  aries_img, taurus_img, gemini_img, cancer_img,
  leo_img,   virgo_img,  libra_img,  scorpio_img,
  sagittarius_img, capricorn_img, aquarius_img,  pisces_img
};

// the orbital elements for the seven classical planets, dependent on julian day d
void get_orbital_elements(int it, double d, double &N, double &i, double &w, double &a, double &e, double &M) {
  switch(it) {
    case 0: N = 0.0; i = 0.0; w = 282.9404 + 4.70935e-5 * d; a = 1.000000; e = 0.016709 - 1.151e-9 * d; M = 356.0470 + 0.9856002585 * d; break;
    case 1: N = 125.1228 - 0.0529538083 * d; i = 5.1454; w = 318.0634 + 0.1643573223 * d; a = 60.2666; e = 0.054900; M = 115.3654 + 13.0649929509 * d; break;
    case 2: N = 48.3313 + 3.24587e-5 * d; i = 7.0047 + 5.00e-8 * d; w = 29.1241 + 1.01444e-5 * d; a = 0.387098; e = 0.205635 + 5.59e-10 * d; M = 168.6562 + 4.0923344368 * d; break;
    case 3: N = 76.6799 + 2.46590e-5 * d; i = 3.3946 + 2.75e-8 * d; w = 54.8910 + 1.38374e-5 * d; a = 0.723330; e = 0.006773 - 1.302e-9 * d; M = 48.0052 + 1.6021302244 * d; break;
    case 4: N = 49.5574 + 2.11081e-5 * d; i = 1.8497 - 1.78e-8 * d; w = 286.5016 + 2.92961e-5 * d; a = 1.523688; e = 0.093405 + 2.516e-9 * d; M = 18.6021 + 0.5240207766 * d; break;
    case 5: N = 100.4542 + 2.76854e-5 * d; i = 1.3030 - 1.557e-7 * d; w = 273.8777 + 1.64505e-5 * d; a = 5.20256; e = 0.048498 + 4.469e-9 * d; M = 19.8950 + 0.0830853001 * d; break;
    case 6: N = 113.6634 + 2.38980e-5 * d; i = 2.4886 - 1.081e-7 * d; w = 339.3939 + 2.97661e-5 * d; a = 9.55475; e = 0.055546 - 9.499e-9 * d; M = 316.9670 + 0.0334442282 * d; break;
  }
}

/************** MATHEMATICS **************/
double pi = M_PI;

long intdiv(double a, double b) {
  return (long)(a / b);
}

double cosd(double deg) {
  return cos(deg * DEG_TO_RAD);
}

double sind(double deg) {
  return sin(deg * DEG_TO_RAD);
}

double atan2d(double y, double x) {
  return atan2(y, x) * RAD_TO_DEG;
}

double wrap360(double angle) {
  double result = fmod(angle, 360.0);
  if (result < 0) {
    result += 360.0;
  }
  return result;
}

void print_dec_to_sexa(Adafruit_SH1106G &display, double degrees) {
  degrees = wrap360(degrees);
  int whole_degrees = (int)degrees;

  // add 0.5 for rounding to the nearest whole minute
  int minutes = (int)((degrees - whole_degrees) * 60.0 + 0.5);
  if (minutes >= 60) {
    minutes -= 60;
    whole_degrees += 1;
  }

  int sign_idx = whole_degrees / 30;
  if (sign_idx > 11) sign_idx = 11;
  if (sign_idx < 0)  sign_idx = 0;

  // display only degree in sign, which are 30 degree increments of 360
  whole_degrees = whole_degrees % 30;
  if (whole_degrees < 10) {
    display.print("0");
  }
  display.print(whole_degrees);
  display.print("\xF7"); // Degree symbol in 7-bit ascii

  if (minutes < 10) {
    display.print("0");
  }
  display.print(minutes);
  display.print("'"); 

  int start_x = display.getCursorX();
  int start_y = display.getCursorY();
  
  // this odd work around is so we can read and print a variable image array correctly
  unsigned char* glyphPtr = (unsigned char*)pgm_read_ptr(&(zodiacGlyphs[sign_idx]));
  for (int col = 0; col < 7; col++) {
    unsigned char colData = pgm_read_byte(&glyphPtr[col]);
    for (int row = 0; row < 7; row++) {
      if (colData & (1 << row)) {
        display.drawPixel(start_x + col, start_y + row, SH110X_WHITE);
      }
    }
  }

  display.setCursor(start_x + 8, start_y);
}

/************** SETUP, PLACE NO FUNCTIONS BELOW HERE **************/
void setup() {
  // DS3231 rtc module
  Serial.begin(9600);
  
  Serial.println(F("\n Booting up..."));
  Serial.flush();

  if (! rtc.begin()) {
    Serial.println(F("Error: RTC setup"));
    Serial.flush();
    while (1);
  }

  if (rtc.lostPower()) {
    // sets the RTC to the date & time this sketch was compiled, corrected to UTC
    DateTime localCompileTime = DateTime(F(__DATE__), F(__TIME__));
    uint32_t utcTimestamp = localCompileTime.unixtime() - (TIMEZONE_OFFSET_HOURS * 3600);
    rtc.adjust(DateTime(utcTimestamp));
  }

  // SH1106 oled module
  if (!display.begin(0x3C, true)) {
    Serial.println(F("Error: OLED setup"));
    Serial.flush();
    for(;;);
  }
  
  Wire.setWireTimeout(3000, true);

  display.clearDisplay();
  display.setContrast(10);
  display.setTextSize(1);
  display.setTextColor(SH110X_WHITE);
  display.display();
}


/************** MAIN LOOP **************/
void loop () {
  /************** GET TIME & ORBITAL ELEMENTS **************/
  // utc for astronomical calculations
  DateTime now = rtc.now();
  int y = now.year(); 
  int m = now.month();
  int day = now.day();
  int utc_h = now.hour();
  double utc_m = now.minute();

  // local time, for display alone
  uint32_t local_seconds = now.unixtime() + (TIMEZONE_OFFSET_HOURS * 3600LL);
  DateTime local_now(local_seconds);
  int local_min = local_now.minute();
  int local_h = local_now.hour();
  int local_d = local_now.day();
  int local_m = local_now.month();
  int local_y = local_now.year();
  int weekday = local_now.dayOfTheWeek();

  // julian day number
  // 32-bit precision, accurate to 7 digits; perhaps off by 30 seconds
  double d = 367.0 * y - intdiv(7.0*(y + intdiv(m + 9.0, 12.0)), 4.0);
  d = d - 3.0 * intdiv(intdiv(y + intdiv(m - 9.0, 7.0), 100.0) + 1.0, 4.0);
  d = d + intdiv(275.0 * m, 9.0) + day - 730515.0;
  d = d + (utc_h + (utc_m/60.0)) / 24.0;

  // specific values needed for shared perturbations
  double dummy_N, dummy_i, dummy_w, dummy_a, dummy_e; // throwaways
  double Ns, is, ws, as, es, Ms;
  get_orbital_elements(0, d, Ns, is, ws, as, es, Ms);

  double Nm, im, wm, am, em, Mm;
  get_orbital_elements(1, d, Nm, im, wm, am, em, Mm);

  double Mj;
  get_orbital_elements(5, d, dummy_N, dummy_i, dummy_w, dummy_a, dummy_e, Mj);

  double Msat;
  get_orbital_elements(6, d, dummy_N, dummy_i, dummy_w, dummy_a, dummy_e, Msat);

  Ms = wrap360(Ms);
  Mm = wrap360(Mm);
  Nm = wrap360(Nm);
  ws = wrap360(ws);
  wm = wrap360(wm);
  Mj = wrap360(Mj);
  Msat = wrap360(Msat);

  double Ls = Ms + ws;
  double Lm = Mm + wm + Nm;
  double D = Lm - Ls;
  double F = Lm - Nm;

  /************** CALCULATE POSITIONS **************/
  double xs = 0;
  double ys = 0;

  // calculate sun first, needed for other planets
  {
    int it = 0;
    double N, i, w, a, e, M;
    get_orbital_elements(it, d, N, i, w, a, e, M);
    
    N = wrap360(N);
    i = wrap360(i);
    w = wrap360(w);
    M = wrap360(M);

    double E0 = M + (180.0 / pi) * e * sind(M) * (1.0 + e * cosd(M));
    double tol = 1e-5;
    double E = 0.0;
    for (int numerical_iter = 0; numerical_iter < 1000; numerical_iter++) {
      double E1 = E0 - (E0 - e * (180.0 / pi) * sind(E0) - M) / (1.0 - e * cosd(E0));
      if (fabs(E1 - E0) < tol || isnan(E1)) {
        E = E1;
        break;
      } 
      E0 = E1;
    }

    double ecl = 23.4393 - 3.563e-7 * d;

    double xg = 0;
    double yg = 0;

    double xv = a * (cosd(E) - e);
    double yv = a * (sqrt(1 - e * e) * sind(E));

    double v = atan2d(yv, xv);
    double r = sqrt(pow(xv, 2) + pow(yv, 2));

    double lonsun = wrap360(v + w);
    double rs = r;
    double Ls = M + w;

    xs = r * cosd(lonsun);
    ys = r * sind(lonsun);

    xg = xs;
    yg = ys;

    obsecl[0] = lonsun;
  }

  for (int it = 1; it <= 6; it++) {
    double N, i, w, a, e, M;
    get_orbital_elements(it, d, N, i, w, a, e, M);
    
    N = wrap360(N);
    i = wrap360(i);
    w = wrap360(w);
    M = wrap360(M);

    double E0 = M + (180.0 / pi) * e * sind(M) * (1.0 + e * cosd(M));
    double tol = 1e-5;
    double E = 0.0;
    
    for (int numerical_iter = 0; numerical_iter < 1000; numerical_iter++) {
      double E1 = E0 - (E0 - e * (180.0 / pi) * sind(E0) - M) / (1.0 - e * cosd(E0));
      if (fabs(E1 - E0) < tol || isnan(E1)) {
        E = E1;
        break;
      }
      E0 = E1;
    }

    double xv = a * (cosd(E) - e);
    double yv = a * (sqrt(1.0 - e * e) * sind(E));
    double v = atan2d(yv, xv);
    double r = sqrt(xv * xv + yv * yv);

    double xh = r * (cosd(N) * cosd(v + w) - sind(N) * sind(v + w) * cosd(i));
    double yh = r * (sind(N) * cosd(v + w) + cosd(N) * sind(v + w) * cosd(i));
    double zh = r * (sind(v + w) * sind(i));

    double lonecl = atan2d(yh, xh);
    double latecl = atan2d(zh, sqrt(xh * xh + yh * yh));

    double lon_corr = 0;
    double lat_corr = 0;

    // specific perturbations per planet
    if (it == 1) {
      lon_corr += -1.274 * sind(Mm - 2 * D) + 0.658 * sind(2 * D) - 0.186 * sind(Ms)
                  - 0.059 * sind(2 * Mm - 2 * D) - 0.057 * sind(Mm - 2 * D + Ms)
                  + 0.053 * sind(Mm + 2 * D) + 0.046 * sind(2 * D - Ms)
                  + 0.041 * sind(Mm - Ms) - 0.035 * sind(D) - 0.031 * sind(Mm + Ms)
                  - 0.015 * sind(2 * F - 2 * D) + 0.011 * sind(Mm - 4 * D);

      lat_corr += -0.173 * sind(F - 2 * D) - 0.055 * sind(Mm - F - 2 * D)
                  - 0.046 * sind(Mm + F - 2 * D) + 0.033 * sind(F + 2 * D)
                  + 0.017 * sind(2 * Mm + F);

      r += -0.58 * cosd(Mm - 2 * D) - 0.46 * cosd(2 * D);
    } 
    else if (it == 5) {
      lon_corr += -0.332 * sind(2 * Mj - 5 * Msat - 67.6) - 0.056 * sind(2 * Mj - 2 * Msat + 21)
                  + 0.042 * sind(3 * Mj - 5 * Msat + 21) - 0.036 * sind(Mj - 2 * Msat)
                  + 0.022 * cosd(Mj - Msat) + 0.023 * sind(2 * Mj - 3 * Msat + 52)
                  - 0.016 * sind(Mj - 5 * Msat - 69);
    } 
    else if (it == 6) {
      lon_corr += 0.812 * sind(2 * Mj - 5 * Msat - 67.6) - 0.229 * cosd(2 * Mj - 4 * Msat - 2)
                  + 0.119 * sind(Mj - 2 * Msat - 3) + 0.046 * sind(2 * Mj - 6 * Msat - 69)
                  + 0.014 * sind(Mj - 3 * Msat + 32);

      lat_corr += -0.020 * cosd(2 * Mj - 4 * Msat - 2) + 0.018 * sind(2 * Mj - 6 * Msat - 49);
    }

    lonecl += lon_corr;
    latecl += lat_corr;

    lonecl = wrap360(lonecl);
    latecl = wrap360(latecl);

    double xh_perturbed = r * cosd(lonecl) * cosd(latecl);
    double yh_perturbed = r * sind(lonecl) * cosd(latecl);

    if (it == 1) {
      double xg = xh_perturbed;
      double yg = yh_perturbed;
      obsecl[1] = atan2d(yg, xg);
    } else {
      double xg = xh_perturbed + xs;
      double yg = yh_perturbed + ys;
      obsecl[it] = atan2d(yg, xg);
    }
  }
    
  /************** DISPLAY **************/
  display.clearDisplay();

  int cx = 64;
  int cy = 31;

  // wheel frame
  display.drawCircle(cx, cy, 31, SH110X_WHITE);
  display.drawCircle(cx, cy, 21, SH110X_WHITE);
  display.drawCircle(cx, cy, 1,  SH110X_WHITE);

  // lines on cusp of each sign 
  for (int deg = 0; deg < 360; deg += 30) {
    int display_deg = 180 + deg;
    int x1 = cx + 21 * cosd(display_deg);
    int y1 = cy - 21 * sind(display_deg);
    int x2 = cx + 31 * cosd(display_deg);
    int y2 = cy - 31 * sind(display_deg);
    display.drawLine(x1, y1, x2, y2, SH110X_WHITE);
  }

  // zodiac glyphs
  for (int sign = 0; sign < 12; sign++) {
    double angle = 180.0 + (sign * 30.0 + 15.0); 
    int x = cx + 26 * cosd(angle);
    int y = cy - 26 * sind(angle);

    unsigned char* zGlyphPtr = (unsigned char*)pgm_read_ptr(&(zodiacGlyphs[sign]));
    for (int col = 0; col < 7; col++) {
      unsigned char colData = pgm_read_byte(&zGlyphPtr[col]);
      for (int row = 0; row < 7; row++) {
        if (colData & (1 << row)) {
          display.drawPixel(x - 3 + col, y - 3 + row, SH110X_WHITE);
        }
      }
    }
  }

  for (int it = 0; it < 7; it++) {
    double angle = 180.0 + obsecl[it];
    int x = cx + 14 * cosd(angle);
    int y = cy - 14 * sind(angle);

    // planet glyph centered on point
    unsigned char* pGlyphPtr = (unsigned char*)pgm_read_ptr(&(planetGlyphs[it]));
    for (int col = 0; col < 5; col++) {
      unsigned char colData = pgm_read_byte(&pGlyphPtr[col]);
      for (int row = 0; row < 7; row++) {
        if (colData & (1 << row)) {
          display.drawPixel(x - 2 + col, y - 3 + row, SH110X_WHITE);
        }
      }
    }
  }

  // calendar date on left hand panel
  display.setTextSize(1);
  display.setCursor(0, 12);
  strcpy_P(buffer, (char*)pgm_read_ptr(&(daysOfTheWeek[weekday])));
  display.print(buffer);
  
  display.setCursor(0, 26);
  if (local_m < 10) display.print(F("0"));
  display.print(local_m);
  display.print(F("-"));
  if (local_d < 10) display.print(F("0"));
  display.print(local_d);
  
  display.setCursor(0, 40);
  display.print(local_y);

  // clock time on right hand panel
  display.setCursor(98, 26);
  if (local_h < 10) display.print(F("0"));
  display.print(local_h);
  display.print(F(":"));
  if (local_min < 10) display.print(F("0"));
  display.print((int)local_min);

  // display now
  display.display();

  // update once every 30 seconds, which is roughly limit of our accuracy
  delay(30*1000); 
}