# MyTimer

**‼️ NOTE: This is the actual, authoritative plan and requirement for the program.**  
The document may contain inconsistencies, as it is derived from this plan.  
📌 Refer to `task/task{n}.md` for the most up-to-date and accurate tasks.

> 🚧 当前文档仅供参考，真实计划与需求以 `task/task{n}.md`与`README.md`中为准。请开发和实现过程中优先参考代码任务。非管理员不得修改`README.md`


[项目进度](ROADMAP.md) | [Project Progress 中文版](ROADMAP.zh.md) | [详细教程](TUTORIAL.md)

## 📋 项目概览

- **项目目标**：构建一个可跨设备同步的倒计时管理系统，支持远程控制、通知推送、实时更新和设置同步。
- **系统组成**：服务器 + 多客户端（桌面/Web/移动），通过网络通信保持状态同步。

## 🚀 快速开始

1. 安装依赖并运行测试（也可以使用下方的管理脚本）：
   ```bash
   pip install -r requirements.txt
   pytest -q
   ```
   或执行
   ```bash
   git pull 
   python tools/manage.py install
   python tools/manage.py test
   ```
3. 更新
   ```bash
   python tools/manage.py update
   python tools/manage.py test
   ```
2. 启动服务器（或使用 `python tools/manage.py start`）：
   ```bash
   uvicorn mytimer.server.api:app --reload
   ```
   启动后可使用 `python tools/manage.py log` 查看后台输出。
3. 启动交互式客户端：
```bash
python -m mytimer.client.controller interactive
```
交互界面下输入 `help` 可查看所有命令，`quit` 退出。
或使用图形界面：
```bash
python -m mytimer.client.tui_app
```
或启动桌面版 Qt GUI：
```bash
python -m qt_client
```

---

## ✅ 主要模块与职责（支持并行开发）

| 模块名称              | 类型     | 功能说明                                               | 可并行 | 依赖           | 完成情况 |
|---------------------|----------|--------------------------------------------------------|--------|----------------|----------|
| 🧠 TimerManager     | Server  | 管理计时器对象，提供创建、更新、删除、倒计时与状态检测功能            | ✅     | 无             | ✅ |
| 🌐 APIServer        | Server  | 提供 REST API 和 WebSocket 接口                        | ✅     | TimerManager   | ✅ |
| 🔔 Notifier         | Server  | 监控倒计时到期状态并执行通知推送                         | ✅     | TimerManager   | ✅ |
| 👤 ClientAuth       | Server  | 客户端鉴权模块，识别设备ID或Token                       | ✅     | APIServer      | ✅ |
| 🖼️ ClientViewLayer | Client  | 客户端主界面，显示计时器列表与状态、标签、剩余时间等信息         | ✅     | SyncService    | ✅ |
| 🎮 ClientController | Client  | 接收用户操作指令并通过 API 向服务器发送请求                    | ✅     | APIServer      | ✅ |
| ⚙️ ClientSettings   | Client  | 设置面板：铃声、通知选项、导入导出配置、本地缓存                    | ✅     | 本地数据        | ✅ |
| 🔁 SyncService      | Client  | 与服务器保持 WebSocket 同步、REST 接口控制                      | ✅     | Server API     | ✅ |
| 🧭 ServerDiscovery  | Client  | 自动发现局域网服务器，展示服务器连接状态                      | ✅     | 无             | ✅ |
完成情况说明：✅ 已完成，❌ 未完成

---
## ✅ CLI 图形界面模块与职责（支持并行开发）

| 模块名称             | 类型    | 功能说明                                      | 可并行 | 依赖                  | 完成情况 |
|--------------------|---------|-------------------------------------------|--------|---------------------|----------|
| 🖥️ TUIApp          | Client | 负责启动 Rich/Textual 应用并管理界面布局与事件循环 | ✅     | CLIViewLayer, InputHandler | ✅ |
| 📊 CLIViewLayer    | Client | 使用表格和面板渲染计时器列表与状态  | ✅     | SyncService        | ✅ |
| ⌨️ InputHandler    | Client | 解析键盘输入，映射为计时器的控制指令 | ✅     | SyncService        | ✅ |
| 🔧 CLISettings     | Client | 提供终端设置菜单，保存主题和服务器地址等配置         | ✅     | 本地数据              | ❌ |
| 🔔 TUINotifier     | Client | 在终端显示提醒，并可调用系统通知                 | ✅     | TimerManager       | ✅ |

### 🗺️ CLI 开发路线图

| 周数     | 目标内容                                   |
|--------|---------------------------------------|
| 第 1 周  | 搭建 TUIApp 框架，能显示计时器表格                   |
| 第 2 周  | 完成键盘控制逻辑，集成 SyncService 实时同步            |
| 第 3 周  | 加入设置菜单和通知功能，优化界面交互                  |
| 第 4 周  | 整理文档与测试，准备发布                             |

---

## ✅ Qt 桌面客户端模块

| 模块名称        | 类型    | 功能说明                             | 可并行 | 依赖            | 完成情况 |
|---------------|-------|------------------------------------|------|---------------|------|
| 🪟 MainWindow | Client | Qt 主窗口，显示计时器表格与状态        | ✅   | NetworkClient | ✅ |
| 🖱️ TrayIcon   | Client | 系统托盘图标，提供显示/隐藏、添加计时器等 | ✅   | MainWindow    | ✅ |
| 🌐 NetworkClient | Client | 轮询服务器获取计时器信息               | ✅   | requests       | ✅ |
| 🔊 SoundClient | Client | 向本地声音服务器发送播放指令            | ✅   | requests       | ✅ |

---

## 📌 项目开发阶段与任务划分

### 🚀 第一阶段：核心服务开发（T0）

| 任务项                    | 模块              | 技术栈                          | 交付内容                             |
|-------------------------|-------------------|----------------------------------|------------------------------------|
| 计时器数据结构设计            | TimerManager      | Python                           | 支持创建/暂停/恢复/重置倒计时功能             |
| 本地定时器管理接口            | TimerManager      | Python                           | 支持多个计时器对象并发管理                     |
| API 设计与实现              | APIServer         | FastAPI                          | 提供 `/timers` `/status` `/notify` 等接口   |
| WebSocket 广播机制         | WebSocketServer   | FastAPI + WebSockets             | 客户端可实时接收倒计时更新与控制状态             |
| 通知模块                  | Notifier          | Python + 协程调度器                    | 倒计时到期后触发推送和服务器端通知                |

### 🎨 第二阶段：客户端功能实现（T1）

| 任务项                | 模块              | 技术栈                            | 交付内容                              |
|---------------------|-------------------|----------------------------------|-------------------------------------|
| 主界面 UI            | ViewLayer         | HTML/React 或 PyQt               | 计时器显示卡片、倒计时剩余时间、edit/save 等     |
| 控制逻辑              | Controller        | JavaScript / Python              | 用户操作事件发送请求至服务器                    |
| WebSocket 同步机制     | SyncService       | JS WebSocket / Python client     | 客户端能实时获取服务器的状态同步与更新              |
| 本地设置与缓存管理        | Settings          | localStorage / JSON / SQLite     | 设置项存储与导入导出、本地缓存倒计时状态              |
| 自动发现服务器功能        | ServerDiscovery   | UDP 广播 / mDNS                  | 自动检测局域网服务器并显示可连接状态信息             |

### 🔔 第三阶段：通知功能扩展（T2）

| 任务项            | 模块                         | 技术栈                               | 交付内容                      |
|-----------------|------------------------------|------------------------------------|-----------------------------|
| 通知选择界面         | Settings                     | Web UI / PyQt                      | 铃声选择、自定义文件路径              |
| 客户端播放音频功能      | 通知响应模块                      | HTML5 Audio / Qt Multimedia        | 计时器结束后自动播放铃声               |
| 后台通知机制         | ServiceWorker / OS 通知系统      | JS Notification API / `plyer` 等     | 后台消息通知栏提醒（桌面 / 移动端）     |

---

## 🧪 可选阶段：测试与调试优化（T3）

| 任务项              | 模块           | 工具建议                         | 目标说明                       |
|-------------------|----------------|----------------------------------|------------------------------|
| 单元测试              | TimerManager   | pytest                           | 计时器数据结构与状态机验证              |
| 接口自动测试           | APIServer      | Postman / HTTPie                 | 验证 API 响应、参数正确性              |
| WebSocket 状态模拟测试 | SyncService    | WebSocket mocking tools          | 验证网络断连恢复后状态一致性            |
| 多端一致性测试         | Client 全模块     | 多平台模拟器 / 手动测试                 | 多平台 UI + 状态同步一致性验证           |

---

## 📅 示例时间线（可并行开发）

| 周数     | 目标内容                                               |
|--------|-----------------------------------------------------|
| 第 1 周  | 搭建服务器核心模块（TimerManager + API + WebSocket）        |
| 第 2 周  | 搭建客户端原型 UI、实现设置界面及基础通信逻辑                   |
| 第 3 周  | 完善通知系统、自动发现服务器、实现本地缓存与配置导入导出功能         |
| 第 4 周  | 联调测试、修复跨端问题、完成部署打包与上线准备                     |

---

## 🔧 技术选型建议

| 模块            | 推荐技术                                    |
|----------------|--------------------------------------------|
| 服务器端          | FastAPI + asyncio + uvicorn               |
| WebSocket 支持   | FastAPI WebSocket 模块                    |
| 客户端（Web）    | React + Tailwind / Vue                    |
| 客户端（桌面）    | PyQt6 / Tkinter                           |
| 客户端（移动端）   | Flutter + PWA 支持                         |
| 本地存储          | JSON 配置文件 / SQLite                    |
| 通知实现          | Web Notification API / `plyer` / `notify-send` |

## 🧭 ServerDiscovery 模块示例

本仓库提供 `tools/server_discovery.py` 用于在局域网内自动发现服务端。示例的实现基于 UDP 广播：

```bash
# 终端 1：启动模拟服务器
python -m tools.mock_server

# 终端 2：运行发现脚本
python -m tools.server_discovery
```

脚本会在 3 秒内等待服务器响应，并打印发现的服务器 IP 地址；若未发现则输出 `No server found`。

## 📴 Local Mode

TUI 启动时若无法连接服务器，将自动进入本地模式，所有计时器状态会保存在
`~/.timercli/timers.json` 中。重新连上服务器后可手动同步。

`tools/test_discovery.py` 演示了如何在代码中启动模拟服务器并调用发现函数，可用于简单的功能测试。

## 📖 代码结构说明

- `mytimer/server/api.py`：FastAPI 服务端实现，提供计时器的 REST 接口和 WebSocket 广播。
- `mytimer/core/timer_manager.py`：内部计时器数据结构与管理逻辑。
- `mytimer/core/notifier.py`：监控計時器完成並執行自定義回調通知。
- `tools/server_discovery.py`：通过 UDP 广播发现局域网内的服务器。
- `tools/mock_server.py`：配合发现脚本使用的简易 UDP 模拟服务器。
- `tests/`：pytest 单元测试，覆盖 API 与计时器管理逻辑。

代码中已加入详细的 Docstring，阅读源码即可了解各函数与类的用途。
更多使用细节请参考 [《MyTimer 教程》](TUTORIAL.md)。

如需查看开发进度，请访问 [ROADMAP.md](ROADMAP.md) 或 [中文版](ROADMAP.zh.md)。
