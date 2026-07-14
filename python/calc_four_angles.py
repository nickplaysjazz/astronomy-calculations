import datetime
import numpy as np
import re
import sys

from orbital_elements import OrbitalElements
from calc_planetary_positions import calc_positions

# some macros to simplify trig calcs
cosd = lambda deg : np.cos(np.deg2rad(deg))
sind = lambda deg : np.sin(np.deg2rad(deg))
tand = lambda deg : np.tan(np.deg2rad(deg))
atan2d = lambda y, x :  np.mod(np.rad2deg(np.atan2(y, x)), 360)

pi = np.pi

degree_sign = u'\N{DEGREE SIGN}'

signs = ["aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"]


class bcolors:
    FAIL = '\033[91m'
    ENDC = '\033[00m'

def io_with_location():

    calendar_input = None
    time_input = None
    longitude_input = None
    latitude_input = None

    inputs = sys.argv[1:] 

    for item in inputs:
        if re.match(r"\d{4}-\d{2}-\d{2}", item):
            calendar_input = item
        elif re.match(r"\d{2}:\d{2}", item):
            time_input = item
        elif re.match(r"-?\d+(\.\d+)?[nsNS]", item, re.IGNORECASE):
            latitude_input = item
        elif re.match(r"-?\d+(\.\d+)?[ewEW]", item, re.IGNORECASE):
            longitude_input = item
        else:
            sys.exit(f"{bcolors.FAIL}Usage: \"python calc_four_angles.py YYYY-MM-DD HH:MM latDegN lonDegE \" with HH:MM in UTC." \
                 f"\n\nInputs are accepted regardless of order, provided they each fit the exact form provided above." \
                 f"\nIf YYYY-MM-DD is not present in exact form, then the current date is assumed." \
                 f"\nIf HH:MM is not present in exact form, then the current time is assumed." \
                 f"\n\nIf latDegN, lonDegE are not present in exact form with appended N/S & E/W respectively, then Washington, D.C. (39, -77) is assumed. (Negative longitudes are west of prime meridian.)")
            
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

    if (longitude_input == None): 
        longitude = -77 
    else: 
        try: 
            lon_num = longitude_input.rstrip('EW')
            val = np.float64(lon_num)

            if longitude_input.upper().endswith('W'):
                longitude = -abs(val)
            else: 
                longitude = abs(val)
            
        except ValueError as err:
            print(f"{bcolors.FAIL}{err}{bcolors.ENDC}")
    
    if (latitude_input == None): 
        latitude = 39 
    else: 
        try:
            lat_num = latitude_input.rstrip('NS')
            val = np.float64(lat_num)

            if latitude_input.upper().endswith('S'):
                latitude = -abs(val)
            else:
                latitude = abs(val)

        except ValueError as err: 
            print(f"{bcolors.FAIL}{err}{bcolors.ENDC}")
    
    return year, month, day, hour, minute, longitude, latitude 

def ecliptic_to_equatorial(lon, lat, d):
    """Converts ecliptic coordinates (lat, lon) to equatorial (RA, decl)."""
    ecl = 23.4393 - 3.563e-7 * d
    sin_dec = sind(lat) * cosd(ecl) + cosd(lat) * sind(ecl) * sind(lon)
    dec = np.rad2deg(np.arcsin(sin_dec))
    y = sind(lon) * cosd(ecl) - tand(lat) * sind(ecl)
    x = cosd(lon)
    ra = atan2d(y, x)
    return ra, dec


def get_gmst(d_utc):
    """Calculates Greenwich Mean Sidereal Time (in degrees)."""
    D = d_utc - 1.5
    gmst = 280.46061837 + 360.98564736629 * D
    return gmst % 360


if __name__ == "__main__":
    correct_for_precession = False
    # for tropical, Western ascendant, we don't correct for precession
    # for sidereal ascendant or for determining which constellation is rising, correct for precession
    epoch = 2000

    y, m, day, io_h, io_m, longitude, latitude = io_with_location()
    UT = io_h + (io_m/60)

    # day number and fraction
    d = 367 * y - 7 * (y + (m + 9) // 12) // 4 - 3 * ((y + (m - 9)//7)//100 + 1)//4 + 275 * m // 9 + day - 730515
    d = d + UT / 24
    
    gmst = get_gmst(d)
    lst = (gmst + longitude) % 360.0

    # obliquity of ecliptic
    ecl = 23.4393 - 3.563e-7 * d

    # ecliptic longitude of the Aacendant
    y_comp = cosd(lst)
    x_comp = -(sind(lst) * cosd(ecl) + tand(latitude) * sind(ecl))
    ascendant_deg = atan2d(y_comp, x_comp)

    # ecliptic longitude of MC/midheaven
    y_comp_mc = sind(lst)
    x_comp_mc = cosd(lst) * cosd(ecl)
    mc_deg = atan2d(y_comp_mc, x_comp_mc)
    
    # descendant
    descendant_deg = (ascendant_deg + 180.0) % 360.0

    # IC/ bottom of sky
    ic_deg = (mc_deg + 180.0) % 360.0

    def format_angle(deg, title):
        idx = int(deg // 30)
        deg_in_sign = deg % 30
        min_in_sign = int(60 * (deg_in_sign - int(deg_in_sign)))
        return f"\t{title:4}: {int(deg_in_sign):02d}{degree_sign} {min_in_sign:02d}\' in {signs[idx]}"

    print("")
    print(f"Four angles calculated for: {y:04}-{m:02}-{day:02} {io_h:02}:{io_m:02} UTC, at {longitude}E, {latitude}N")
    print(format_angle(ascendant_deg, "ASC"))
    print(format_angle(ic_deg, "IC"))
    print(format_angle(descendant_deg, "DSC"))
    print(format_angle(mc_deg, "MC"))
    #print(f"Day number: {d} (relative to Jan 1 2000.0 at 0h UT)")
    print("")