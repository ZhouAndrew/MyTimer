
# ✅ 待实现功能清单：支持 CLI 实时更新与自动响铃

### 进度
所有列出的任务均已在仓库代码中实现，故该 TASK 已完成。

## 📌 问题描述

当前 CLI 工具中：

* `tick` 命令只能手动触发，服务器不自动推进计时器。
* `list` 显示信息，但客户端无法自动获取更新。
* 计时器结束后无任何响铃提示或通知，体验不完整。

这与项目计划中**跨端同步、通知推送、自动控制**的目标不符。

---

## 🛠️ 待实现任务清单（供 Codex 实现）

### 1. **WebSocket 通知模块**

#### 🔧 服务端任务

* [x] 创建 `WebSocketManager` 类用于管理所有客户端连接。
* [x] 为 `TimerManager` 添加 `on_tick`、`on_finish` 回调注册机制。
* [x] 每次 tick 或计时器结束时广播当前状态到客户端。
* [x] 消息格式建议使用：

  ```json
  {
    "type": "update",
    "timer_id": "1",
    "remaining": 3.0,
    "finished": false
  }
  ```

#### 🧪 示例代码接口

```python
await websocket.send_json({
    "type": "update",
    "timer_id": timer_id,
    "remaining": timer.remaining,
    "finished": timer.finished
})
```

---

### 2. **CLI 客户端主动响铃支持**

#### 🎯 功能要求

* [x] CLI 模式中每次 `tick` 后判断计时器是否结束。
* [x] 如果结束，自动响铃（终端响铃或系统音效）。
* [x] 提供配置选项决定是否播放音效（例如 `~/.timercli/config.json`）。

#### 🔔 方案建议

* 简易响铃：

  ```python
  print('\a')  # 终端响铃
  ```
* 使用系统命令播放音效：

  ```python
  import os
  os.system("aplay alarm.wav")  # Linux 示例
  ```

---

### 3. **支持自动 tick 模式（服务端或 CLI）**

#### 🕒 功能说明

* [x] 服务端可启动自动 tick 计时器（每秒递减）。
* [x] 或 CLI 客户端支持后台自动 tick。
* [x] 可设定 tick 周期（默认每秒）与启停控制。

---

## 📎 建议模块结构

```
mytimer/
├── server/
│   ├── timer_manager.py
│   ├── websocket_manager.py  ← ✅ 新增
│   ├── notifier.py           ← ✅ 可选：统一 tick 检查与响铃广播
├── tools/
│   └── manage.py             ← ✅ CLI 入口，加入响铃与轮询逻辑
```

---

## 🔚 目标结果

* CLI 工具能够在不依赖用户主动 `list` 的情况下实时获取更新。
* 倒计时结束后 CLI 能发出提示音或终端响铃。
* 为日后 Web/桌面/移动端客户端提供统一通知接口。


