### **Complete To-Do List for Codex:**

#### **1. Server-side Tasks:**
- [ ] Implement WebSocket notification system for real-time updates.
- [ ] Enable WebSocket client subscriptions to server updates.
- [ ] Add batch operations (Pause All, Delete All, Reset All timers).
- [ ] Add support for persistent timer states (JSON/SQLite).
- [ ] Implement timer state recovery after service restart.
- [ ] Create REST API endpoints to control timers (`/timers/pause_all`, `/timers/reset_all`).
- [ ] Enhance API with status queries (active timers, server status).
- [ ] Implement custom notification types (system notifications, sound alerts, etc.).

#### **2. Client-side Tasks:**
- **CLI Client**:
  - [ ] Add real-time command hints and spelling suggestions.
  - [ ] Support `pause/resume/remove all` functionality.
  - [ ] Allow clearing or resetting all timers.
  - [ ] Implement command history/autocompletion.
  - [ ] Provide system sound or terminal bell for notifications.

- **TUI Client**:
  - [ ] Add automatic refresh of the timer list (using WebSocket or scheduled fetch).
  - [ ] Implement support for user actions on selected timers (pause/resume/delete).
  - [ ] Display server status and connection info.

#### **3. Synchronization and Real-time Updates:**
- [ ] Implement synchronization between multiple clients using WebSocket.
- [ ] Ensure timers across different platforms (CLI, TUI, Web) stay synchronized.
- [ ] Handle disconnections and reconnections smoothly with state resynchronization.

#### **4. Timer Ringing and Notifications:**
- [ ] Add support for automatic ringing when the timer completes (CLI and TUI).
- [ ] Allow users to configure sound effects or use terminal bell for alerts.
- [ ] Enable system-wide notifications (e.g., using `notify-send` or `plyer`).
