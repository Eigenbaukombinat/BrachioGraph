// ESPpio firmware
// ----------------
// Receives a tiny line-based ASCII protocol over USB-CDC and drives fixed
// LEDC hardware-PWM channels accordingly.
//
// Protocol (one command per line, terminated with '\n'):
//   S <pin> <us>      set servo pulse-width in microseconds (us=0 detaches)
//   F <pin> <hz>      set PWM frequency (accepted, currently fixed at 50 Hz)
//   G <pin>           get last commanded pulse-width  -> reply: "<us>\n"
//   P                 ping                            -> reply: "OK\n"
//   V                 version                         -> reply: "ESPPIO 2 LEDC\n"
//   D                 debug mapping/state             -> one-line state dump
//
// <pin> is the *logical* pin number used by the host (matching the BCM pin
// numbers BrachioGraph historically used: 14, 15, 18). The firmware maps
// these to physical ESP32-S3 GPIOs via PIN_MAP below.
//
// Fire-and-forget: S and F return nothing, so the host never blocks.
// Lines longer than LINE_BUF or unknown commands are silently dropped.

#include <Arduino.h>

// --------------------------------------------------------------------------
// Configuration
// --------------------------------------------------------------------------

// Map host-side logical pins (left) to physical ESP32-S3 GPIOs (right).
// Adjust to match your wiring. GPIO 1/2/3 are safe defaults on the S3-Mini.
struct PinMap {
    int logical;
    int gpio;
    int channel;
};

static const PinMap PIN_MAP[] = {
    {14, 4, 0},   // shoulder servo
    {15, 5, 2},   // elbow servo
    {18, 6, 4},   // pen-lift servo
};
static const size_t PIN_MAP_LEN = sizeof(PIN_MAP) / sizeof(PIN_MAP[0]);

static const int  SERVO_MIN_US   = 400;
static const int  SERVO_MAX_US   = 2600;
static const int  SERVO_FREQ_HZ  = 50;
static const int  SERVO_PERIOD_US = 1000000 / SERVO_FREQ_HZ;
static const int  LEDC_BITS       = 14;
static const int  LEDC_MAX_DUTY   = (1 << LEDC_BITS) - 1;
static const size_t LINE_BUF     = 64;

// --------------------------------------------------------------------------
// State
// --------------------------------------------------------------------------

struct ServoSlot {
    int    logical = -1;
    int    gpio    = -1;
    int    channel = -1;
    int    last_us = 0;
    bool   attached = false;
};

static ServoSlot slots[PIN_MAP_LEN];

static char   line_buf[LINE_BUF];
static size_t line_len = 0;

// --------------------------------------------------------------------------
// Helpers
// --------------------------------------------------------------------------

static ServoSlot* slot_for(int logical_pin) {
    for (size_t i = 0; i < PIN_MAP_LEN; ++i) {
        if (slots[i].logical == logical_pin) {
            return &slots[i];
        }
    }
    return nullptr;
}

static uint32_t pulse_to_duty(int pulse_us) {
    return (uint32_t)((uint64_t)pulse_us * LEDC_MAX_DUTY / SERVO_PERIOD_US);
}

static void attach_slot(ServoSlot* s) {
    if (s->attached) return;

    ledcSetup(s->channel, SERVO_FREQ_HZ, LEDC_BITS);
    ledcAttachPin(s->gpio, s->channel);
    s->attached = true;
}

static void cmd_set_servo(int logical_pin, int pulse_us) {
    ServoSlot* s = slot_for(logical_pin);
    if (!s) return;

    if (pulse_us == 0) {
        if (s->attached) {
            ledcWrite(s->channel, 0);
            ledcDetachPin(s->gpio);
            s->attached = false;
        }
        s->last_us = 0;
        return;
    }

    if (pulse_us < SERVO_MIN_US) pulse_us = SERVO_MIN_US;
    if (pulse_us > SERVO_MAX_US) pulse_us = SERVO_MAX_US;

    attach_slot(s);
    ledcWrite(s->channel, pulse_to_duty(pulse_us));
    s->last_us = pulse_us;
}

static void cmd_get_servo(int logical_pin) {
    ServoSlot* s = slot_for(logical_pin);
    Serial.printf("%d\n", s ? s->last_us : 0);
}

static void cmd_debug() {
    Serial.print("MAP");
    for (size_t i = 0; i < PIN_MAP_LEN; ++i) {
        Serial.printf(
            " %d:g%d:c%d:%d:%d",
            slots[i].logical,
            slots[i].gpio,
            slots[i].channel,
            slots[i].last_us,
            slots[i].attached ? 1 : 0
        );
    }
    Serial.print("\n");
}

static void handle_line(char* line) {
    // strip CR
    char* cr = strchr(line, '\r');
    if (cr) *cr = '\0';
    if (line[0] == '\0') return;

    char cmd = line[0];
    switch (cmd) {
        case 'S': {
            int pin = 0, us = 0;
            if (sscanf(line + 1, "%d %d", &pin, &us) == 2) {
                cmd_set_servo(pin, us);
            }
            break;
        }
        case 'F': {
            // Frequency is fixed at 50 Hz for servo use; accept silently.
            break;
        }
        case 'G': {
            int pin = 0;
            if (sscanf(line + 1, "%d", &pin) == 1) {
                cmd_get_servo(pin);
            }
            break;
        }
        case 'P':
            Serial.print("OK\n");
            break;
        case 'V':
            Serial.print("ESPPIO 2 LEDC\n");
            break;
        case 'D':
            cmd_debug();
            break;
        default:
            // unknown -> ignore
            break;
    }
}

// --------------------------------------------------------------------------
// Arduino entry points
// --------------------------------------------------------------------------

void setup() {
    Serial.begin(921600);   // baudrate is ignored over native USB-CDC

    for (size_t i = 0; i < PIN_MAP_LEN; ++i) {
        slots[i].logical = PIN_MAP[i].logical;
        slots[i].gpio    = PIN_MAP[i].gpio;
        slots[i].channel = PIN_MAP[i].channel;
    }
}

void loop() {
    while (Serial.available()) {
        int c = Serial.read();
        if (c < 0) break;
        if (c == '\n') {
            line_buf[line_len] = '\0';
            handle_line(line_buf);
            line_len = 0;
        } else if (line_len < LINE_BUF - 1) {
            line_buf[line_len++] = (char)c;
        } else {
            // overflow: reset buffer, drop line
            line_len = 0;
        }
    }
}
