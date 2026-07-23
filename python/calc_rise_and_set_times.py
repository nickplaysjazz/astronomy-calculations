"""

The following code is adapted from an algorithm developed by Paul Schlyter.
For details, please see his original write-up at https://stjarnhimlen.se/comp/riset.html.

"""
import numpy as np
from prettytable import PrettyTable

from calc_four_angles import io_with_location, get_gmst
from calc_planetary_positions import calc_positions

cosd = lambda deg: np.cos(np.deg2rad(deg))
sind = lambda deg: np.sin(np.deg2rad(deg))
tand = lambda deg: np.tan(np.deg2rad(deg))
atan2d = lambda y, x: np.mod(np.rad2deg(np.atan2(y, x)), 360)

pi = np.pi

degree_sign = u'\N{DEGREE SIGN}'

planets = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]


class bcolors:
    FAIL = '\033[91m'
    ENDC = '\033[00m'


def get_altitude(UT, target_planet, y, m, day, longitude, latitude, d0):
    planet_idx = planets.index(target_planet)
    d_ut = d0 + UT / 24.0
    
    eq_pos = calc_positions(y, m, day, UT, d_ut, is_equatorial=True)
    xe, ye, ze = eq_pos[planet_idx]
    
    RA = atan2d(ye, xe)
    Dec = np.rad2deg(np.atan2(ze, np.sqrt(xe**2 + ye**2)))
    
    gmst = get_gmst(d_ut)
    lst = (gmst + longitude) % 360.0
    
    HA = (lst - RA) % 360.0
    
    sin_alt = sind(latitude) * sind(Dec) + cosd(latitude) * cosd(Dec) * cosd(HA)
    alt = np.rad2deg(np.arcsin(np.clip(sin_alt, -1.0, 1.0)))
    return alt

def calc_rise_set_events(target_planet, y, m, day, longitude, latitude):
    d0 = 367 * y - 7 * (y + (m + 9) // 12) // 4 - 3 * ((y + (m - 9)//7)//100 + 1)//4 + 275 * m // 9 + day - 730515

    # International convention for solar rise/set is -0.833, when sun upper limb touching horizon, atmospheric refraction accounted for
    # Otherwise we use -0.583, where the planet's center touches the horizon, atmospheric refraction accounted for
    h0 = -0.833 if target_planet == "sun" else -0.583

    # scan +/- 1 hour in the day just in case our root-finding needs to get a root very close to the edge of the day
    hours = np.arange(0, 26, 1)
    alts = [get_altitude(h, target_planet, y, m, day, longitude, latitude, d0) - h0 for h in hours]
    
    events = []
    
    for i in range(24):
        y1, y2 = alts[i], alts[i+1]
        
        if y1 * y2 <= 0 and y1 != y2:
            ut_cross = hours[i] - y1 / (y2 - y1)
            
            h_a, h_b = hours[i], hours[i+1]
            f_a, f_b = y1, y2
            for _ in range(4):
                if abs(f_b - f_a) < 1e-8:
                    break
                ut_cross = h_b - f_b * (h_b - h_a) / (f_b - f_a)
                f_cross = get_altitude(ut_cross, target_planet, y, m, day, longitude, latitude, d0) - h0
                h_a, f_a = h_b, f_b
                h_b, f_b = ut_cross, f_cross
            
            if 0.0 <= ut_cross < 24.0:
                event_type = "Rises" if y1 < y2 else "Sets"
                events.append((ut_cross, event_type))

    events.sort(key=lambda x: x[0])
    
    if not events:
        if alts[0] > 0:
            return "Always above horizon; no setting"
        else:
            return "Always below horizon; no rising"
            
    return events

def format_time(ut_hours):
    h = int(ut_hours)
    m = int(round((ut_hours - h) * 60))
    if m == 60:
        h = (h + 1) % 24
        m = 0
    return f"{h:02d}:{m:02d}"

def format_events(events):
    if isinstance(events, str):
        return events
    
    formatted = [f"{event_type} {format_time(ut)}" for ut, event_type in events]
    return " - ".join(formatted)

if __name__ == "__main__":
    y, m, day, io_h, io_m, longitude, latitude = io_with_location()
    
    table = PrettyTable()
    table.field_names = [
        "Planet",
        "Events (UTC)"
    ]
    table.align["Planet"] = "l"
    table.align["Events (in UTC)"] = "l"
    
    for planet_name in planets:
        events = calc_rise_set_events(planet_name, y, m, day, longitude, latitude)
        table.add_row(
            [
                planet_name,
                format_events(events)
            ]
        )
    
    print(f"\nRise & set times occurring on {y:04d}-{m:02d}-{day:02d} at {longitude}E, {latitude}N in UTC")
    print(table)
    print("")