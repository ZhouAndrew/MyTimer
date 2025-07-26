# Task 7: Fix TUI Timer Creation and Enable Timestamp-Based Logic

## Goal
Ensure TUI timer creation works fully and switch the timer system to timestamp-based logic to eliminate server-driven ticking.

---

## Part 1: Fix TUI Timer Creation

- [x] In `view_layer.py`, ensure `[c]` keybinding opens an input prompt (via `Prompt.ask` or similar).
- [x] Prompt for at least `duration` (in seconds) and optionally `tag`.
- [x] Send a POST request to the server's timer creation API (`/timers` or equivalent).
- [x] Refresh the view to show the new timer immediately.
- [x] Confirm timer appears and starts ticking when `start_at` is set.

---

## Part 2: Migrate Timer Logic to Timestamp-Based Model

### Server-Side (`timer_manager.py`, API)

- [ ] When creating a timer:
  - Store `created_at = now`
  - Store `start_at = now` if not paused
  - Store `duration` in seconds
- [ ] Remove dependence on `.tick()` for timer state changes.
- [ ] Retain `/tick` route for compatibility (no-op or logs only).
- [ ] On timer listing/response, do **not** serialize `remaining` directly — it should be computed by the client.

### Client-Side (CLI + TUI)

- [ ] Derive `remaining = max(0, duration - (now - start_at))` if `start_at` is set.
- [ ] Display `status = finished` when `remaining == 0`
- [ ] Fall back to default logic if `start_at` is missing (for legacy).

---

## Part 3: Testing & Verification

- [ ] Create a timer via TUI and confirm it starts ticking in the dashboard.
- [ ] Verify `list` in CLI returns `remaining` decreasing over time.
- [ ] Stop and restart the server, confirm `remaining` is preserved via timestamps.
- [ ] Remove reliance on tick mutation — `POST /tick?...` can be deprecated.
- [ ] Confirm no error or crash in local mode if server is unreachable.

---

## Optional

- [ ] Add debug logs in server: log `start_at`, `remaining`, `finished` for each timer.
- [ ] Add unit tests for client-side `remaining` computation.
