"""Quick smoke-plot: draw demo.json with default BrachioGraph parameters."""
from brachiograph import BrachioGraph

bg = BrachioGraph()
print("Drawing demo.json ...", flush=True)
bg.plot_file("images/demo.json")
bg.quiet()
print("done.", flush=True)
