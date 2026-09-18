# 故障排查
- COM 连接失败：确认 AutoCAD 已启动，比较实际 AutoCAD 与 Python/Agent 进程完整性等级，再核实版本化 ProgID。不要删除注册表或自动关闭图纸。
- Python 找不到：安装 Python 3.12 x64，或使用 -PythonExe 指定解释器，避免 WindowsApps 占位程序。
- 已有 Skill：安装器拒绝覆盖；RC 请指定独立 -SkillsDirectory。
- Ringo 拒绝连接：检查 SketchUp 是否打开了模型、正确 profile/port 是否启动。认证配置留在本机，不能贴出密钥。
- 某些 Ringo 工具不显示：历史 Codex tuple schema 兼容问题见 RINGO_LOCAL_PATCH_REPORT.md；不要自动应用未经当前客户端验证的补丁。
- MCP 报 RPC 错误：只读核查实际文档是否已开/关/保存；不要盲目重复操作。
- PDF 空白或截图异常：按限制报告 PARTIAL，检查真实页面和保存重开结果，不以 OK 返回值认定完成。

- 创建报 Color 属性不存在：可能是返回值序列化假失败，不能重复创建。必须用 Creation Guard 检查新增句柄和关键几何；仅匹配时 SUCCESS_WITH_FALSE_ERROR，保留上游报错。
