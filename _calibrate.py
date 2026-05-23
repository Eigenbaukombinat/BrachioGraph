"""Interaktive Kalibrierung der Pulse-Widths.

Bedienung:
    Schulter (innen):  a/A = -10/-1 µs   s/S = +10/+1 µs
    Ellbogen (außen):  k/K = -10/-1 µs   l/L = +10/+1 µs
    Stift:             z = -10 µs        x = +10 µs

    c  Wert erfassen (fragt nach Winkel bzw. Stift-Zustand u/d)
    v  bisher erfasste Werte anzeigen
    0  beenden und Ergebnis ausgeben

Pro Winkel BEIDE Richtungen erfassen (einmal von links anfahren = "cw",
einmal von rechts = "acw"), damit eine bidirektionale Tabelle entsteht.

Empfohlen: Schulter über -135° .. -45° in 15°-Schritten,
           Ellbogen über   45° .. 135° in 15°-Schritten,
           Stift up und down.
"""
from brachiograph import BrachioGraph

bg = BrachioGraph()
try:
    bg.capture_pws()
finally:
    bg.quiet()
    print("done.")
