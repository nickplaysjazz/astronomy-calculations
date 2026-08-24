import datetime
import re
import sys
import numpy as np
from prettytable import PrettyTable

from calc_planetary_positions import calc_positions

# Trigonometric helpers
atan2d = lambda y, x: np.mod(np.rad2deg(np.atan2(y, x)), 360)

CARDINAL_EVENTS = {
    "aries": "March Equinox",
    "cancer": "June Solstice",
    "libra": "September Equinox",
    "capricorn": "December Solstice"
}

def parse_cli_args():
    calendar_input = None
    time_input = None

    for item in sys.argv[1:]:
        if re.match(r"^\d{4}-\d{2}-\d{2}$", item):
            calendar_input = item
        elif re.match(r"^\d{2}:\d{2}$", item):
            time_input = item

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

    return y, m, day, io_h, io_m

def get_day_number(dt):
    """Calculates the astronomical day number 'd' from a datetime object."""
    y, m, day = dt.year, dt.month, dt.day
    # Keep the high precision UT calculation for the initial bounds
    UT = dt.hour + dt.minute / 60.0 + dt.second / 3600.0 + dt.microsecond / 3600000000.0
    
    d = (367 * y - 7 * (y + (m + 9) // 12) // 4 - 3 * ((y + (m - 9) // 7) // 100 + 1) // 4 + 275 * m // 9 + day - 730515)
    return d + UT / 24.0

def day_number_to_datetime(d):
    """Epoch d = 0.0 corresponds to 1999-12-31 00:00 UT (2000 Jan 0.0)."""
    epoch = datetime.datetime(1999, 12, 31, 0, 0, tzinfo=datetime.timezone.utc)
    return epoch + datetime.timedelta(days=d)

def get_sun_longitude(d):
    """Fetches the geocentric ecliptic longitude of the Sun for a given day number 'd'."""
    # We pass 0 for y, m, day, and UT since calc_positions ignores them anyway.
    ecl_positions = calc_positions(0, 0, 0, 0, d, is_equatorial=False, correct_for_precession=False)
    
    # Sun is index 0 in the planets list
    xg, yg, zg = ecl_positions[0]
    return np.mod(np.rad2deg(np.atan2(yg, xg)), 360)

def find_seasons(start_dt, days_ahead=365):
    seasons = []
    start_d = get_day_number(start_dt)
    end_d = start_d + days_ahead
    
    # Step through time in 6-hour increments
    d_steps = np.arange(start_d, end_d + 0.25, 0.25)
    
    prev_d = d_steps[0]
    prev_lon = get_sun_longitude(prev_d)
    prev_sign_idx = int(prev_lon // 30)

    for curr_d in d_steps[1:]:
        curr_lon = get_sun_longitude(curr_d)
        curr_sign_idx = int(curr_lon // 30)

        if curr_sign_idx != prev_sign_idx:
            target_sign_idx = curr_sign_idx
            target_sign_name = [
                "aries", "taurus", "gemini", "cancer", "leo", "virgo", 
                "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"
            ][target_sign_idx]

            if target_sign_name in CARDINAL_EVENTS:
                target_deg = target_sign_idx * 30.0

                def lon_diff(d_val):
                    lon = get_sun_longitude(d_val)
                    diff = (lon - target_deg) % 360.0
                    return diff - 360.0 if diff > 180.0 else diff

                low_d, high_d = prev_d, curr_d
                for _ in range(25):
                    mid_d = (low_d + high_d) / 2.0
                    if abs(lon_diff(mid_d)) < 1e-6:
                        break
                    if (lon_diff(low_d) > 0) == (lon_diff(mid_d) > 0):
                        low_d = mid_d
                    else:
                        high_d = mid_d

                crossing_dt = day_number_to_datetime((low_d + high_d) / 2.0)
                seasons.append((crossing_dt, CARDINAL_EVENTS[target_sign_name], target_sign_name.capitalize()))

            prev_sign_idx = curr_sign_idx

        prev_d = curr_d
        prev_lon = curr_lon

    return seasons

if __name__ == "__main__":
    y, m, day, io_h, io_m = parse_cli_args()
    start_dt = datetime.datetime(y, m, day, io_h, io_m, tzinfo=datetime.timezone.utc)

    seasons = find_seasons(start_dt, days_ahead=365)

    table = PrettyTable()
    table.field_names = ["Date & Time (UTC)", "Event", "Sun Ingress"]
    table.align["Date & Time (UTC)"] = "l"
    table.align["Event"] = "l"
    table.align["Sun Ingress"] = "l"

    for dt_event, event_name, sign in seasons:
        table.add_row([
            dt_event.strftime("%Y-%m-%d %H:%M"),
            event_name,
            f"00°00' {sign}"
        ])

    print(f"\nEquinoxes & solstices occurring 1 year from {start_dt.strftime('%Y-%m-%d %H:%M')} UTC")
    print(table)
    print("")