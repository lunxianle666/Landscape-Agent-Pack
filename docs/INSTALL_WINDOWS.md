# Windows 安装与演练
前置：合法 AutoCAD 桌面版；Python 3.11+ x64（优先已测 3.12.10）。SketchUp 是可选组件，使用时另需合法 SketchUp 2023 与 Node ≥22。PowerShell 5.1 可运行。

## 第一次下载安装

1. 打开[RC2 Release下载页](https://github.com/lunxianle666/Landscape-Agent-Pack/releases/tag/v0.1.0-rc2)。
2. 在 Assets 中下载 `Landscape-Agent-Pack-v0.1.0-rc2-windows.zip`，不要误选 Source code。
3. 在下载文件夹空白处右键，打开终端 / PowerShell，输入以下命令；将文件名替换为你实际下载的文件名：

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath ".\Landscape-Agent-Pack-v0.1.0-rc2-windows.zip"
```

Windows ZIP 的最终 SHA256 请以 GitHub Release 页面公布的 SHA256 / Asset digest 为准。大小写不影响比较。与 Release 公布值不一致就停止，不运行安装器。

4. 右键 ZIP → 全部解压。打开解压后的 `Landscape-Agent-Pack` 文件夹，找到 `setup.bat`。不要在 ZIP 预览里直接运行。
5. 正常权限打开 AutoCAD。首次做绘图测试前，先自己保存并关闭所有图纸，保留 AutoCAD 程序运行。
6. 双击 `setup.bat` 安装；不知道如何合并配置时，复制[AI安装与配置总指令](AI_INSTALL_ASSISTANT_CN.md)给能访问本机的 Agent。安装窗口关闭不代表全部成功，让 AI 从本机 `runs` 结果核实。

若希望首次安装同时做最小绘图测试，可以在解压文件夹打开 PowerShell，以这个命令代替双击：

```powershell
.\setup.bat -RunGeometrySmoke
```

已有同名 Skill 时拒绝覆盖，不要删除原 Skill 或反复运行。让 AI 根据下面的独立演练参数选一个新目标。测试完成后，按生成片段合并客户端配置、重载客户端，并发送[连接检查提示词](../prompts/QUICK_PROMPTS_CN.md#1-检查连接)。不能因 SketchUp 的可选跳过认定 AutoCAD 失败。

安装完成后看[小白使用手册](BEGINNER_USAGE_CN.md)。日常绘图不必重新运行安装器或安装总指令。

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

RC2 不自动安装 Ringo，不应用本机 schema 修改（此行为继承自 RC1.1 历史验证）。启动 SketchUp 后，从扩展菜单启动已有桥。SketchUp 是可选组件。只有显式 -RunSketchUpSmoke / --sketchup 才进行 bridge_status / model_get_info；默认不连接、不启动，未运行输出 SKIPPED_NOT_RUNNING。明确测试时仍只连接既有实例，不修改模型。

## Codex / TRAE
安装器生成 `codex-autocad.toml` 和 `trae-autocad.json`。检查后仅合并 autocad 服务，不覆盖整个配置文件。Codex 使用 `[mcp_servers.autocad]`；官方说明：https://developers.openai.com/zh-Hans/docs/extend/mcp
TRAE 的 JSON 模板提供标准 stdio 片段，当前未完成 TRAE 客户端验收。

AutoCAD 服务固定 COM backend 和 Discovery search，不静默使用 ezdxf 替代真实 DWG 控制。不要以管理员身份运行整个安装器来掩盖 COM 权限冲突。

临时绘图要求 AutoCAD 文档集合为空。若有任何打开的图纸，测试拒绝绘图；请自行保存并关闭，不由安装器关闭。

AutoCAD 绘图测试通过自有 Creation Guard 包装；原始 MCP 错误仍保留为证据。所有保存重开和实体复核代码为本 Pack 自有实现，未复制无许可证重绘 Skill。
