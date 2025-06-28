# 开发任务清单
[English](REARMED.md) | [项目概览](README.md) | [教程](TUTORIAL.md)


## 已完成
- 清理了 `mytimer/server/api.py` 和测试中的无用导入。
- 安装了所需依赖。
- 通过 `pytest -q` 验证所有单元测试均通过。
- 实现了计时器结束通知模块 `Notifier`。
- 新增 CLI 模块（`tui_app.py`、`client_view_layer.py`、`input_handler.py`）。
- 完成 `ClientSettings` 模块并实现配置持久化。

## 待办
 - 补充端到端测试以覆盖完整的客户端/服务器工作流程.


返回 [教程](TUTORIAL.md) 或 [项目概览](README.md)。
