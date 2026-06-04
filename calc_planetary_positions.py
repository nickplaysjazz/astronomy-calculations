"""

The following code is adapted from an algorithm developed by Paul Schlyter.
For details, please see his original write-up at https://stjarnhimlen.se/comp/ppcomp.html.

"""

import datetime
import numpy as np
import re
import sys

from prettytable import PrettyTable

from orbital_elements import OrbitalElements


class bcolors:
    FAIL = '\033[91m'
    ENDC = '\033[00m'


def io():

    calendar_input = None
    time_input = None

    inputs = sys.argv[1:] 

    for item in inputs:
        if re.match(r"\d{4}-\d{2}-\d{2}", item):
            calendar_input = item
        elif re.match(r"\d{2}:\d{2}", item):
            time_input = item
        else:
            sys.exit(f"{bcolors.FAIL}Usage: \"python calc_planetary_positions.py YYYY-MM-DD HH:MM latDegN lonDegE \" with HH:MM in UTC." \
                 f"\n\nInputs are accepted regardless of order, provided they each fit the exact form provided above."
                 f"\nIf YYYY-MM-DD HH:MM are not present in exact form, then the current date and time is assumed.")
            
    if (calendar_input == None):
        dat = datetime.datetime.now(datetime.timezone.utc)
        year = dat.year
        month = dat.month
        day = dat.day
    else:
        try:
            dat = datetime.date.fromisoformat(calendar_input)
            year = dat.year
            month = dat.month
            day = dat.day
        except ValueError as err:
            print(f"{bcolors.FAIL}{err}{bcolors.ENDC}")

    if (time_input == None):
        dat = datetime.datetime.now(datetime.timezone.utc)
        hour = dat.hour
        minute = dat.minute
    else:
        try:
            dat = datetime.time.fromisoformat(time_input)
            hour = dat.hour
            minute = dat.minute
        except ValueError as err:
            print(f"{bcolors.FAIL}{err}{bcolors.ENDC}")

    return year, month, day, hour, minute


def main():

    cosd = lambda deg : np.cos(np.deg2rad(deg))
    sind = lambda deg : np.sin(np.deg2rad(deg))
    tand = lambda deg : np.tan(np.deg2rad(deg))
    atan2d = lambda y, x :  np.mod(np.rad2deg(np.atan2(y, x)), 360)

    degree_sign = u'\N{DEGREE SIGN}'

    y, m, day, io_h, io_m = io()
    UT = io_h + (io_m/60)

    pi = np.pi

    # day number and fraction
    d = 367 * y - 7 * (y + (m + 9) // 12) // 4 - 3 * ((y + (m - 9)//7)//100 + 1)//4 + 275 * m // 9 + day - 730515
    d = d + UT / 24

    planets = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]

    table = PrettyTable()
    table.field_names = [
        "Planet",
        f"RA ({degree_sign})",
        f"Dec ({degree_sign})",
    ]
    table.align["Planet"] = "r"
    table.align[f"RA ({degree_sign})"] = "r"
    table.align[f"Dec ({degree_sign})"] = "r"

    data_list = []

    planetary_distances = []

    # terms that will be overriden as they are calculated and used in later calculations
    lonsun = None
    rs = None
    # ecliptic rectangular geocentric coordinates for sun
    xs = None
    ys = None

    true_anomaly_list = [0 for x in range(7)]
    equatorial_positions = [np.array([0,0,0]) for x in range(7)]

    # Orbital elements to be used later
    elements = OrbitalElements(d)

    # wrap degrees to 360 if needed
    N_list = np.mod(elements.N_list, 360)
    i_list = np.mod(elements.i_list, 360)
    w_list = np.mod(elements.w_list, 360)
    a_list = elements.a_list
    e_list = elements.e_list
    M_list = np.mod(elements.M_list, 360)

    # some specific values are needed to calculate perturbations 
    Ms = M_list[0]
    Mm = M_list[1]
    Nm = N_list[1]
    ws = w_list[0]
    wm = w_list[1]
    Ls = Ms + ws
    Lm = Mm + wm + Nm
    D = Lm - Ls
    F = Lm - Nm
    Mj = M_list[5]
    Ms = M_list[6]

    for planet_num, planet_name in enumerate(planets):
        # longitude of ascending node
        N = N_list[planet_num]

        # inclination to the ecliptic, the plane of earth's orbit
        i = i_list[planet_num]

        # argument of perihelion
        w = w_list[planet_num]

        # mean distance to sun, the semi-major axis
        a = a_list[planet_num]

        # eccentricity
        e = e_list[planet_num]

        # mean anomaly
        M = M_list[planet_num]

        # eccentric anomaly
        # must be solved iteratively, here to a specific tolerance
        E0 = M + (180 / pi) * e * sind(M) * (1 + e * cosd(M))
        numerical_iter = 0
        tol = 1e-5
        while True:
            numerical_iter += 1
            E1 = E0 - (E0 - e * (180 / pi) * sind(E0) - M) / (1 - e * cosd(E0))
            if abs(E1 - E0) < tol:
                E = E1
                break
            elif numerical_iter > 10000:
                sys.exit(f"{bcolors.FAIL}" \
                    f"ERROR !! Numerical tolerance of {tol} for eccentric anomaly has not been met within 10,000 iterations for {planet_name}. Halting program!" \
                    f"{bcolors.ENDC}"
                )
            else:
                E0 = E1

        # obliquity of the ecliptic
        ecl = 23.4393 - 3.563e-7 * d

        xg = 0
        yg = 0

        # used in calculating v, r
        xv = a * (cosd(E) - e)
        yv = a * (np.sqrt(1 - e**2) * sind(E))

        # true anomaly
        v = atan2d(yv, xv)
        true_anomaly_list[planet_num] = np.mod(v,360)

        # distance
        r = np.sqrt(xv**2 + yv**2)

        if planet_name == "sun":
            # true longitude
            lonsun = np.mod(v + w, 360)
            rs = r
            Ls = M + w

            # heliocentric distance of sun is trivially 0
            planetary_distances.append(0)

            # ecliptic rectangular geocentric coordinates for sun
            xs = r * cosd(lonsun)
            ys = r * sind(lonsun)

            xg = xs
            yg = ys

            # equatorial rectangular geocentric coordinates for sun
            xe = xs
            ye = ys * cosd(ecl)
            ze = ys * sind(ecl)

            equatorial_positions[0] = np.array([xe, ye, ze])

        else:
            # heliocentric ecliptic coordinates (or geocentric for Moon)
            xh = r * (cosd(N) * cosd(v + w) - sind(N) * sind(v + w) * cosd(i))
            yh = r * (sind(N) * cosd(v + w) + cosd(N) * sind(v + w) * cosd(i))
            zh = r * (sind(v + w) * sind(i))

            # heliocentric longitude
            lonecl = atan2d(yh, xh)
            latecl = atan2d(zh, np.sqrt(xh**2 + yh**2))

            # We do NOT correct for precession here
            # which would be necesary if we are plotting positions against a map of the stars

            if planet_name == "moon":
                lonecl += (
                    -1.274 * sind(Mm - 2 * D)
                    + 0.658 * sind(2 * D)
                    - 0.186 * sind(Ms)
                    - 0.059 * sind(2 * Mm - 2 * D)
                    - 0.057 * sind(Mm - 2 * D + Ms)
                    + 0.053 * sind(Mm + 2 * D)
                    + 0.046 * sind(2 * D - Ms)
                    + 0.041 * sind(Mm - Ms)
                    - 0.035 * sind(D)
                    - 0.031 * sind(Mm + Ms)
                    - 0.015 * sind(2 * F - 2 * D)
                    + 0.011 * sind(Mm - 4 * D)
                )

                latecl += (
                    -0.173 * sind(F - 2 * D)
                    - 0.055 * sind(Mm - F - 2 * D)
                    - 0.046 * sind(Mm + F - 2 * D)
                    + 0.033 * sind(F + 2 * D)
                    + 0.017 * sind(2 * Mm + F)
                )

                r += -0.58 * cosd(Mm - 2 * D) - 0.46 * cosd(2 * D)
            elif planet_name == "jupiter":
                lonecl += (
                    -0.332 * sind(2 * Mj - 5 * Ms - 67.6)
                    - 0.056 * sind(2 * Mj - 2 * Ms + 21)
                    + 0.042 * sind(3 * Mj - 5 * Ms + 21)
                    - 0.036 * sind(Mj - 2 * Ms)
                    + 0.022 * cosd(Mj - Ms)
                    + 0.023 * sind(2 * Mj - 3 * Ms + 52)
                    - 0.016 * sind(Mj - 5 * Ms - 69)
                )

            elif planet_name == "saturn":
                lonecl += (
                    +0.812 * sind(2 * Mj - 5 * Ms - 67.6)
                    - 0.229 * cosd(2 * Mj - 4 * Ms - 2)
                    + 0.119 * sind(Mj - 2 * Ms - 3)
                    + 0.046 * sind(2 * Mj - 6 * Ms - 69)
                    + 0.014 * sind(Mj - 3 * Ms + 32)
                )
                latecl += -0.020 * cosd(2 * Mj - 4 * Ms - 2) + 0.018 * sind(
                    2 * Mj - 6 * Ms - 49
                )

            lonecl = np.mod(lonecl, 360)
            latecl = np.mod(latecl, 360)

            # perturbed heliocentric ecliptic coordinates (or geocentric for Moon)
            xh_perturbed = r * cosd(lonecl) * cosd(latecl)
            yh_perturbed = r * sind(lonecl) * cosd(latecl)
            zh_perturbed = r * sind(latecl)

            # perturbed heliocentric distance (geocentric for Moon)
            rhelio = np.sqrt(xh_perturbed**2 + yh_perturbed**2 + zh_perturbed**2)
            planetary_distances.append(rhelio)

            # geocentric ecliptic coordinates
            if planet_name == "moon":
                xg = xh_perturbed
                yg = yh_perturbed
                zg = zh_perturbed
            else:
                xg = xh_perturbed + xs
                yg = yh_perturbed + ys
                zg = zh_perturbed

            # equatorial geocentric coordinates
            xe = xg
            ye = yg * cosd(ecl) - zg * sind(ecl)
            ze = yg * sind(ecl) + zg * cosd(ecl)

            equatorial_positions[planet_num] = np.array([xe, ye, ze])

            # geocentric distance
            rg = np.sqrt(xg**2 + yg**2 + zg**2)

        # right ascension
        RA = atan2d(ye, xe)

        # declination. Do NOT wrap this to [0, 360)
        Dec = np.rad2deg(np.atan2(ze, np.sqrt(xe**2 + ye**2)))

        data_list.append(
            [
                planet_name,
                "{:0.4f}".format(round(RA, 4)),
                "{:00.4f}".format(round(Dec, 4)),
            ]
        )

    for x in data_list: 
        table.add_row(x)    

    print("")
    print(f"Calculations for: {y}-{m}-{day} {io_h}:{io_m} UTC")
    #print(f"Day number: {d} (relative to Jan 1 2000.0 at 0h UT)")
    print(table)
    print("")


if __name__ == "__main__":
    main()