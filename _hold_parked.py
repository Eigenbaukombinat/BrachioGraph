"""Helper: hold BrachioGraph in parked pose until interrupted."""
import time
from brachiograph import BrachioGraph

bg = BrachioGraph()
bg.set_angles(bg.servo_1_parked_angle, bg.servo_2_parked_angle)
bg.pen.up()
print(
    "Parked pose held: shoulder pw=1500 (angle -90), elbow pw=1500 (angle 90), "
    "pen up pw=1500.",
    flush=True,
)
print("Strg-C oder kill_terminal, wenn du fertig bist.", flush=True)
try:
    while True:
        time.sleep(1)
finally:
    bg.quiet()
    print("quiet.", flush=True)
