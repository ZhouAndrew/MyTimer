
# ✅ MyTimer 项目并行任务清单（TODO）

## 🧠 Server 端

### ⏱ TimerManager 模块（✅ 可并行）

* [x] 支持计时器自动递减机制（后台 tick 或整合 `autotick`）
* [x] 增加持久化机制：支持保存计时器状态（JSON/SQLite）
* [x] 实现批量操作：暂停全部 / 删除全部 / 重置全部计时器
* [x] 增加状态重启恢复功能（支持服务重启后恢复定时器状态）

### 🌐 APIServer 模块（✅ 可并行）

* [x] 增强 CLI 命令解析错误提示（如参数缺失、拼写建议）
* [x] 添加 REST API 接口 `/timers/pause_all`, `/timers/reset_all`
* [x] 支持 API 查询服务器状态（如运行中计时器数量）

### 🔔 Notifier 模块（✅ 可并行）

* [x] 实现倒计时结束后的通知机制（print/log）
* [x] 集成系统通知支持：`notify-send` / `plyer`
* [x] 支持自定义通知类型（静音、弹窗、铃声等）

---

## 🎮 客户端（CLI / TUI）

### 🧾 CLI 客户端（✅ 可并行）

* [x] 增加命令提示与拼写建议（使用 `difflib.get_close_matches`）
* [x] 支持 pause/resume/remove all 命令
* [x] 支持清除所有计时器命令 `clear` 或 `reset`
* [x] 引入历史记录或命令补全（如用 `readline`）

### 🖥 TUI 客户端（✅ 可并行）

* [x] 添加定时刷新机制（定时拉取或订阅 WebSocket）
* [x] 支持对选中计时器的操作（暂停/恢复/删除）
* [x] 增加操作快捷键提示区域
* [x] 显示当前连接服务器地址和状态

---

## 🔁 SyncService 与 WebSocket（✅ 可并行）

* [x] 实现 WebSocket 客户端订阅服务端更新
* [x] 支持跨端状态实时同步（TUI、Web 同时控制）
* [x] 断线重连后状态重同步

---

## ⚙️ 设置与本地缓存（✅ 可并行）

* [x] 添加配置项支持（保存 API 地址、本地设置）
* [x] 实现导入导出配置为 JSON
* [x] 添加客户端身份标识配置（设备名或 token）

---

## 🔍 ServerDiscovery（✅ 可并行）

* [x] 实现局域网服务器发现功能（UDP 广播或 mDNS）
* [x] 在 TUI 或设置中显示可连接服务器列表
* [x] 支持自动连接上次成功连接的服务器

---

## 🔔 通知与音效模块（✅ 可并行）

* [x] 集成本地音频播放功能（使用 `pygame` 或 `QtMultimedia`）
* [x] 支持多种提示音选择（支持导入本地 mp3）
* [x] 实现静音模式和音量调节

---

## 🧪 测试与调试（✅ 可并行）

* [x] 添加自动测试脚本覆盖 TUI、CLI、API 多模块组合
* [ ] 使用 WebSocket mocking 工具测试状态同步一致性
* [x] 添加 timer 状态单元测试（开始、暂停、恢复、完成）
* [ ] 使用 `pytest-cov` 增加覆盖率报告

