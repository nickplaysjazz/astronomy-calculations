import numpy as np
from prettytable import PrettyTable

from orbital_elements import OrbitalElements
from calc_planetary_positions import calc_positions, io

cosd = lambda deg : np.cos(np.deg2rad(deg))
sind = lambda deg : np.sin(np.deg2rad(deg))
tand = lambda deg : np.tan(np.deg2rad(deg))
atan2d = lambda y, x :  np.mod(np.rad2deg(np.atan2(y, x)), 360)

pi = np.pi

degree_sign = u'\N{DEGREE SIGN}'

planets = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]

# geocentric speeds are taken from wikipedia, calculated from a program using apparently good ephemeris
# could double check these values
MEAN_GEOCENTRIC_SPEEDS = {
    "sun": 0.985555556,
    "moon": 13.17638889,
    "mercury": 1.383333333,
    "venus": 1.200,
    "mars": 0.524166667,
    "jupiter": 0.083055556,
    "saturn": 0.033611111
}

# we could use a more complex scheme to scale deviations by max/min velocities achievable
# MAX_GEOCENTRIC_SPEEDS = {
#     "sun": 1.05,
#     "moon": 16.5,
#     "mercury": 2.416667,
#     "venus": 1.366667,
#     "mars": 0.8666667,
#     "jupiter": 0.261111,
#     "saturn": 0.146667
# }

# MIN_GEOCENTRIC_SPEEDS = {
#     "sun": 0.952778,
#     "moon": 11.76,
#     "mercury": -1.5,
#     "venus": -0.68667,
#     "mars": -0.43667,
#     "jupiter": -0.14722,
#     "saturn": -0.09167
# }

def calc_angular_speeds(y, m, day, UT, d):
    ecliptic_positions = calc_positions(y, m, day, UT, d, is_equatorial=False)
    
    elements_0 = OrbitalElements(d)
    elements_1 = OrbitalElements(d + 1)
    
    M_list_0 = np.mod(elements_0.M_list, 360)
    M_list_1 = np.mod(elements_1.M_list, 360)
    
    # daily mean motion in deg/day
    delta_M = np.mod(M_list_1 - M_list_0 + 180, 360) - 180
    n_list = delta_M 

    speeds = []
    sun_vg = np.array([0.0, 0.0, 0.0])
    
    for planet_num, planet_name in enumerate(planets):
        a = elements_0.a_list[planet_num]
        e = elements_0.e_list[planet_num]
        M = M_list_0[planet_num]
        w = elements_0.w_list[planet_num]
        N = elements_0.N_list[planet_num]
        i = elements_0.i_list[planet_num]
        n = n_list[planet_num]
        
        # obtain eccentric anomaly E 
        E0 = M + (180 / pi) * e * sind(M) * (1 + e * cosd(M))
        tol = 1e-5
        while True:
            E1 = E0 - (E0 - e * (180 / pi) * sind(E0) - M) / (1 - e * cosd(E0))
            if abs(E1 - E0) < tol:
                E = E1
                break
            E0 = E1
            
        # time derivative of eccentric anomaly: rad/day
        dE_dt = np.deg2rad(n) / (1 - e * cosd(E))
        
        # velocity in the orbital plane in au/day
        vx_v = -a * sind(E) * dE_dt
        vy_v = a * np.sqrt(1 - e**2) * cosd(E) * dE_dt
        
        if planet_name == "sun":
            # sun elements are Earth's elements, geocentric perspective
            # need rotated
            vx_g = vx_v * cosd(w) - vy_v * sind(w)
            vy_g = vx_v * sind(w) + vy_v * cosd(w)
            vz_g = 0.0
            
            vg = np.array([vx_g, vy_g, vz_g])
            sun_vg = vg
        else:
            # map orbital velocity to the heliocentric ecliptic
            Px = cosd(w)*cosd(N) - sind(w)*sind(N)*cosd(i)
            Py = cosd(w)*sind(N) + sind(w)*cosd(N)*cosd(i)
            Pz = sind(w)*sind(i)
            
            Qx = -sind(w)*cosd(N) - cosd(w)*sind(N)*cosd(i)
            Qy = -sind(w)*sind(N) + cosd(w)*cosd(N)*cosd(i)
            Qz =  cosd(w)*sind(i)
            
            vh = np.array([
                vx_v * Px + vy_v * Qx,
                vx_v * Py + vy_v * Qy,
                vx_v * Pz + vy_v * Qz
            ])
            
            if planet_name == "moon":
                # moons elements are geocentric
                vg = vh
            else:
                # otherwise geocentric velocity = heliocentric velocity + sun geocentric velocity
                vg = vh + sun_vg
                
        # apparent angular speed across the sky is d(lambda)/dt
        xg, yg, zg = ecliptic_positions[planet_num]
        vxg, vyg, vzg = vg
        
        dlambda_dt = (xg * vyg - yg * vxg) / (xg**2 + yg**2)
        deg_per_day = np.rad2deg(dlambda_dt)
        
        speeds.append(deg_per_day)
        
    return speeds

if __name__ == "__main__":
    y, m, day, io_h, io_m = io()
    UT = io_h + (io_m/60)
    
    d = 367 * y - 7 * (y + (m + 9) // 12) // 4 - 3 * ((y + (m - 9)//7)//100 + 1)//4 + 275 * m // 9 + day - 730515
    d = d + UT / 24

    speeds = calc_angular_speeds(y, m, day, UT, d)

    table = PrettyTable()
    table.field_names = ["Planet", "Current Speed", "Mean Speed", "Deviation", "Status"]
    table.align = "r"
    
    for planet_num, planet_name in enumerate(planets):
        current_speed = speeds[planet_num]
        mean_speed = MEAN_GEOCENTRIC_SPEEDS[planet_name]
        
        # deviation percentage relative to the mean speed
        deviation_pct = ((current_speed - mean_speed) / mean_speed) * 100
        
        if current_speed < 0:
            status = "Retrograde"
        elif current_speed > mean_speed:
            status = "Direct (Swift)"
        else:
            status = "Direct (Slow)"
            
        table.add_row([
            planet_name.capitalize(),
            f"{current_speed:+.4f}{degree_sign}/day",
            f"{mean_speed:.4f}{degree_sign}/day",
            f"{deviation_pct:+.1f}%",
            status
        ])
        
    print(f"\nApparent geocentric velocities for: {y:04}-{m:02}-{day:02} {io_h:02}:{io_m:02} UTC")
    print(table)
    print("")
    print("")