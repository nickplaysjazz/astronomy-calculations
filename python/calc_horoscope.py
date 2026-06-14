"""

The following code is adapted from an algorithm developed by Paul Schlyter.
For details, please see his original write-up at https://stjarnhimlen.se/comp/ppcomp.html.

"""

import datetime
import numpy as np
import re
import sys

from prettytable import PrettyTable

from calc_planetary_positions import io, calc_positions

# some macros to simplify trig calcs
cosd = lambda deg : np.cos(np.deg2rad(deg))
sind = lambda deg : np.sin(np.deg2rad(deg))
tand = lambda deg : np.tan(np.deg2rad(deg))
atan2d = lambda y, x :  np.mod(np.rad2deg(np.atan2(y, x)), 360)

pi = np.pi

degree_sign = u'\N{DEGREE SIGN}'

planets = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]
signs = ["aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"]


class bcolors:
    FAIL = '\033[91m'
    ENDC = '\033[00m'


if __name__ == "__main__":
    y, m, day, io_h, io_m = io()
    UT = io_h + (io_m/60)

    d = 367 * y - 7 * (y + (m + 9) // 12) // 4 - 3 * ((y + (m - 9)//7)//100 + 1)//4 + 275 * m // 9 + day - 730515
    d = d + UT / 24
    
    # planetary positions
    ecl_positions = calc_positions(y, m, day, UT, d, is_equatorial=False, correct_for_precession=False)

    table = PrettyTable()
    table.field_names = [
        "Planet",
        f"Sign",
        f"Position",
    ]
    table.align["Planet"] = "r"
    table.align[f"Sign"] = "r"
    table.align[f"Position"] = "r"

    for planet_number, planet_name in enumerate(planets):
        xg, yg, zg = ecl_positions[planet_number]

        # astrology uses ecliptic geocentric coordinates
        obsecl = atan2d(yg, xg)
        hr = int(obsecl // 15)

        degree_in_sign = int(np.mod(obsecl, 30))
        min_in_sign = int(60*(obsecl - int(obsecl)))

        table.add_row(
            [
                planet_name,
                signs[hr//2],
                f"{degree_in_sign:02}{degree_sign} {min_in_sign:02}\'"
            ]
        )

    print("")
    print(f"Horoscope for: {y:04}-{m:02}-{day:02} {io_h:02}:{io_m:02} UTC")
    # print(f"Day number: {d} (relative to Jan 1 2000.0 at 0h UT)")
    print(table)
    print("")