# Windows 安装与演练
前置：合法 AutoCAD 桌面版、SketchUp 2023；Python 3.11+ x64（优先已测 3.12）；SketchUp 接入需 Node ≥22。PowerShell 5.1 可运行。

双击 `setup.bat` 默认安装依赖并尝试安装 SketchUp Landscape Skill。已有同名 Skill 时会拒绝覆盖，保留原件。当前 `autocad-dwg-redraw` 授权未确认，不安装。

RC 独立演练命令：
```powershell
.\setup.bat -InstallRoot "<PATH>" -SkillsDirectory "<PATH>" -RunGeometrySmoke
```
必须替换占位符为独立目录。可传 `-PythonExe`、`-NodeExe`、`-RingoDirectory`。`-UseExistingDependency` 只验证当前 Python 中的固定依赖版本，避免重新安装；默认是独立 venv 安装。

安装结果在 InstallRoot 的 runs 下。配置文件、日志和 DWG 都是本机数据，不可上传。允许目录默认只有本轮临时绘图目录；开展实际项目时由用户明确选择新的项目目录。

## Ringo 固定官方版本
来源：https://github.com/Ringophilia/Ringo-Sketchup-MCP
固定提交：`2dd54d945b0e7a5d1843d58a94a33f5c8875df01`（package 1.3.2）。在独立第三方工具目录中准备官方源码，按该提交 README 使用 `npm ci`、`npm run build`、`npm run setup -- --year 2023`。这些步骤不属于本 Pack 自动安装；已有扩展或 Ringo 配置先检查冲突，不覆盖。

RC1.1 不自动安装 Ringo，不应用本机 schema 修改。启动 SketchUp 后，从扩展菜单启动已有桥。SketchUp 是可选组件。只有显式 -RunSketchUpSmoke / --sketchup 才进行 bridge_status / model_get_info；默认不连接、不启动，未运行输出 SKIPPED_NOT_RUNNING。明确测试时仍只连接既有实例，不修改模型。

## Codex / TRAE
安装器生成 `codex-autocad.toml` 和 `trae-autocad.json`。检查后仅合并 autocad 服务，不覆盖整个配置文件。Codex 使用 `[mcp_servers.autocad]`；官方说明：https://developers.openai.com/zh-Hans/docs/extend/mcp
TRAE 的 JSON 模板提供标准 stdio 片段，当前未完成 TRAE 客户端验收。

AutoCAD 服务固定 COM backend 和 Discovery search，不静默使用 ezdxf 替代真实 DWG 控制。不要以管理员身份运行整个安装器来掩盖 COM 权限冲突。

临时绘图要求 AutoCAD 文档集合为空。若有任何打开的图纸，测试拒绝绘图；请自行保存并关闭，不由安装器关闭。

AutoCAD 绘图测试通过自有 Creation Guard 包装；原始 MCP 错误仍保留为证据。所有保存重开和实体复核代码为本 Pack 自有实现，未复制无许可证重绘 Skill。
