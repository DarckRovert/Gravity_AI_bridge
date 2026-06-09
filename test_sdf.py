import numpy as np

def sdBox(p, b):
    q = np.abs(p) - b
    return np.linalg.norm(np.maximum(q, 0.0)) + min(max(q[0], max(q[1], q[2])), 0.0)

def map_stairs(p):
    sp = np.array(p)
    sp[0] = abs(sp[0]) - 4.0
    stairs_step = 0.2
    stairs_slope = np.floor((sp[1] + sp[2] * 1.5) / stairs_step) * stairs_step
    box_p = sp - np.array([0.0, stairs_slope, 0.0])
    return sdBox(box_p, np.array([0.8, stairs_step*0.4, 20.0]))

p1 = np.array([0.0, 0.19999, 0.0])
p2 = np.array([0.0, 0.20001, 0.0])

d1 = map_stairs(p1)
d2 = map_stairs(p2)

print(f"p1: {p1}, d1: {d1}")
print(f"p2: {p2}, d2: {d2}")
print(f"Distance between points: {np.linalg.norm(p1 - p2)}")
print(f"Difference in SDF: {abs(d1 - d2)}")
if abs(d1 - d2) > np.linalg.norm(p1 - p2):
    print("ERROR: Lipschitz continuity violated! Rays will break/clip.")
else:
    print("OK")
