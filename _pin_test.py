"""Pin-Diagnose: bewegt nacheinander Pin 14, 15, 18 mit einem kleinen Wackler.

Beobachte, welcher physische Servo sich beim jeweiligen Pin bewegt.
Erwartete Zuordnung:
    Pin 14 -> Schulter (innerer Arm)
    Pin 15 -> Ellbogen (äußerer Arm)
    Pin 18 -> Stift
"""
from time import sleep
import esppio

rpi = esppio.pi()
sleep(0.3)


def wackel(pin):
    for us in (1300, 1700, 1500):
        rpi.set_servo_pulsewidth(pin, us)
        sleep(0.8)


for pin in (14, 15, 18):
    input(f"\n==> ENTER druecken, dann ~3 s beobachten:  PIN {pin}")
    wackel(pin)
    rpi.set_servo_pulsewidth(pin, 0)  # detach
    print(f"   (Pin {pin} fertig, detached.)")

print("\nfertig.")
rpi.stop()
