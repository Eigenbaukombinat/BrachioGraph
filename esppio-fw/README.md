# ESPpio firmware

Firmware for an ESP32-S3 Mini that exposes its hardware-PWM servo outputs
to a host computer over USB-CDC, replacing the `pigpiod` daemon used by
BrachioGraph on a Raspberry Pi.

The matching host-side shim is [`esppio.py`](../esppio.py) in the project
root. It exposes the small subset of the `pigpio` API that BrachioGraph
actually uses (`set_servo_pulsewidth`, `set_PWM_frequency`,
`get_servo_pulsewidth`, `stop`).

## Wiring

Default logical-to-physical pin mapping (see `PIN_MAP` in `src/main.cpp`):

| BrachioGraph pin | ESP32-S3 GPIO | Purpose          |
|------------------|---------------|------------------|
| 14               | GPIO 1        | shoulder servo   |
| 15               | GPIO 2        | elbow servo      |
| 18               | GPIO 3        | pen-lift servo   |

Power the servos from an **external 5 V supply** (≥ 2 A). Tie its GND to
the ESP32 GND. Do not feed servos from the board's USB 5 V pin.

## Build & flash

```sh
pio run -t upload
pio device monitor -b 921600
```

The board enumerates as native USB-CDC: `/dev/ttyACM*` on Linux,
`/dev/cu.usbmodem*` on macOS — no driver required.

## Protocol

Line-based ASCII, one command per `\n`-terminated line:

| Command            | Effect                                        | Reply        |
|--------------------|-----------------------------------------------|--------------|
| `S <pin> <us>`     | set servo pulse-width (`us=0` detaches)       | —            |
| `F <pin> <hz>`     | set PWM frequency (accepted, fixed at 50 Hz)  | —            |
| `G <pin>`          | get last commanded pulse-width                | `<us>\n`     |
| `P`                | ping                                          | `OK\n`       |
| `V`                | version                                       | `ESPPIO 1\n` |
