# Task 8C: Refactor Server for Client-Pull Architecture

## Objective
Change how timers are handled so clients compute when to ring instead of the server pushing ring commands.

## Tasks
- [ ] Modify server timer model to include:
  - [ ] `start_at` (timestamp)
  - [ ] `duration` (seconds)
- [ ] Remove server → client ring mechanism
- [ ] Clients should compute remaining time:
  ```python
  remaining = max(0, duration - (now - start_at))
  ```
- [ ] Clients check for `remaining == 0` and trigger sound locally via POST to `/ring`
