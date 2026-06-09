import numpy as np

def map_stairs_correct(p):
    sp = np.array(p)
    # The new heightmap math:
    stairs_step = 0.2
    # target height is determined by Z only
    slope_y = -sp[2] * 1.5
    stepped_y = np.floor(slope_y / stairs_step) * stairs_step
    # exact vertical distance
    vert_dist = sp[1] - stepped_y
    # multiply by cos(theta) safety factor to approximate euclidean distance
    # slope is 1.5 in Z, so vector is (0, 1, 1.5). length is sqrt(1 + 2.25) = 1.8
    safety_factor = 1.0 / 1.8
    d = vert_dist * safety_factor
    return d

p1 = np.array([0.0, 0.19999, 0.0])
p2 = np.array([0.0, 0.20001, 0.0])

d1 = map_stairs_correct(p1)
d2 = map_stairs_correct(p2)

print(f"p1: {p1}, d1: {d1}")
print(f"p2: {p2}, d2: {d2}")
print(f"Distance between points: {np.linalg.norm(p1 - p2)}")
print(f"Difference in SDF (Y test): {abs(d1 - d2)}")
if abs(d1 - d2) > np.linalg.norm(p1 - p2):
    print("ERROR: Lipschitz continuity violated on Y! Rays will break/clip.")
else:
    print("OK on Y")

p3 = np.array([0.0, 0.2, 0.13333])
p4 = np.array([0.0, 0.2, 0.13334])
d3 = map_stairs_correct(p3)
d4 = map_stairs_correct(p4)
print(f"Difference in SDF (Z test): {abs(d3 - d4)} vs Distance {np.linalg.norm(p3 - p4)}")
if abs(d3 - d4) > np.linalg.norm(p3 - p4):
    print("ERROR: Lipschitz continuity violated on Z!")
else:
    print("OK on Z")

