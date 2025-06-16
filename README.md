# MyTimer

## 📋 项目概览

- **项目目标**：构建一个可跨设备同步的倒计时管理系统，支持远程控制、通知推送、实时更新和设置同步。
- **系统组成**：服务器 + 多客户端（桌面/Web/移动），通过网络通信保持状态同步。

---

## ✅ 主要模块与职责（支持并行开发）

| 模块名称              | 类型     | 功能说明                                               | 可并行 | 依赖           |
|---------------------|----------|--------------------------------------------------------|--------|----------------|
| 🧠 TimerManager     | Server  | 管理计时器对象，提供创建、更新、删除、倒计时与状态检测功能            | ✅     | 无             |
| 🌐 APIServer        | Server  | 提供 REST API 和 WebSocket 接口                        | ✅     | TimerManager   |
| 🔔 Notifier         | Server  | 监控倒计时到期状态并执行通知推送                         | ✅     | TimerManager   |
| 👤 ClientAuth       | Server  | 客户端鉴权模块，识别设备ID或Token                       | ✅     | APIServer      |
| 🖼️ ClientViewLayer | Client  | 客户端主界面，显示计时器列表与状态、标签、剩余时间等信息         | ✅     | SyncService    |
| 🎮 ClientController | Client  | 接收用户操作指令并通过 API 向服务器发送请求                    | ✅     | APIServer      |
| ⚙️ ClientSettings   | Client  | 设置面板：铃声、通知选项、导入导出配置、本地缓存                    | ✅     | 本地数据        |
| 🔁 SyncService      | Client  | 与服务器保持 WebSocket 同步、REST 接口控制                      | ✅     | Server API     |
| 🧭 ServerDiscovery  | Client  | 自动发现局域网服务器，展示服务器连接状态                        | ✅     | 无             |

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
