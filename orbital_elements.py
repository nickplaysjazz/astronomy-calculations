"""

The following values are taken from algorithms developed by Paul Schlyter.
For details, please see his original write-up at https://stjarnhimlen.se/comp/ppcomp.html.

"""
class OrbitalElements:
    def __init__(self, d):
        # day number
        self.d = d

        # in the following, each element in the list is for the planets in the following order:
        # sun, moon, mercury, venus, mars, jupiter, saturn

        # longitude of ascending node
        self.N_list = [
            0.0,
            125.1228 - 0.0529538083 * d,
            48.3313 + 3.24587e-5 * d,
            76.6799 + 2.46590e-5 * d,
            49.5574 + 2.11081e-5 * d,
            100.4542 + 2.76854e-5 * d,
            113.6634 + 2.38980e-5 * d,
        ]
        # inclination to ecliptic
        self.i_list = [
            0.0,
            5.1454,
            7.0047 + 5.00e-8 * d,
            3.3946 + 2.75e-8 * d,
            1.8497 - 1.78e-8 * d,
            1.3030 - 1.557e-7 * d,
            2.4886 - 1.081e-7 * d,
        ]
        # argument of periapsis
        self.w_list = [
            282.9404 + 4.70935e-5 * d,
            318.0634 + 0.1643573223 * d,
            29.1241 + 1.01444e-5 * d,
            54.8910 + 1.38374e-5 * d,
            286.5016 + 2.92961e-5 * d,
            273.8777 + 1.64505e-5 * d,
            339.3939 + 2.97661e-5 * d,
        ]
        # semi-major axis: in AU except for Luna, in earth radii
        self.a_list = [1.000000, 60.2666, 0.387098, 0.723330, 1.523688, 5.20256, 9.55475]
        # ecccentricity
        self.e_list = [
            0.016709 - 1.151e-9 * d,
            0.054900,
            0.205635 + 5.59e-10 * d,
            0.006773 - 1.302e-9 * d,
            0.093405 + 2.516e-9 * d,
            0.048498 + 4.469e-9 * d,
            0.055546 - 9.499e-9 * d,
        ]
        # mean anomaly
        self.M_list = [
            356.0470 + 0.9856002585 * d,
            115.3654 + 13.0649929509 * d,
            168.6562 + 4.0923344368 * d,
            48.0052 + 1.6021302244 * d,
            18.6021 + 0.5240207766 * d,
            19.8950 + 0.0830853001 * d,
            316.9670 + 0.0334442282 * d,
        ]