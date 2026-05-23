"""Draw a small house: a box with a triangular roof and a door."""
from brachiograph import BrachioGraph

bg = BrachioGraph()

# house outline (4 cm wide, 3 cm tall), centred around x=-1, y=8.5
lines = [
    # walls + roof, closed polygon
    [[-3, 7], [1, 7], [1, 9], [-1, 10.5], [-3, 9], [-3, 7]],
    # door
    [[-1.5, 7], [-1.5, 8], [-0.5, 8], [-0.5, 7]],
    # window
    [[0, 8], [0.5, 8], [0.5, 8.5], [0, 8.5], [0, 8]],
]

bg.plot_lines(lines, bounds=[-3, 7, 1, 10.5])
bg.quiet()
print("done.", flush=True)
