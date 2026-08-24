import datetime
import re
import sys
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import numpy as np
from timezonefinder import TimezoneFinder


class bcolors:
    FAIL = "\033[91m"
    ENDC = "\033[00m"


# Common timezone abbreviation map to fixed offsets
TZ_ABBR_MAP = {
    "UTC": datetime.timezone.utc,
    "GMT": datetime.timezone.utc,
    "EST": datetime.timezone(datetime.timedelta(hours=-5), name="EST"),
    "EDT": datetime.timezone(datetime.timedelta(hours=-4), name="EDT"),
    "CST": datetime.timezone(datetime.timedelta(hours=-6), name="CST"),
    "CDT": datetime.timezone(datetime.timedelta(hours=-5), name="CDT"),
    "MST": datetime.timezone(datetime.timedelta(hours=-7), name="MST"),
    "MDT": datetime.timezone(datetime.timedelta(hours=-6), name="MDT"),
    "PST": datetime.timezone(datetime.timedelta(hours=-8), name="PST"),
    "PDT": datetime.timezone(datetime.timedelta(hours=-7), name="PDT"),
    "AKST": datetime.timezone(datetime.timedelta(hours=-9), name="AKST"),
    "AKDT": datetime.timezone(datetime.timedelta(hours=-8), name="AKDT"),
    "HST": datetime.timezone(datetime.timedelta(hours=-10), name="HST"),
    "BST": datetime.timezone(datetime.timedelta(hours=1), name="BST"),
    "CET": datetime.timezone(datetime.timedelta(hours=1), name="CET"),
    "CEST": datetime.timezone(datetime.timedelta(hours=2), name="CEST"),
    "EET": datetime.timezone(datetime.timedelta(hours=2), name="EET"),
    "EEST": datetime.timezone(datetime.timedelta(hours=3), name="EEST"),
    "JST": datetime.timezone(datetime.timedelta(hours=9), name="JST"),
    "AEST": datetime.timezone(datetime.timedelta(hours=10), name="AEST"),
    "AEDT": datetime.timezone(datetime.timedelta(hours=11), name="AEDT"),
}


def parse_explicit_timezone(tz_str: str):
    """Parses abbreviation (EDT, EST), fixed offset (UTC-5, GMT+2, -05:00), or IANA string (America/New_York)."""
    if not tz_str:
        return None

    clean_str = tz_str.strip()
    upper_str = clean_str.upper()

    # 1. Check abbreviation map
    if upper_str in TZ_ABBR_MAP:
        return TZ_ABBR_MAP[upper_str]

    # 2. Check IANA timezone database (e.g. America/New_York, Europe/London)
    try:
        return ZoneInfo(clean_str)
    except (ZoneInfoNotFoundError, ValueError):
        pass

    # 3. Check fixed UTC/GMT offsets (e.g., UTC-5, GMT+3:30, -05:00, +2)
    match = re.match(r"^(?:UTC|GMT)?([+-]\d{1,2})(?::?(\d{2}))?$", upper_str)
    if match:
        hours = int(match.group(1))
        minutes = int(match.group(2) or 0)
        if hours < 0:
            minutes = -minutes
        offset = datetime.timedelta(hours=hours, minutes=minutes)
        return datetime.timezone(offset, name=upper_str)

    return None


def io_with_location():
    calendar_input = None
    time_input = None
    longitude_input = None
    latitude_input = None
    tz_input = None

    inputs = sys.argv[1:]

    for item in inputs:
        if re.match(r"^\d{4}-\d{2}-\d{2}$", item):
            calendar_input = item
        elif re.match(r"^\d{2}:\d{2}$", item):
            time_input = item
        elif re.match(r"^-?\d+(\.\d+)?[nsNS]$", item, re.IGNORECASE):
            latitude_input = item
        elif re.match(r"^-?\d+(\.\d+)?[ewEW]$", item, re.IGNORECASE):
            longitude_input = item
        elif parse_explicit_timezone(item) is not None:
            tz_input = item
        else:
            sys.exit(
                f'{bcolors.FAIL}Usage: "uv run convert_utc_to_local_time.py [YYYY-MM-DD] [HH:MM] [latDegN lonDegE | TIMEZONE]"'
                f"\n\nInputs are accepted regardless of order."
                f"\nNote: Providing coordinates and an explicit time zone together is not allowed."
                f"\nIf YYYY-MM-DD is omitted, current date is assumed."
                f"\nIf HH:MM is omitted, current UTC time is assumed."
                f"\nIf coordinates and timezone are both omitted, Washington, D.C. (39N 77W) is assumed.{bcolors.ENDC}"
                f"\nTIMEZONE input examples: UTC-5, EDT, EST, CDT, America/New_York, +02:00."
                f"\nNote that TIMEZONE and coordinates are mutually exclusive."
            )

    # Enforce mutual exclusivity between explicit timezone and coordinates
    has_coords = (latitude_input is not None) or (longitude_input is not None)
    has_tz = tz_input is not None

    if has_coords and has_tz:
        sys.exit(
            f"{bcolors.FAIL}Error: Cannot provide both coordinates and an explicit time zone.\n"
            f"Pass either coordinates (e.g. 39N 77W) OR a time zone (e.g. EST, UTC-5), but not both.{bcolors.ENDC}"
        )

    # Date resolution
    if calendar_input is None:
        dat = datetime.datetime.now(datetime.timezone.utc)
        year, month, day = dat.year, dat.month, dat.day
    else:
        try:
            dat = datetime.date.fromisoformat(calendar_input)
            year, month, day = dat.year, dat.month, dat.day
        except ValueError as err:
            sys.exit(f"{bcolors.FAIL}Invalid date input: {err}{bcolors.ENDC}")

    # Time resolution
    if time_input is None:
        dat = datetime.datetime.now(datetime.timezone.utc)
        hour, minute = dat.hour, dat.minute
    else:
        try:
            dat = datetime.time.fromisoformat(time_input)
            hour, minute = dat.hour, dat.minute
        except ValueError as err:
            sys.exit(f"{bcolors.FAIL}Invalid time input: {err}{bcolors.ENDC}")

    # Longitude resolution
    if longitude_input is None:
        longitude = -77.0
    else:
        try:
            lon_num = re.sub(r"[ewEW]$", "", longitude_input)
            val = np.float64(lon_num)
            longitude = -abs(val) if longitude_input.upper().endswith("W") else abs(val)
        except ValueError as err:
            sys.exit(f"{bcolors.FAIL}Invalid longitude: {err}{bcolors.ENDC}")

    # Latitude resolution
    if latitude_input is None:
        latitude = 39.0
    else:
        try:
            lat_num = re.sub(r"[nsNS]$", "", latitude_input)
            val = np.float64(lat_num)
            latitude = -abs(val) if latitude_input.upper().endswith("S") else abs(val)
        except ValueError as err:
            sys.exit(f"{bcolors.FAIL}Invalid latitude: {err}{bcolors.ENDC}")

    tz_obj = parse_explicit_timezone(tz_input) if tz_input else None

    return year, month, day, hour, minute, float(longitude), float(latitude), tz_obj, tz_input


def convert_utc_to_local():
    year, month, day, hour, minute, longitude, latitude, explicit_tz, tz_str = io_with_location()

    dt_utc = datetime.datetime(
        year, month, day, hour, minute, tzinfo=datetime.timezone.utc
    )

    print("")
    print(f"Input UTC Time  : {dt_utc.strftime('%Y-%m-%d %H:%M UTC')}")

    target_tz = None
    tz_label = ""

    # Determine timezone source (Explicit CLI input vs Coordinate Lookup)
    if explicit_tz is not None:
        target_tz = explicit_tz
        tz_label = f"Specified ({tz_str})"
    else:
        tf = TimezoneFinder()
        tz_name = tf.timezone_at(lng=longitude, lat=latitude)
        if tz_name:
            target_tz = ZoneInfo(tz_name)
            tz_label = f"GPS Lookup ({tz_name})"
        else:
            tz_label = "Unknown / International Waters"

    print(
        f"Coordinates     : {abs(latitude):.4f}°{'N' if latitude >= 0 else 'S'}, "
        f"{abs(longitude):.4f}°{'E' if longitude >= 0 else 'W'}"
    )

    if target_tz:
        dt_local = dt_utc.astimezone(target_tz)
        offset_str = dt_local.strftime("%z")
        formatted_offset = f"UTC{offset_str[:3]}:{offset_str[3:]}" if offset_str else ""
        tz_display_name = dt_local.tzname() or str(target_tz)

        print(f"Time Zone       : {tz_label} [{tz_display_name}, {formatted_offset}]")
        print(f"Local Time      : {dt_local.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print(f"Time Zone       : {tz_label}")


if __name__ == "__main__":
    convert_utc_to_local()