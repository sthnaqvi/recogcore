# Phase 6 — End-to-end integration + testing on Mac

**Est. 15–20 hrs** · See [../PLAN.md](../PLAN.md) for overall architecture and progress log.

## Goal
Wire every previous phase into one running loop — camera → recognize → greet → converse → log —
and harden it against the edge cases that only show up once everything runs together
continuously, not in isolated phase-by-phase testing.

## Task breakdown

1. Write `recog_core/main_loop.py`: the top-level orchestrator that owns the `HardwareProvider`
   instance and drives, per frame/cycle: detect (Phase 1) → recognize (Phase 2) → greeting
   decision incl. cooldown (Phase 3) → conversation turn if triggered (Phase 4) → event logging
   (Phase 5). This replaces the ad-hoc per-phase test scripts as the real entry point
   (`recogcore run`).
2. Add a top-level state machine per tracked person (idle → detected → greeted → conversing →
   idle) instead of letting greeting/conversation/logging each independently guess state from
   timestamps — consolidates the cooldown/entry/exit logic from Phases 3 and 5 into one place so
   they can't drift out of sync with each other.
3. **Multiple faces in frame**: decide and implement a policy — e.g. process the largest/closest
   face for conversation (only one conversation at a time), but still log `detected` events for
   every recognized face in frame. Test with 2+ people in view simultaneously.
4. **Poor lighting**: test in dim room lighting and backlit conditions; confirm the system
   degrades gracefully (more "unknown" classifications or no detections) rather than
   crashing or producing wildly wrong confident matches — tune the Phase 2 threshold further if
   needed now that real conditions are being tested, not just the earlier isolated tuning pass.
5. **False positives**: deliberately test with photos-of-a-person held up to camera, similar-
   looking family members, and non-face objects, to see how the detector/recognizer combination
   holds up; document known failure modes in this file's notes rather than silently accepting
   them.
6. **Config toggle testing**: systematically test `CAMERA_ENABLED=false`, `MIC_ENABLED=false`,
   `SPEAKER_ENABLED=false` (and combinations) — confirm the main loop degrades sensibly (e.g.
   mic-off means greetings still work but no conversation; camera-off means no detection loop
   runs at all) rather than crashing on a `None` provider.
7. **Backend availability**: test the main loop's behavior when the Node backend is down/
   unreachable — logging calls should fail soft (log a local warning, don't crash the whole
   assistant) rather than taking down the recognition/greeting/conversation experience.
8. **Long-running stability**: run the full loop unattended for an extended period (an hour+)
   watching for memory growth (camera frame buffers, audio buffers not being released) or
   resource leaks (file handles from repeated snapshot writes) — this is the Mac-side proxy for
   the eventual Pi 24x7 requirement in Phase 10.
9. Add structured logging (Python `logging` module, not just prints) across the main loop so
   issues found during this phase's testing are actually diagnosable — separate log
   levels/streams for recognition events vs conversation vs errors.
10. Write an integration test (`tests/test_main_loop.py`) that runs the loop against fixture
    camera frames/audio (not live hardware) through a fake `HardwareProvider`, asserting the
    full pipeline produces the expected sequence of greeting/logging calls — this is what
    catches regressions in later phases without needing a human in front of the camera every time.

## File/folder layout created by this phase

```
python-service/
├── tests/
│   ├── test_main_loop.py
│   └── fixtures/
│       └── fake_provider.py       # test double implementing HardwareProvider
└── recog_core/
    ├── main_loop.py
    └── state_machine.py            # per-person idle/detected/greeted/conversing state
```
