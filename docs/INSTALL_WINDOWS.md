# Windows 安装与开始：v0.2.0

当前正式 Release 为 [v0.2.0](https://github.com/lunxianle666/Landscape-Agent-Pack/releases/tag/v0.2.0)，Tag 对应提交 `ac378d84ce4bbb9489ee4664b0db3e498e0359fa`。下面先获取固定正式快照，再按用途选择安装路径。旧 Beta/RC 步骤见 [历史说明](HISTORY.md)。

## 1. 下载并校验正式包

从 Release Assets 下载 [Landscape-Agent-Pack-v0.2.0.zip](https://github.com/lunxianle666/Landscape-Agent-Pack/releases/download/v0.2.0/Landscape-Agent-Pack-v0.2.0.zip) 与 [.zip.sha256](https://github.com/lunxianle666/Landscape-Agent-Pack/releases/download/v0.2.0/Landscape-Agent-Pack-v0.2.0.zip.sha256)。不要将 GitHub 自动生成的 Source code ZIP 与此附件混为一谈。

在下载目录比较本地 ZIP 的 SHA-256 与 sidecar/Release 中的值：

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath .\Landscape-Agent-Pack-v0.2.0.zip
Get-Content -LiteralPath .\Landscape-Agent-Pack-v0.2.0.zip.sha256
```

正式 ZIP 的 SHA-256 为：

```text
71f4899bb1bc88f75558ab6dff065931a34f0ef05995c6a4b47ecf9b93013422
```

不匹配时停止，从可信 Release 重取；不要运行 manifest 生成器消除失败。完整解压到新目录（例如 `D:\GitHub\Landscape-Agent-Pack-v0.2.0`），进入含 `setup.bat` 和 `manifest.json` 的根目录，不在 ZIP 预览中运行。先执行只读完整性验证：

```powershell
py -3.12 -B installer/verify-rules.py --root .
```

此命令需要已安装的 Python；实测为 Python 3.12.10 x64。WindowsApps 占位解释器不可用。

## 2. 按用途选择路径

| 用途 | 入口 | 安装范围与前提 |
| --- | --- | --- |
| Agent 规则、独立 Skill、AutoCAD MCP 配置片段与旧链 smoke | 下方 A：`setup.bat` | 沿用规则/MCP 安装器；不自动安装完整 v0.2 Core/QA/Bridge 开发依赖 |
| Python Core、Geometry/PDF QA、CAD→SU Bridge 最小回归 | 下方 B：独立 venv + 源码 | 安装 `requirements-v02-dev.txt`；既有合法 CAD/SU、兼容 Ringo 和授权配置仍需自行准备 |

两条路径均不替代客户端真实发现、连接和项目预检。只需 AutoCAD 时无需为规则安装启动 SketchUp。

## A. 规则 / MCP 安装器

先准备合法 AutoCAD、Python 3.11+ x64（实测 3.12.10）和联网 pip；以普通权限启动 CAD，安装器与 CAD 保持同一权限级别。使用新的短安装目录，例如：

```powershell
.\setup.bat -InstallRoot 'D:\AI-Tools\LAP-v020-rules'
```

安装器建立独立 runtime，固定安装 AutoCAD MCP Pro 1.5.1，复制 Skill/六项规则，生成配置片段并运行 MCP smoke。依赖失败会 FAIL；传递依赖未全量锁定。它不安装/修改 Ringo，不替你合并客户端配置。

同版本安装会复用并重新校验；不同版本或损坏规则保留并 FAIL，使用独立目录，不能覆盖升级。`-PythonExe` 可指定实际解释器，`-SkillsDirectory` 可指定 Skill 目录。现有不同内容的 Skill 保留并 WARN，新文件暂存于 InstallRoot/skills，须人工比较、备份后选择，避免同名重复发现。安装根超过 120 字符会在写入前拒绝，以避免已观察到的 pywin32 WinError206；不修改系统长路径策略。

### 客户端人工配置

从安装结果打印的本次 `runs` 目录取 `config/codex-autocad.toml` 或 `trae-autocad.json`。备份客户端配置，只合并一个服务节；保留既有 env，不追加重复 TOML 节或 JSON key，不覆盖整文件。按 [客户端说明](CLIENT_CONFIG_CN.md) 完全退出并重启，确认 Skill/MCP 实际可发现、可调用；让 Agent 读取 `pack-rules/AGENT_CONTEXT.md`，再真实调用 `system_status`，检查 `backend=com`、`connected=true`。

新安装后的 Codex 桌面发现/配置重载仍为 **MANUAL TEST REQUIRED**。文件存在或安装结果 WARN/exit=0 不代表完整端到端 ready。

### 诊断与可选真实 smoke

```powershell
.\setup.bat -InstallRoot 'D:\AI-Tools\LAP-v020-rules' -DiagnosticOnly
```

DiagnosticOnly 不安装或修复文件，完整性失败会传播为 FAIL。若需要真实绘图 smoke，先自行保存并关闭所有已有 CAD 文档，保留程序运行，再执行：

```powershell
.\setup.bat -InstallRoot 'D:\AI-Tools\LAP-v020-rules' -RunGeometrySmoke
```

这会在允许的测试目录创建矩形/圆并保存、关闭、重开 DWG、复核几何；它是需实际软件的测试，不属于文档/静态校验。安装器不关闭用户图纸。`-RunSketchUpSmoke` 仅检查既有 bridge/info，不是 DWG→SKP 完整验收。

## B. v0.2.0 Python 源码工作流

可直接使用第 1 步校验后的正式包。开发者也可获取固定 Tag，避免把后续 main 文档提交当成原始发行快照：

```powershell
git clone --branch v0.2.0 --depth 1 https://github.com/lunxianle666/Landscape-Agent-Pack.git D:\GitHub\Landscape-Agent-Pack-v020
cd D:\GitHub\Landscape-Agent-Pack-v020
```

该方式处于 detached HEAD，适合检查固定版本；开发修改应另建分支。源码目录和 venv 均使用尚不存在的独立目录，不覆盖现有安装。在所选包/源码根目录运行：

```powershell
py -3.12 -m venv D:\AI-Tools\Landscape-Agent-Pack\venv-v020
& D:\AI-Tools\Landscape-Agent-Pack\venv-v020\Scripts\python.exe -B installer/verify-rules.py --root .
& D:\AI-Tools\Landscape-Agent-Pack\venv-v020\Scripts\python.exe -m pip install -r requirements-v02-dev.txt -r installer/requirements.txt
& D:\AI-Tools\Landscape-Agent-Pack\venv-v020\Scripts\python.exe -B -m unittest discover -s tests/unit -v
& D:\AI-Tools\Landscape-Agent-Pack\venv-v020\Scripts\python.exe -B -m unittest discover -s tests/smoke -v
```

`installer/requirements.txt` 提供旧安装器/smoke 使用的 AutoCAD MCP；开发依赖提供几何、PDF 和测试传输模块。上述 unit/smoke 回归通过不等于真实 CAD/SU 验收。

真实最小 E2E 需要 AutoCAD 没有打开的用户文档、SketchUp 打开位于唯一 `runs/` 目录中的自有且已保存空白 SKP。按 [Bridge 工作流](V02_BRIDGE.md#reproduction) 操作，并使用上面的 venv 解释器；先确认 Bridge 实例/端口与当前模型。通过 `--config` 指定隔离的 Ringo 配置，保留认证，仅在目标进程/配置中授权可信 Ruby；不要公开配置或 Token。

历史验证使用 AutoCAD 2025、SketchUp Pro 2023 23.0.367 与本机既有兼容 Ringo 1.3.2。新 venv、干净 checkout、临时配置仍为 **PARTIAL_FRESH_ENV**，不证明全新机器或未修改上游插件安装。参阅 [RC2 验收](V02_RC2_ACCEPTANCE.md)、[兼容调整](RINGO_LOCAL_PATCH_REPORT.md) 和 [已测环境](TESTED_ENVIRONMENT.md)。

## 失败恢复、卸载与完整性

安装失败会保留 runtime、规则、暂存 Skill、runs 并打印可能写入的目录，便于诊断；无事务式自动回滚。卸载前备份需要的图纸/运行结果，只移除确认属于本项目的独立安装根、新建且未修改的 Skill 和自己合并的 MCP 节。不要删除共享 Python/Node/CAD/SU/Ringo。

源码 `.gitattributes` 保持提交字节，校验继续拒绝缺失/篡改。main 的维护提交与正式 Tag/ZIP 校验值分别对应各自快照，不能混用。见 [完整性约定](INTEGRITY.md)、[排错](TROUBLESHOOTING_CN.md)。
