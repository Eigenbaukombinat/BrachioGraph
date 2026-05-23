"""Draw a small rectangle near the centre of the drawing area."""
from brachiograph import BrachioGraph

bg = BrachioGraph()
# Default bounds are [-8, 4, 6, 13]; centre ~ (-1, 8.5).
# Small 4x3 cm box around that centre.
bg.box(bounds=(-3, 7, 1, 10))
bg.quiet()
print("done.", flush=True)
