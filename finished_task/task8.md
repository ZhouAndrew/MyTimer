# Task 8 Verification

The Qt GUI, local sound server and timestamp based architecture were implemented for Task 8. During review I found two issues:

1. `start_at` was not updated when timers were paused or resumed. Clients computing remaining time using the timestamp would show incorrect values after resuming. The pause/resume methods (and their batch variants) now clear or reset `start_at` so resumed timers use the current time.
2. The tray icon object created in `qt_client.main` had no reference, allowing it to be garbage collected. A persistent reference is now stored on the Qt application.

A regression test covering the `start_at` logic was added and all tests pass.
