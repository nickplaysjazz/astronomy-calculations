import datetime
import numpy as np

from prettytable import PrettyTable
from calc_planetary_positions import io, calc_positions

# macros for trig calculations
cosd = lambda deg: np.cos(np.deg2rad(deg))
sind = lambda deg: np.sin(np.deg2rad(deg))
tand = lambda deg: np.tan(np.deg2rad(deg))
atan2d = lambda y, x: np.mod(np.rad2deg(np.atan2(y, x)), 360)

# constants needed for calculations
EARTH_RADIUS_KM = 6378.137
SUN_RADIUS_KM = 695700.0
MOON_RADIUS_KM = 1737.40
AU_IN_KM = 149597870.7

# generated from an equirectangular projection (necessarily equirectangular for a regular lat/lon grid!)
# 144 by 36
WORLD_MAP = [
    "................................................................................................................................................",
    "................................................................................................................................................",
    "...............................#...##...#....####################...............##.................................#............................",
    "......................###.........##..............#############.................................#.............########..........................",
    "......##########....####...##.#..#.#.......##........##########..................#######.....#.....#..#...#####################################.",
    ".......##############################.##...###.......###.........##...........####.#####.#######################################################",
    ".......###......#.################.......####...............................####...##############.##################################........#...",
    "....................###################..########.....................#.#.......#.###############.###############################.........#.....",
    ".....................#.#######################............................###################.#####################################.#...........",
    "......................#######################.#..........................#####..#####..#.####.####################################..............",
    "......................####################............................###.........#.#######################################..#.....#............",
    "........................##################...............................#####..........###################################.....##..............",
    "...........................#########...#.............................########################.#############################.....................",
    ".............................####..................................#####################.#####..#.##.#####################......................",
    "..............................###...#..............................######################.#######.......#####...#####...........................",
    "...................................##..............................######################..####.........##........####..........................",
    "......................................#....##......................########################..#...........#..........##..........................",
    "..........................................########...................####..###################...........................#......................",
    ".........................................############.........................#############.......................#...####......................",
    "........................................#################.....................############..........................#......#.....####...........",
    ".........................................##################....................##########..........................................#............",
    "..........................................###############......................###########.....................................##...............",
    "............................................#############.....................###########...##..............................##########..........",
    "............................................###########........................#########...##...........................###############.........",
    "............................................#########...........................#######..................................################.......",
    "............................................########.............................####....................................####....#######........",
    "...........................................#######.................................................................................####.........",
    "............................................###......................................................................................#..........",
    "...........................................###..................................................................................................",
    "............................................#...................................................................................................",
    "................................................................................................................................................",
    "................................................................................................................................................",
    "..............................................#................................................#...................##..##......###..............",
    "............................................#.##.....................###.############################..########################################.",
    "..............##############################.................#.#############################################################################....",
    "...........#.##############################.............#..#################################################################################....",
]


def calculate_delta_t(y, m):
    """
    Predicts Delta T (TT - UT) in seconds using NASA Espenak-Meeus polynomial fits.
    Expects integer year (y) and month (m). Should be fairly accurate from -1999 to 3000 CE.
    See https://eclipse.gsfc.nasa.gov/LEcat5/deltatpoly.html for details
    """
    decimal_year = y + (m - 0.5) / 12.0
    if 2005 <= decimal_year < 2050:
        t = decimal_year - 2005
        return 62.92 + 0.32217 * t + 0.005589 * t**2
    elif 1986 <= decimal_year < 2005:
        t = decimal_year - 2000
        return 63.86 + 3.374 * t - 0.3541 * t**2 - 0.00104 * t**3
    elif 1900 <= decimal_year < 1961:
        t = (decimal_year - 1900) / 100.0
        return -2.71 + 101.42 * t - 165.23 * t**2 + 372.48 * t**3 - 279.79 * t**4
    elif 1600 <= decimal_year < 1800:
        t = (decimal_year - 1600) / 100.0
        return 120 - 98.08 * t - 153.2 * t**2 + 140.27 * t**3
    elif 500 <= decimal_year < 1600:
        u = (decimal_year - 1000) / 100.0
        return (
            1574.2
            - 556.01 * u
            + 71.23472 * u**2
            + 0.319781 * u**3
            - 0.8503463 * u**4
            - 0.005050998 * u**5
            + 0.0083572073 * u**6
        )
    elif 2050 <= decimal_year < 2150:
        return -20 + 32 * ((decimal_year - 1820) / 100.0) ** 2
    else:
        t = (decimal_year - 1820) / 100.0
        return -20.0 + 32.0 * t**2


def get_coords(y, m, day, UT, d, planet_index):
    # correct utc to terrestrial time
    delta_t_seconds = calculate_delta_t(y, m)
    delta_t_days = delta_t_seconds / 86400.0
    d_tt = d + delta_t_days

    ecl_positions = calc_positions(
        y, m, day, UT, d_tt, is_equatorial=False, correct_for_precession=True
    )
    xg, yg, zg = ecl_positions[planet_index]

    lon = atan2d(yg, xg)
    lat = np.rad2deg(np.arctan2(zg, np.sqrt(xg**2 + yg**2)))
    dist_raw = np.sqrt(xg**2 + yg**2 + zg**2)

    # convert all units to km
    if planet_index == 0:
        dist_km = dist_raw * AU_IN_KM
    elif planet_index == 1:
        dist_km = dist_raw * EARTH_RADIUS_KM
    else:
        dist_km = dist_raw

    return lon, lat, dist_km


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


def generate_ascii_map(
    target_ra,
    target_dec,
    d_utc,
    is_solar,
    moon_ra=None,
    moon_dec=None,
    moon_dist_km=None,
    r_sun=None,
    r_moon=None,
):

    map_str = "      180W                    120W                    60W                      0                      60E                     120E                   180E\n"
    map_str += "      +-----------------------+-----------------------+-----------------------+-----------------------+-----------------------+-----------------------+\n"

    # map is 144 by 36
    lats = 87.5 - np.arange(36) * 5.0 
    lons = -178.75 + np.arange(144) * 2.5

    totality_mask = np.zeros((36, 144), dtype=bool)
    partial_mask = np.zeros((36, 144), dtype=bool)

    # when we have a solar eclipse, we need to track +/- 2.5 hours around the maximum eclipse
    # this allows us to find the path of totality as the eclipse occurs
    time_steps = []
    if is_solar and all(v is not None for v in [y, m, day, UT]):
        for dt_minutes in range(-150, 151, 5):
            d_offset = d_utc + (dt_minutes / 1440.0)
            s_lon, s_lat, s_dist = get_coords(y, m, day, UT, d_offset, 0)
            m_lon, m_lat, m_dist = get_coords(y, m, day, UT, d_offset, 1)
            s_ra, s_dec = ecliptic_to_equatorial(s_lon, s_lat, d_offset)
            m_ra, m_dec = ecliptic_to_equatorial(m_lon, m_lat, d_offset)
            rsun = np.rad2deg(np.arcsin(SUN_RADIUS_KM / s_dist))
            rmoon = np.rad2deg(np.arcsin(MOON_RADIUS_KM / m_dist))

            time_steps.append(
                {
                    "d_utc": d_offset,
                    "sun_ra": s_ra,
                    "sun_dec": s_dec,
                    "moon_ra": m_ra,
                    "moon_dec": m_dec,
                    "moon_dist_km": m_dist,
                    "r_sun": rsun,
                    "r_moon": rmoon,
                }
            )
    else:
        time_steps = [
            {
                "d_utc": d_utc,
                "sun_ra": target_ra,
                "sun_dec": target_dec,
                "moon_ra": moon_ra,
                "moon_dec": moon_dec,
                "moon_dist_km": moon_dist_km,
                "r_sun": r_sun,
                "r_moon": r_moon,
            }
        ]

    lat_offsets = np.array([-2.0, 0.0, 2.0])
    lon_offsets = np.array([-1.0, 0.0, 1.0])

    grid_lats = np.clip(
        lats[:, None, None, None] + lat_offsets[None, None, :, None], -90, 90
    )
    grid_lons = lons[None, :, None, None] + lon_offsets[None, None, None, :]

    for step in time_steps:
        gmst = get_gmst(step["d_utc"])

        if is_solar:
            # need to find horizon first
            center_lmst = (gmst + lons[None, :]) % 360
            center_lha = (center_lmst - step["sun_ra"]) % 360
            sin_alt_center = sind(lats[:, None]) * sind(step["sun_dec"]) + cosd(
                lats[:, None]
            ) * cosd(step["sun_dec"]) * cosd(center_lha)
            daylight_cells = sin_alt_center > 0

            if not np.any(daylight_cells):
                continue

            #  topocentric conversions
            lst = (gmst + grid_lons) % 360
            x_obs = EARTH_RADIUS_KM * cosd(grid_lats) * cosd(lst)
            y_obs = EARTH_RADIUS_KM * cosd(grid_lats) * sind(lst)
            z_obs = EARTH_RADIUS_KM * sind(grid_lats)

            x_body = (
                step["moon_dist_km"] * cosd(step["moon_dec"]) * cosd(step["moon_ra"])
            )
            y_body = (
                step["moon_dist_km"] * cosd(step["moon_dec"]) * sind(step["moon_ra"])
            )
            z_body = step["moon_dist_km"] * sind(step["moon_dec"])

            xt, yt, zt = x_body - x_obs, y_body - y_obs, z_body - z_obs
            topo_ra = atan2d(yt, xt)
            topo_dec = np.rad2deg(np.arctan2(zt, np.sqrt(xt**2 + yt**2)))

            # angular separation from great circle
            cos_sep = sind(step["sun_dec"]) * sind(topo_dec) + cosd(
                step["sun_dec"]
            ) * cosd(topo_dec) * cosd(step["sun_ra"] - topo_ra)
            cos_sep = np.clip(cos_sep, -1.0, 1.0)
            sep = np.rad2deg(np.arccos(cos_sep))

            step_totality = sep <= abs(step["r_sun"] - step["r_moon"])
            step_partial = sep <= (step["r_sun"] + step["r_moon"])

            any_totality = np.any(step_totality, axis=(2, 3)) & daylight_cells
            any_partial = np.any(step_partial, axis=(2, 3)) & daylight_cells

            totality_mask |= any_totality
            partial_mask |= any_partial
        else:
            # for a lunar eclipse, visibility map is the Moon's altitude profile above horizon
            lmst = (gmst + lons[None, :]) % 360
            lha = (lmst - step["sun_ra"]) % 360
            sin_alt = sind(lats[:, None]) * sind(step["sun_dec"]) + cosd(
                lats[:, None]
            ) * cosd(step["sun_dec"]) * cosd(lha)
            totality_mask |= sin_alt > 0
            break

    # plot graph now
    for r in range(36):
        lat = lats[r]
        row_str = f"{abs(lat+2.5):4.0f} |" if r % 6 == 0 else "     |"

        for c in range(144):
            base_char = WORLD_MAP[r][c]
            if totality_mask[r, c]:
                row_str += "@" if base_char == "#" else ":"
            elif is_solar and partial_mask[r, c]:
                row_str += "+" if base_char == "#" else "."
            else:
                row_str += "#" if base_char == "#" else " "
        map_str += row_str + "\n"

    map_str += "      +-----------------------+-----------------------+-----------------------+-----------------------+-----------------------+-----------------------+\n"
    map_str += (
        "Legend: [@:] = Path of Totality/Annularity, [+.] = Partial eclipse, [# ] = No eclipse\n"
        if is_solar
        else "Legend: [@] = Eclipse visible on land, [:] = Eclipse visible on water, [#] = No eclipse\n"
    )
    return map_str


def get_geographic_summary(ra, dec, d_utc, is_solar):
    gmst = get_gmst(d_utc)
    sub_lon = (ra - gmst + 180) % 360 - 180
    sub_lat = dec
    lat_dir = "N" if sub_lat >= 0 else "S"
    lon_dir = "E" if sub_lon >= 0 else "W"
    body = "Sun" if is_solar else "Moon"
    return f"The {body} will be directly overhead at {abs(sub_lat):.1f}\N{DEGREE SIGN} {lat_dir}, {abs(sub_lon):.1f}\N{DEGREE SIGN} {lon_dir}. "


def get_syzygy_diff(d, y, m, day, UT):
    sun_lon, _, _ = get_coords(y, m, day, UT, d, 0)
    moon_lon, _, _ = get_coords(y, m, day, UT, d, 1)
    diff = moon_lon - sun_lon
    return (diff + 180) % 360 - 180


def find_exact_syzygy(d_start, d_end, y, m, day, UT, target_diff):
    # here we have a bisection zero-finding method
    low, high = d_start, d_end
    for _ in range(500):
        mid = (low + high) / 2.0
        diff = get_syzygy_diff(mid, y, m, day, UT)
        eval_diff = (diff - target_diff + 180) % 360 - 180
        diff_low = get_syzygy_diff(low, y, m, day, UT)
        eval_diff_low = (diff_low - target_diff + 180) % 360 - 180

        if eval_diff * eval_diff_low > 0:
            low = mid
        else:
            high = mid

        if abs(eval_diff) < 1e-6:
            break
    return mid


def check_for_eclipse(d_syz, y, m, day, UT, is_solar):
    sun_lon, sun_lat, sun_dist = get_coords(y, m, day, UT, d_syz, 0)
    moon_lon, moon_lat, moon_dist = get_coords(y, m, day, UT, d_syz, 1)

    r_sun = np.rad2deg(np.arcsin(SUN_RADIUS_KM / sun_dist))
    r_moon = np.rad2deg(np.arcsin(MOON_RADIUS_KM / moon_dist))
    pi_sun = np.rad2deg(np.arcsin(EARTH_RADIUS_KM / sun_dist))
    pi_moon = np.rad2deg(np.arcsin(EARTH_RADIUS_KM / moon_dist))

    abs_beta = abs(moon_lat)

    # abs_beta parameter tells us relative size of sun/moon when viewed from earth
    if is_solar:
        beta_max = r_sun + r_moon + pi_moon - pi_sun
        if abs_beta <= beta_max:
            if abs_beta < (r_moon + pi_moon - pi_sun - r_sun):
                if r_moon >= r_sun:
                    return "Total Solar Eclipse"
                return "Annular Solar Eclipse"
            return "Partial Solar Eclipse"
        return None
    else:
        R_umbra = pi_moon + pi_sun - r_sun
        R_penumbra = pi_moon + pi_sun + r_sun
        if abs_beta <= (R_umbra + r_moon):
            if abs_beta <= (R_umbra - r_moon):
                return "Total Lunar Eclipse"
            return "Partial Lunar Eclipse"
        elif abs_beta <= (R_penumbra + r_moon):
            return "Penumbral Lunar Eclipse"
        return None


def convert_d_to_utc(d):
    base_date = datetime.datetime(1999, 12, 31, 0, 0, 0)
    delta = datetime.timedelta(days=d)
    return base_date + delta


if __name__ == "__main__":
    y, m, day, io_h, io_m = io()
    UT = io_h + (io_m / 60.0)

    d_start = (
        367 * y
        - 7 * (y + (m + 9) // 12) // 4
        - 3 * ((y + (m - 9) // 7) // 100 + 1) // 4
        + 275 * m // 9
        + day
        - 730515
    )
    d_start = d_start + UT / 24.0

    search_days = 365

    print(
        f"\nScanning for eclipses one year forward from: {y:04}-{m:02}-{day:02} {io_h:02}:{io_m:02} UTC"
    )

    table = PrettyTable()
    table.field_names = ["Date (UTC)", "Type"]
    table.align = "l"

    prev_diff = get_syzygy_diff(d_start, y, m, day, UT)

    report_content = 144 * "=" + "\n"
    report_content += 60 * " " + "ECLIPSE VISIBILITY REPORT" + 60 * " " + "\n"
    report_content += 144 * "=" + "\n\n"

    for step in range(1, search_days):
        d_current = d_start + step
        current_diff = get_syzygy_diff(d_current, y, m, day, UT)

        is_crossing = False
        target_diff = 0
        is_solar = True

        if prev_diff < 0 and current_diff >= 0:
            is_crossing = True
            target_diff = 0
            is_solar = True
        elif (prev_diff > 0 and current_diff <= 0) and abs(
            prev_diff - current_diff
        ) > 180:
            is_crossing = True
            target_diff = 180
            is_solar = False

        if is_crossing:
            d_syz = find_exact_syzygy(
                d_current - 1, d_current, y, m, day, UT, target_diff
            )
            eclipse_type = check_for_eclipse(d_syz, y, m, day, UT, is_solar)

            if eclipse_type:
                dt_utc = convert_d_to_utc(d_syz)
                sun_lon, sun_lat, sun_dist = get_coords(y, m, day, UT, d_syz, 0)
                moon_lon, moon_lat, moon_dist = get_coords(y, m, day, UT, d_syz, 1)

                table.add_row([dt_utc.strftime("%Y-%m-%d %H:%M:%S"), eclipse_type])

                sun_ra, sun_dec = ecliptic_to_equatorial(sun_lon, sun_lat, d_syz)
                moon_ra, moon_dec = ecliptic_to_equatorial(moon_lon, moon_lat, d_syz)

                target_ra = sun_ra if is_solar else moon_ra
                target_dec = sun_dec if is_solar else moon_dec

                report_content += f"[{eclipse_type.upper()}]\n"
                report_content += (
                    f"UTC Time:   {dt_utc.strftime('%Y-%m-%d %H:%M:%S')}\n"
                )
                report_content += (
                    get_geographic_summary(target_ra, target_dec, d_syz, is_solar)
                    + "\n\n"
                )

                if is_solar:
                    r_sun = np.rad2deg(np.arcsin(SUN_RADIUS_KM / sun_dist))
                    r_moon = np.rad2deg(np.arcsin(MOON_RADIUS_KM / moon_dist))
                    report_content += generate_ascii_map(
                        sun_ra,
                        sun_dec,
                        d_syz,
                        True,
                        moon_ra=moon_ra,
                        moon_dec=moon_dec,
                        moon_dist_km=moon_dist,
                        r_sun=r_sun,
                        r_moon=r_moon,
                    )
                else:
                    report_content += generate_ascii_map(
                        moon_ra, moon_dec, d_syz, False
                    )

                report_content += "\n" + 144 * "=" + "\n\n"

        prev_diff = current_diff

    print(table)

    with open("eclipse_report.txt", "w", encoding="utf-8") as f:
        f.write(report_content)

    print("\nReport successfully saved to 'eclipse_report.txt'.")
