# Phase 10 — Final Pi deployment + real-world testing

**Est. 10–15 hrs** · See [../PLAN.md](../PLAN.md) for overall architecture and progress log.

## Goal
Take the fully working Pi build (Phases 8–9) from "works on a desk" to "mounted, unattended,
survives a reboot, runs 24x7" — the last mile before this is a real installed device rather than
a dev setup.

## Task breakdown

1. Decide and build physical mounting (entryway-facing camera angle, sensor placement) — informed
   by whatever case/mounting plan the user has for the physical Pi unit.
2. **Auto-start on boot**: write a `systemd` unit (`deploy/recogcore.service`) that starts the
   Python service (`recogcore run`) and the Node backend on boot, restarts on crash
   (`Restart=on-failure`), and waits for network/audio devices to be ready before starting.
3. Ensure both services log to a persistent location (`data/logs/` or `journalctl` via systemd)
   with log rotation configured, since this will run unattended for long stretches and someone
   needs to be able to debug it after the fact without SSH-ing in at the moment of a failure.
4. **24x7 stability testing**: run the deployed unit continuously for several days, watching for
   memory growth, crashes, or degraded recognition accuracy over time (e.g. from camera lens
   condensation, temperature drift affecting the sensor from Phase 9) — log findings here or in
   a `docs/pi-setup.md` troubleshooting section.
5. **Power/thermal check**: monitor Pi CPU temperature under sustained load (recognition +
   conversation cycles), confirm it stays within safe operating range with the chosen
   case/mounting (add a heatsink/fan if not); confirm the power adapter is sufficient under peak
   load (camera + audio + Wi-Fi + occasional LLM API calls if `conversation.mode: llm`).
6. **Reboot resilience test**: power-cycle the Pi (simulating a power outage) and confirm the
   `systemd` services come back up cleanly and reconnect to MySQL without manual intervention.
7. **Network resilience**: test behavior when Wi-Fi drops temporarily — recognition/greeting
   (fully local) should keep working; only the LLM conversation path (Phase 4) and dashboard
   (Phase 7, if accessed remotely) should degrade, and should degrade gracefully (per the
   fail-soft backend handling built in Phase 6) rather than crashing the whole service.
8. Final documentation pass: update root `README.md` and `docs/pi-setup.md` with the complete,
   final install/deploy instructions reflecting anything learned during this phase, so a fresh
   Pi + fresh clone of the repo can go from empty SD card to running assistant by following the
   docs alone — this is the real test of the "anyone can install and use this" open-source goal
   from `PLAN.md`.

## File/folder layout created by this phase

```
robot-assistant/
└── deploy/
    ├── recogcore.service          # systemd unit, Python service
    └── recogcore-backend.service  # systemd unit, Node backend
```
