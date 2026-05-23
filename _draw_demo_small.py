"""Draw demo.json scaled small near the centre of the drawing area."""
from brachiograph import BrachioGraph

bg = BrachioGraph()
# Small image area, centred-ish around (-1, 8.5). ~5x4 cm.
bg.plot_file("images/demo.json", bounds=(-3.5, 6.5, 1.5, 10.5))
bg.quiet()
print("done.", flush=True)
