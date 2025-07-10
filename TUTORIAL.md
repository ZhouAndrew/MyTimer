# MyTimer 教程
[项目概览](README.md) | [开发进度](ROADMAP.md) | [进度中文版](ROADMAP.zh.md)


[项目概览](README.md) | [开发进度](ROADMAP.md) | [进度中文版](ROADMAP.zh.md)



本教程将介绍如何运行本仓库提供的倒计时管理示例，以及各模块的基本交互流程。

## 环境准备

1. 安装依赖（或使用 `python tools/manage.py install`）：
   ```bash
   pip install -r requirements.txt
   ```
2. 更新依赖（可选，或使用 `python tools/manage.py update`）：
    ```bash
    pip install -U -r requirements.txt
    ```
    `update` 命令仅用于更新依赖。如需获得最新的程序代码，请执行 `git pull` 或重新下载仓库。
3. 运行单元测试确保环境正常（或使用 `python tools/manage.py test`）：
   ```bash
   pytest -q
   ```

## 启动 API 服务

`mytimer/server/api.py` 使用 FastAPI 实现 REST 与 WebSocket 接口，可通过以下命令启动：

```bash
uvicorn mytimer.server.api:app --reload
```
或执行
```bash
python tools/manage.py start
```

默认情况下，服务监听在 `http://127.0.0.1:8000`。若要关闭服务器，可以运行 `python tools/manage.py stop`。您可以使用 `curl` 或任何支持 HTTP 的工具与之交互。

### 创建计时器

```bash
curl -X POST 'http://127.0.0.1:8000/timers?duration=5'
```

此接口会返回新建计时器的 `timer_id`。随后可通过 `/timers/{timer_id}/pause`、`/resume` 等接口控制计时器。

### WebSocket 更新

建立 WebSocket 连接：

```bash
websocat ws://127.0.0.1:8000/ws
```

每当计时器状态变化时，服务器会向所有连接推送 JSON 数据，方便客户端实时更新显示。

## 发现局域网服务器

`tools/server_discovery.py` 提供了一个简单的 UDP 广播实现，用于在局域网中寻找服务器：

```bash
python -m tools.server_discovery
```

脚本将发送广播并在指定超时时间内等待回应，若发现服务器地址，会打印在终端。配合 `tools/mock_server.py` 可以在本地模拟测试。

## 启动 CLI 客户端

交互式方式：
```bash
python -m mytimer.client.controller interactive
```
进入交互模式后，可输入 `help` 查看所有支持的命令，使用 `quit` 退出。

图形界面：
```bash
python -m mytimer.client.tui_app
```
默认使用 WebSocket 与服务器保持同步，可通过 `--no-ws` 改为轮询模式：
```bash
python -m mytimer.client.tui_app --no-ws
```

## 计时器管理逻辑

`TimerManager` 维护多个计时器对象，每次调用 `tick` 时推进所有计时器的剩余时间。计时器结束时会自动停止运行。您可以根据需要扩展计时器完成后的通知逻辑。

## 关键文档字符串摘录

为了快速了解代码结构，以下列出部分核心类与方法的 Docstring：

### `mytimer/core/timer_manager.py`

```python
class Timer:
    """Simple countdown timer."""

class TimerManager:
    """Manage multiple :class:`Timer` instances."""

    def create_timer(self, duration: float) -> int:
        """Create a new timer and return its identifier."""

    def tick(self, seconds: float) -> None:
        """Advance all managed timers."""
```

### `mytimer/core/notifier.py`

```python
class Notifier:
    """Monitor a :class:`TimerManager` and invoke a callback on timer completion."""

    async def start(self, interval: float = 1.0) -> None:
        """Start monitoring timers."""

    async def stop(self) -> None:
        """Stop monitoring timers."""
```

### `mytimer/client/sync_service.py`

```python
class SyncService:
    """Maintain WebSocket sync with the API server and expose REST helpers."""
```

## 结语

以上即为 MyTimer 的基本使用方式。阅读源码和 Docstring 可以获取更深入的实现细节。

更多信息参见 [README](README.md) 与 [ROADMAP](ROADMAP.md)。
