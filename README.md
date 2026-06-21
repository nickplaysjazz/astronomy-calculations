# Astronomy Calculations
Calculations written in Python & the Arduino platform to obtain astronomical positions for a given date.

Currently this code can be used to obtain geocentric planetary positions in Right Ascension and Declination for the classical planets: the Sun, the Moon, Mercury, Venus, Mars, Jupiter, and Saturn. These planetary positions have benn confirmed to be accurate to +/- 1-2 arc-minutes when compared with high-quality ephemerides like the NASA JPL Horizons System. These calculations should be accurate for times not too distant from 2000 CE; from 1900 CE to 2100 CE is certainly acceptable. More in-depth testing of the accuracy of this tool has not been done at this time.  

See [my series of blog posts](https://www.nickplaysjazz.com/posts/astrological-clock-1/) for information on this project and its development.

## Usage
 
### Python
Python scripts are in the directory `python`.

To calculate planetary positions for a given date, run `python calc_planetary_positions.py YYYY-MM-DD HH:MM` with HH:MM in UTC. This calculation will report each planet's Right Ascension (RA) in degrees and the Declination (Dec) in degrees.

To calculate planetary positions in zodiacal terms for a given date, run `python calc_horoscope.py YYYY-MM-DD HH:MM` with HH:MM in UTC. This calculation will report each planet's position in a sign in degrees and minutes.

Inputs are accepted regardless of order, provided they each fit the exact form provided above. If YYYY-MM-DD is not present in exact form, then the current date is assumed. If HH:MM is not present in exact form, then the current time is assumed.

For example, to determine planetary positions at 1:30pm UTC on June 4, 2026 CE, run `python calc_planetary_positions.py 2026-06-04 13:30`. 

### Arduino 
Arduino scripts are in the directory `arduino`. The first provided script is `rtc_oled_test.ino`, a script that can be loaded onto an Arduino Nano connected to an RTC module and OLED display module to test their functionality. This will show the time & date, possibly offset to another time zone by altering the `TIMEZONE_OFFSET_HOURS` variable. 

The second provided script is `astrology_clock.ino`, a script that can be loaded onto an Arduino Nano connected to an RTC module and OLED display module. This will show the local date & time, possibly offset to another time zone by altering the `TIMEZONE_OFFSET_HOURS`, as well as the positions in arc-degrees and arc-minutes of the seven classical planets along the zodiac. These are displayed using traditional astrological symbols. These positions are accurate to about +/- 1 arc-minute.

## Acknowledgments
Astronomical calculations are adapted from algorithms developed by Paul Schlyter. 
For more details, please see his original write-up at https://stjarnhimlen.se/comp/ppcomp.html.

## Contributing
Contributions to this code are welcome. If you have any suggested improvements, please fork the repo and create a pull request. Bug reports and enhancements in the Issues tab are also welcome. 

## License
This project is distributed under the GNU GPL v3 license. See `LICENSE` for more information.

## Contact
You can reach me through the contact information listed on the [About page at my blog](https://www.nickplaysjazz.com/about).
