# Astronomy Calculations
Calculations written in Python to obtain astronomical information for a given date.

Currently this code can be used to obtain planetary positions for the classical planets: the Sun, the Moon, Mercury, Venus, Mars, Jupiter, and Saturn.

See [my series of blog posts](https://www.nickplaysjazz.com/posts/astrological-clock-1.md) for information on this project and its development.

## Usage
To calculate planetary positions for a given date, run `python calc_planetary_positions.py YYYY-MM-DD HH:MM` with HH:MM in UTC. 

This calculator reports the Right Ascension (RA) in degrees and the Declination (Dec) in degrees.

Inputs are accepted regardless of order, provided they each fit the exact form provided above. If YYYY-MM-DD is not present in exact form, then the current date is assumed. If HH:MM is not present in exact form, then the current time is assumed.

For example, to determine planetary positions at 1:30pm UTC on June 4, 2026 CE, run `python calc_planetary_positions.py 2026-06-04 13:30`. 

## Acknowledgments
This code is adapted from algorithms developed by Paul Schlyter. 
For more details, please see his original write-up at https://stjarnhimlen.se/comp/ppcomp.html.

## Contributing
Contributions to this code are welcome. If you have any suggested improvements, please fork the repo and create a pull request. Bug reports and enhancements in the Issues tab are also welcome. 

## License
This project is distributed under the GNU GPL v3 license. See `LICENSE` for more information.

## Contact
You can reach me through the contact information listed on the [About page at my blog](https://www.nickplaysjazz.com/about).
