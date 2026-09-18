# 故障排查
- COM 连接失败：确认 AutoCAD 已启动，比较实际 AutoCAD 与 Python/Agent 进程完整性等级，再核实版本化 ProgID。不要删除注册表或自动关闭图纸。
- Python 找不到：安装 Python 3.12 x64，或使用 -PythonExe 指定解释器，避免 WindowsApps 占位程序。
- 已有 Skill：候选安装器复用一致内容；不同内容保留原件并暂存候选，报告 WARN。不要删除原 Skill；客户端加载候选需人工审核。
- 完整性 FAIL：查看具体路径及 SHA-256 原因。从可信原包重新获取，不运行 build-manifest.py 来掩盖差异。DiagnosticOnly 会返回非零。
- 同版本重复安装：重查规则并运行 smoke，不新增重复 Skill/MCP；不同版本或既有规则损坏时停止，使用独立目录保留旧版。
- Ringo 拒绝连接：检查 SketchUp 是否打开了模型、正确 profile/port 是否启动。认证配置留在本机，不能贴出密钥。
- 某些 Ringo 工具不显示：历史 Codex tuple schema 兼容问题见 RINGO_LOCAL_PATCH_REPORT.md；不要自动应用未经当前客户端验证的补丁。
- MCP 报 RPC 错误：只读核查实际文档是否已开/关/保存；不要盲目重复操作。
- PDF 空白或截图异常：按限制报告 PARTIAL，检查真实页面和保存重开结果，不以 OK 返回值认定完成。

- 创建报 Color 属性不存在：可能是返回值序列化假失败，不能重复创建。必须用 Creation Guard 检查新增句柄和关键几何；仅匹配时 SUCCESS_WITH_FALSE_ERROR，保留上游报错。
