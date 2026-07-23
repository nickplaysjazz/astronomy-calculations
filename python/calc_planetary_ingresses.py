import datetime
import re
import sys
import numpy as np
from prettytable import PrettyTable

from calc_planetary_positions import calc_positions

# Macros for trig calcs
cosd = lambda deg: np.cos(np.deg2rad(deg))
sind = lambda deg: np.sin(np.deg2rad(deg))
tand = lambda deg: np.tan(np.deg2rad(deg))
atan2d = lambda y, x: np.mod(np.rad2deg(np.atan2(y, x)), 360)

planets = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]
signs = ["aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"]

class bcolors:
    FAIL = '\033[91m'
    ENDC = '\033[00m'

def parse_cli_args():
    calendar_input = None
    time_input = None
    target_planet = None

    for item in sys.argv[1:]:
        if re.match(r"^\d{4}-\d{2}-\d{2}$", item):
            calendar_input = item
        elif re.match(r"^\d{2}:\d{2}$", item):
            time_input = item
        elif item.lower() in planets:
            target_planet = item.lower()

    if target_planet is None:
        sys.exit(f"{bcolors.FAIL}Error: Please specify a valid target planet: {planets}{bcolors.ENDC}")

    if calendar_input is None:
        dat = datetime.datetime.now(datetime.timezone.utc)
        y, m, day = dat.year, dat.month, dat.day
    else:
        dat = datetime.date.fromisoformat(calendar_input)
        y, m, day = dat.year, dat.month, dat.day

    if time_input is None:
        dat = datetime.datetime.now(datetime.timezone.utc)
        io_h, io_m = dat.hour, dat.minute
    else:
        dat = datetime.time.fromisoformat(time_input)
        io_h, io_m = dat.hour, dat.minute

    return y, m, day, io_h, io_m, target_planet

def get_day_number(dt):
    y, m, day = dt.year, dt.month, dt.day
    UT = dt.hour + dt.minute / 60.0 + dt.second / 3600.0
    d = 367 * y - 7 * (y + (m + 9) // 12) // 4 - 3 * ((y + (m - 9)//7)//100 + 1)//4 + 275 * m // 9 + day - 730515
    return d + UT / 24.0

def day_number_to_datetime(d):
    j2000_epoch = datetime.datetime(2000, 1, 1, 12, 0, tzinfo=datetime.timezone.utc)
    return j2000_epoch + datetime.timedelta(days=d)

def get_ecliptic_longitude(d, target_planet):
    dt = day_number_to_datetime(d)
    planet_idx = planets.index(target_planet)
    ecl_pos = calc_positions(dt.year, dt.month, dt.day, dt.hour + dt.minute/60.0, d, is_equatorial=False, correct_for_precession=False)
    xg, yg, _ = ecl_pos[planet_idx]
    return atan2d(yg, xg)

def get_apparent_speed(d, target_planet, delta_d=1e-4):
    """instantaneous angular velocity dlambda/dt in deg/day centered at d"""
    lon_after = get_ecliptic_longitude(d + delta_d, target_planet)
    lon_before = get_ecliptic_longitude(d - delta_d, target_planet)
    
    diff = (lon_after - lon_before) % 360.0
    if diff > 180.0:
        diff -= 360.0
        
    return diff / (2.0 * delta_d)

def find_ingresses(start_dt, target_planet, days_ahead=365):
    ingresses = []
    
    start_d = get_day_number(start_dt)
    end_d = start_d + days_ahead
    
    # 6-hour sampling intervals 
    step = 0.25 
    d_steps = np.arange(start_d, end_d + step, step)
    
    prev_d = d_steps[0]
    prev_lon = get_ecliptic_longitude(prev_d, target_planet)
    prev_sign_idx = int(prev_lon // 30)

    for curr_d in d_steps[1:]:
        curr_lon = get_ecliptic_longitude(curr_d, target_planet)
        curr_sign_idx = int(curr_lon // 30)

        if curr_sign_idx != prev_sign_idx:
            target_sign_idx = curr_sign_idx
            target_deg = target_sign_idx * 30.0

            def lon_diff(d_val):
                lon = get_ecliptic_longitude(d_val, target_planet)
                diff = (lon - target_deg) % 360.0
                if diff > 180.0:
                    diff -= 360.0
                return diff

            low_d = prev_d
            high_d = curr_d
            
            for _ in range(25):
                mid_d = (low_d + high_d) / 2.0
                f_low = lon_diff(low_d)
                f_mid = lon_diff(mid_d)

                if abs(f_mid) < 1e-6:
                    break

                if (f_low > 0 and f_mid > 0) or (f_low < 0 and f_mid < 0):
                    low_d = mid_d
                else:
                    high_d = mid_d

            crossing_d = (low_d + high_d) / 2.0
            ingress_dt = day_number_to_datetime(crossing_d)
            
            # direction at the moment of ingress
            speed = get_apparent_speed(crossing_d, target_planet)
            motion = "Retrograde" if speed < 0 else "Direct"
            
            # prevent duplicates within a 1-hour window
            if not ingresses or abs((ingress_dt - ingresses[-1][0]).total_seconds()) > 3600:
                ingresses.append((ingress_dt, signs[target_sign_idx], motion))

            prev_sign_idx = curr_sign_idx

        prev_d = curr_d
        prev_lon = curr_lon

    return ingresses

if __name__ == "__main__":
    y, m, day, io_h, io_m, target_planet = parse_cli_args()
    start_dt = datetime.datetime(y, m, day, io_h, io_m, tzinfo=datetime.timezone.utc)

    ingresses = find_ingresses(start_dt, target_planet, days_ahead=365)

    table = PrettyTable()
    table.field_names = ["Date & Time (UTC)", "Planet", "Ingress Sign", "Motion"]
    table.align["Date & Time (UTC)"] = "c"
    table.align["Planet"] = "r"
    table.align["Ingress Sign"] = "l"
    table.align["Motion"] = "l"

    for dt_event, sign, motion in ingresses:
        table.add_row([
            dt_event.strftime("%Y-%m-%d %H:%M"),
            target_planet.capitalize(),
            sign.capitalize(),
            motion,
        ])

    print(f"\nPlanetary ingresses for {target_planet} for 1 year starting from {start_dt.strftime('%Y-%m-%d %H:%M')} UTC")
    print(table)
    print("")