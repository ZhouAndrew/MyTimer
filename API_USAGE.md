# MyTimer API Usage

This guide shows how to interact with the MyTimer server from Python or web clients. The server exposes simple REST endpoints and a WebSocket for real-time updates.

## Starting the Server

Start the API server (defaults to `http://127.0.0.1:8000`):

```bash
uvicorn mytimer.server.api:app --reload
```

## REST Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/timers?duration=<seconds>` | Create a new timer. |
| `GET` | `/timers` | List all timers and their states. |
| `POST` | `/timers/{timer_id}/pause` | Pause a running timer. |
| `POST` | `/timers/{timer_id}/resume` | Resume a paused timer. |
| `DELETE` | `/timers/{timer_id}` | Remove a timer. |
| `DELETE` | `/timers` | Remove all timers. |
| `POST` | `/timers/pause_all` | Pause all timers. |
| `POST` | `/timers/resume_all` | Resume all timers. |
| `POST` | `/timers/reset_all` | Reset all timers to their initial durations. |
| `POST` | `/tick?seconds=<sec>` | Manually advance all timers. |
| `GET` | `/status` | Get basic server status. |
| `WS` | `/ws` | WebSocket endpoint for real-time updates. |

## Example: Python Client

```python
import requests

BASE_URL = "http://127.0.0.1:8000"

# Create a 5 second timer
resp = requests.post(f"{BASE_URL}/timers", params={"duration": 5})
timer_id = resp.json()["timer_id"]

# Pause the timer
requests.post(f"{BASE_URL}/timers/{timer_id}/pause")

# Resume the timer
requests.post(f"{BASE_URL}/timers/{timer_id}/resume")

# List all timers
print(requests.get(f"{BASE_URL}/timers").json())
```

## Example: Web Requests

Using `curl`:

```bash
# Create a 5 second timer
curl -X POST "http://127.0.0.1:8000/timers?duration=5"

# List timers
curl "http://127.0.0.1:8000/timers"

# Pause a timer
curl -X POST "http://127.0.0.1:8000/timers/1/pause"
```

In JavaScript:

```javascript
// Create a timer
fetch("/timers?duration=5", { method: "POST" });

// Get timer list
fetch("/timers").then(r => r.json()).then(console.log);
```

## WebSocket Updates

```python
from websocket import create_connection

ws = create_connection("ws://127.0.0.1:8000/ws")
print(ws.recv())  # initial state
ws.close()
```

```javascript
const ws = new WebSocket("ws://127.0.0.1:8000/ws");
ws.onmessage = (event) => console.log(event.data);
```

The server broadcasts timer updates whenever timers are created, updated, or completed.

