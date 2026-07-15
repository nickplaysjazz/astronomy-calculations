import itertools
import numpy as np
from prettytable import PrettyTable

from calc_planetary_positions import calc_positions, io

cosd = lambda deg : np.cos(np.deg2rad(deg))
sind = lambda deg : np.sin(np.deg2rad(deg))
tand = lambda deg : np.tan(np.deg2rad(deg))
atan2d = lambda y, x :  np.mod(np.rad2deg(np.atan2(y, x)), 360)

pi = np.pi

degree_sign = u'\N{DEGREE SIGN}'

planets = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]

# major aspects and their default "orbs" within which they are valid
ASPECTS = {
    "conjunction": (0.0, 7.0),
    "sextile":     (60.0, 7.0),
    "square":      (90.0, 7.0),
    "trine":       (120.0, 7.0),
    "opposition":  (180.0, 7.0)
}

def calc_aspects(y, m, day, UT, d):
    ecliptic_positions = calc_positions(y, m, day, UT, d, is_equatorial=False)
    
    longitudes = []
    for planet_num in range(len(planets)):
        xg, yg, zg = ecliptic_positions[planet_num]
        
        lon = atan2d(yg, xg)
        longitudes.append(lon)
        
    found_aspects = []
    
    # iterating over all pairs of planets
    for i, j in itertools.combinations(range(len(planets)), 2):
        planet1 = planets[i]
        planet2 = planets[j]
        
        lon1 = longitudes[i]
        lon2 = longitudes[j]
        
        # shortest distance only
        diff = abs(lon1 - lon2)
        if diff > 180.0:
            diff = 360.0 - diff
            
        # does the diff land in any aspect? 
        for aspect_name, (target_angle, orb) in ASPECTS.items():
            if abs(diff - target_angle) <= orb:
                deviation = diff - target_angle
                found_aspects.append({
                    "p1": planet1,
                    "p2": planet2,
                    "aspect": aspect_name,
                    "diff": diff,
                    "deviation": deviation
                })
                break 
                
    return found_aspects

if __name__ == "__main__":
    y, m, day, io_h, io_m = io()
    UT = io_h + (io_m/60)
    
    d = 367 * y - 7 * (y + (m + 9) // 12) // 4 - 3 * ((y + (m - 9)//7)//100 + 1)//4 + 275 * m // 9 + day - 730515
    d = d + UT / 24

    aspects = calc_aspects(y, m, day, UT, d)

    table = PrettyTable()
    table.field_names = ["Body 1", "Body 2", "Aspect", "Separation", "Deviation"]
    table.align = "l"
    table.align["Separation"] = "r"
    table.align["Deviation"] = "r"

    aspects.sort(key=lambda x: abs(x["deviation"]))
    
    for asp in aspects:
        table.add_row([
            asp["p1"],
            asp["p2"],
            asp["aspect"],
            f"{asp['diff']:.2f}{degree_sign}",
            f"{asp['deviation']:+.2f}{degree_sign}"
        ])
        
    print(f"\nPlanetary aspects for: {y:04}-{m:02}-{day:02} {io_h:02}:{io_m:02} UTC")
    if not aspects:
        print("No major aspects found within the defined orbs.")
    else:
        print(table)
    print("")