# Phase 9 — Additional sensors

**Est. 12–18 hrs** · See [../PLAN.md](../PLAN.md) for overall architecture and progress log.

## Goal
Add a PIR motion sensor as a wake-trigger (so the Pi isn't continuously running face detection
on every frame, saving compute/power) and a temperature sensor, both via GPIO/I2C, extending the
`HardwareProvider` abstraction and the `person_events` schema rather than bolting on side logic.

## Task breakdown

1. Wire the PIR motion sensor to a Pi GPIO pin; verify raw signal reading with a minimal test
   script (`RPi.GPIO`/`gpiozero`) before integrating.
2. Extend the `HardwareProvider` interface (base class in `recog_core/hardware/base.py`) with an
   optional `wait_for_motion(timeout) -> bool` method; implement it for real in `PiProvider`
   (Phase 8) and as a no-op/always-true stub in `MacProvider` (Mac has no PIR sensor — the main
   loop should still run continuously there, motion-gating is Pi-only).
3. Update `recog_core/main_loop.py` (Phase 6): when running under `PiProvider` with motion
   gating enabled (config flag, e.g. `sensors.motion_gated_capture: true`), the loop blocks on
   `wait_for_motion()` before starting the camera capture/recognition cycle, instead of polling
   the camera continuously. This is the main compute/power saving this phase delivers.
4. Wire the temperature sensor (I2C, e.g. a common Pi-compatible sensor like a BME280/DHT22) via
   a small `recog_core/sensors/temperature.py` reader (`read_celsius() -> float`), independent of
   the `HardwareProvider` camera/audio interface since it's a different concern (ambient
   telemetry, not capture I/O).
5. Extend the MySQL schema (Phase 5) with a new table rather than overloading `person_events`:
   ```sql
   CREATE TABLE sensor_readings (
     id INT AUTO_INCREMENT PRIMARY KEY,
     sensor_type ENUM('temperature', 'motion'),
     value FLOAT,
     timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
   );
   ```
   as `backend/migrations/002_create_sensor_readings.sql`.
6. Add `POST /api/sensor-readings` to `backend/src/routes/` (mirrors the `events.js` pattern from
   Phase 5) and a matching Python-side client method in `logging_client.py`.
7. Periodically log temperature (e.g. every N minutes, config-driven) from the main loop or a
   small background scheduler — independent of the motion/recognition cycle.
8. Log motion-trigger events themselves (`sensor_type: motion`) alongside person recognition
   events, so the dashboard (Phase 7) can later show "motion detected but no face recognized"
   cases (e.g. pets, or someone standing off-camera).
9. Tests: mock GPIO/I2C reads (these can't run in CI without real hardware) — test the
   motion-gating control flow in `main_loop.py` with a fake `wait_for_motion` and the temperature
   logging cadence logic, not the actual sensor hardware.
10. Manual verification on the Pi: confirm the camera/recognition cycle only activates after
    motion is detected, measure idle power draw before/after this change if possible, and confirm
    temperature readings land in `sensor_readings` at the configured interval.

## File/folder layout created by this phase

```
backend/
└── migrations/
    └── 002_create_sensor_readings.sql

python-service/
├── tests/
│   └── test_motion_gating.py
└── recog_core/
    └── sensors/
        ├── __init__.py
        └── temperature.py
```
