# Landscape Agent Pack v0.1.0-beta

Windows 景观 CAD / SketchUp 的 Agent 工作流包：安装器、规则、Skill、MCP 配置片段、重复执行守护和真实文件 smoke test。适合有合法桌面软件、愿意检查 Agent 输出的景观学习与设计用户。它不是自动景观设计软件，也不是生产级或任意 Agent 通用插件。

## 第一步：下载、解压、运行 setup.bat

在 [Beta Release](https://github.com/lunxianle666/Landscape-Agent-Pack/releases/tag/v0.1.0-beta) 的 Assets 下载 `Landscape-Agent-Pack-v0.1.0-beta.zip` 和 `.zip.sha256`，不要误选 Source code。比较 ZIP 的 SHA-256，完整解压，再打开里面的同名文件夹。

先用普通用户权限启动 AutoCAD；安装器与 CAD 必须处于相同权限级别。双击 `setup.bat`，等待检测、独立 Python runtime 安装及 MCP smoke 结果。PowerShell 执行策略仅对本次进程使用 Bypass，不更改系统策略。没有 Python 或依赖下载失败时会明确 FAIL。

Beta 是“主体自动安装 + 客户端配置人工完成”，不是完全一键安装。默认目标为 `%LOCALAPPDATA%\Landscape-Agent-Pack`；既有不同版本或损坏规则不会被覆盖。旧版本用户请用独立目标安装，例如：

```powershell
.\setup.bat -InstallRoot "$env:LOCALAPPDATA\Landscape-Agent-Pack-v0.1.0-beta"
```

安装后从结果打印的 `runs\<本次运行>\config` 取片段，先备份客户端配置，再只合并一个 MCP 服务；同名服务已存在时先比较，不能追加重复节。完全重启客户端，确认 Skill 与 MCP 真实可发现、可调用。安装器不写客户端配置、不自动 reload、不宣称已加载成功。现有不同 Skill 保留，新 Skill 暂存在安装根的 `skills`，须人工检查并选择安装，不能盲目覆盖。

详细步骤：[Windows 安装](docs/INSTALL_WINDOWS.md) · [客户端配置](docs/CLIENT_CONFIG_CN.md) · [小白使用手册](docs/BEGINNER_USAGE_CN.md)。

## 状态与系统要求

Verified 只代表本机最小回归范围，不是对所有机器的保证。

| 软件 / 功能 | Beta 状态 | 范围 |
| --- | --- | --- |
| Windows 11 / Python 3.12.10 x64 / PowerShell 5.1 | Verified | 现有本机；中文与空格目录，C/D 测试目标 |
| AutoCAD 2025 / AutoCAD MCP Pro 1.5.1 COM | Verified | MCP、Guard、真实 DWG 保存关闭重开、独立 Python COM 几何回读 |
| SketchUp Pro 2023 23.0.367 | Limited / Experimental | 本机既有 Ringo 1.3.2 兼容修改下的 box 和简单 DWG→基础三维→SKP 重开；不是原版上游所有组合验证 |
| Codex | Manual Setup | 既有 Agent 调用 SU MCP 已生成文件；新安装后的 Skill/MCP 重载仍 MANUAL TEST REQUIRED |
| TRAE / 其他 Agent | Not Tested | 提供 stdio 示例，不保证客户端兼容 |
| 完整复杂景观 / 曲线精度 / 任意 DWG 自动建模 | Experimental | 本次只验证简单线性基础模型 |
| 全新 Windows / 中文 Windows 账户 / 全权限异常矩阵 | Not Tested | 中文文件夹不等于中文账户 |

必须有合法 AutoCAD 桌面版、Python 3.11+ x64（实测推荐 3.12）、联网 pip、目录写权限；Python WindowsApps 占位程序不可用。安装器固定 AutoCAD MCP Pro 1.5.1，传递依赖未全量锁定。SketchUp 可选，另需合法 Pro 2023、Node ≥22 和外部 Ringo；本包不自动安装/修改 SketchUp 插件，也不分发软件本体。

## 最简单的首次使用

先让 Agent 读取安装后的 `pack-rules/AGENT_CONTEXT.md`（或解压根文件），输出上下文确认块；随后真实调用 `system_status`，要求 `backend=com`、`connected=true`。仅有配置文件不算连接成功。Discovery search 模式可能只显示 `search_tools` / `call_tool`，先发现实际工具。

AutoCAD 示例：先自行保存并关闭所有 CAD 图纸，保留程序运行；在解压目录运行：

```powershell
.\setup.bat -InstallRoot "$env:LOCALAPPDATA\Landscape-Agent-Pack-v0.1.0-beta" -RunGeometrySmoke
```

这会在本项目允许目录创建 1000×500 mm 矩形和半径 100 mm 圆，Guard 拒绝重复执行，然后保存、关闭、重开 DWG 并核对几何。不会关闭用户图纸。有打开图纸时测试拒绝绘图。日常任务只在用户授权的新输出路径保存，不覆盖来源。

SketchUp 示例提示词：“先 bridge_status、model_get_info 确认目标是空白测试模型，再创建 1000×500×300 mm 长方体，保存到我授权的全新 SKP 路径；关闭该模型、重新打开并回读 bounds、solid 和实体数量。”基础 CAD→SU 应原生导入真实 DWG，保留 CAD_REFERENCE，并由实际矩形边推导三维边界；高度由用户提供，不猜设计参数。不得用固定 box 冒充真实 DWG 导入。

## 诊断与常见错误

```powershell
.\setup.bat -InstallRoot "$env:LOCALAPPDATA\Landscape-Agent-Pack-v0.1.0-beta" -DiagnosticOnly
```

- Python 不存在/版本不符：安装 x64 Python，或显式 `-PythonExe` 指定真实解释器。
- pip/网络/pywin32 失败：保留错误与 runtime，修复依赖后重试，不把失败改成成功。
- COM 失败：确认 CAD 已启动并与安装器同权限；不默认提升权限或重启 CAD。
- 完整性 FAIL：会打印具体相对路径、缺失原因或 expected/actual hash；停止使用，从可信 Release 重取，不运行 manifest 生成器“修复”。
- SketchUp bridge 拒绝连接：进入模型后按外部 Ringo 文档启动既有 Server；先确认实例，不启用额外 Ruby 权限来掩盖问题。
- Overall WARN / exit=0：安装主体与 smoke 通过仍不代表人工客户端配置完成。

更多：[排错](docs/TROUBLESHOOTING_CN.md) · [完整性](docs/INTEGRITY.md) · [限制](docs/LIMITATIONS.md)。

## 安全、卸载与失败恢复

规则与关键文件由版本化 manifest 的 SHA-256 检查；缺失或篡改 FAIL。Guard 结合真实后置几何防止错误重放，原始 MCP 错误保留。manifest 不是数字签名，可信 Release ZIP hash 才是外部比较依据；协调替换 manifest/校验器不是其防护范围。

安装器不覆盖 Codex 设置、不删除现有 Skill、不修改 AutoCAD 配置或 SU 插件。失败时保留诊断文件并列出本次写入目录；无复杂事务式自动回滚。先备份需要保留的 DWG/SKP/runs，再手工删除确认属于本项目的独立安装目录。Skill 仅在确认由本次新建且没有个人修改时移除；客户端仅删除自己加入的服务节，保留其他设置；不要卸载共享 Python/Node/CAD/SU/Ringo。

## License、验收与反馈

自有代码 [MIT](LICENSE)，第三方见 [声明](THIRD_PARTY_NOTICES.md)。分发 SketchUp Skill 保留其 LICENSE；`autocad-dwg-redraw` 授权未确认，只保留来源声明、不分发代码。依赖包由用户安装时从上游获取，不能全部称为 MIT。

[CHANGELOG](CHANGELOG.md) · [验收范围](docs/BETA_ACCEPTANCE.md) · [Issues](https://github.com/lunxianle666/Landscape-Agent-Pack/issues)。反馈请附版本、软件版本、失败步骤与脱敏错误；不要上传 Token、私人配置、用户名路径或实际项目图纸。
