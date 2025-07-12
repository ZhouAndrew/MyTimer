# ✅ MyTimer 项目待修复功能清单（可并行）

### 进度
所有列出的任务均已在仓库代码中实现，故该 TASK 已完成。

## 🐛 1. CLI 功能改进

- [x] **修复 `tick` 命令无参数报错不明确的问题**
  - 📄 文件：`mytimer/client/controller.py`
  - 🧪 现象：`tick` 输入无参数时报错 `"Unknown command"`
  - ✅ 目标：改为提示 `"Usage: tick <seconds>"`
  - 💡 建议实现：
    ```python
    elif cmd == "tick":
        if len(args) == 1:
            tick(base_url, float(args[0]))
        else:
            print("Usage: tick <seconds>")
    ```

---

## 🐛 2. TUI 用户体验优化

- [x] **退出时清除屏幕**
  - 📄 文件：`mytimer/client/tui.py`
  - 🧪 现象：退出后终端残留 UI 残影
  - ✅ 目标：退出前清除终端内容
  - 💡 建议实现：
    ```python
    import os
    ...
    finally:
        os.system('clear')
    ```

- [x] **增加自动刷新剩余时间功能**
  - 📄 文件：`mytimer/client/tui.py`
  - 🧪 现象：Timer 状态需手动 tick 更新
  - ✅ 目标：自动每秒刷新状态显示
  - 💡 建议实现：
    - 在主循环中加入 `asyncio.sleep(1)` 或线程定时器；
    - 或轮询 REST API 的状态接口。

---

## ⚙️ 3. TUI 多重启动保护

- [x] **防止多开 TUI 导致终端输出堆叠**
  - 📄 文件：`tools/manage.py` 或 `tui.py`
  - 🧪 现象：运行多个 TUI 时终端残影严重
  - ✅ 目标：仅允许一个 TUI 实例运行
  - 💡 建议实现：
    - 使用 lockfile 或检查是否已存在 PID；
    - 或在启动时检查并提醒已有运行实例。

---

## 📦 4. 功能测试与回归验证

- [x] **补充 CLI 单元测试**
  - 📄 文件：`tests/test_cli.py`
  - ✅ 测试项：
    - [x] `tick` 无参数提示 `"Usage"`
    - [x] `tick 3.0` 正常推进倒计时
    - [x] 多次启动 TUI 后是否清屏
    - [x] Timer 是否能自动减少剩余时间
    - [x] CLI 与 TUI 对 `tick` 状态一致性验证

---

## 🔍 5. 可选优化项（延后）

- [x] **支持 WebSocket 推送实时刷新（替代轮询）**
  - 📄 文件：`server.py`, `tui.py` 等
  - ✅ 目标：服务端推送 timer 更新给 TUI
  - 💡 技术建议：
    - 使用 FastAPI 的 WebSocket 广播
    - 客户端使用 `websocket-client` 接收事件
    - 仅当用户启用自动刷新时建立连接

---

## 📁 文件变更汇总

| 文件路径                    | 修改内容                    |
|-----------------------------|-----------------------------|
| `mytimer/client/controller.py` | 修复 `tick` 无参数处理         |
| `mytimer/client/tui.py`        | 添加自动刷新、退出清屏逻辑     |
| `tools/manage.py`             | 添加 TUI 多开检测（可选）      |
| `tests/test_cli.py`           | 添加相关功能测试             |
