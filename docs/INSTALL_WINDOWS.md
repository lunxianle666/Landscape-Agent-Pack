# Windows Beta 安装

下载 [v0.1.0-beta Release](https://github.com/lunxianle666/Landscape-Agent-Pack/releases/tag/v0.1.0-beta) 的 ZIP 和 `.zip.sha256`；不要使用旧 RC2 附件。比较校验值后右键全部解压，进入 `Landscape-Agent-Pack-v0.1.0-beta` 文件夹。目录可改名，setup 按自身位置找 installer；不要在 ZIP 预览中运行。

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath .\Landscape-Agent-Pack-v0.1.0-beta.zip
```

先安装合法 AutoCAD 和 Python 3.11+ x64（实测 3.12.10），启动 CAD 并与安装器保持相同权限。普通用户双击 `setup.bat`；不需要修改全局 PowerShell 策略。默认安装独立 venv、固定 AutoCAD MCP Pro 1.5.1、Skill、六项规则并自动 smoke。SketchUp 不影响 AutoCAD 主链，使用时另需 Node ≥22 与外部 Ringo。

## 已安装版本 / 选择独立目录

```powershell
.\setup.bat -InstallRoot "$env:LOCALAPPDATA\Landscape-Agent-Pack-v0.1.0-beta" -RunGeometrySmoke
```

同版本复用并重新校验、smoke，不重复 Skill/MCP。不同版本或损坏规则保留并 FAIL，请选择独立目录；Beta 不做覆盖升级迁移。`-SkillsDirectory` 可选独立 Skill 目录，`-PythonExe` 指定实际 Python。`-UseExistingDependency` 是高级选项，要求该 Python 已具有固定依赖，不等于默认安装。

现有同名 Skill 内容不同会保留并 WARN，新文件暂存在 InstallRoot/skills。此时人工比较，先备份再选择客户端搜索目录；不宣称 Agent 已发现。没有明确授权不要覆盖旧 Skill。

## 客户端人工配置（必须）

结果打印本次 runs 路径。配置片段在其中 `config/codex-autocad.toml` / `trae-autocad.json`，路径已按本机生成。备份客户端配置，只合并 autocad 服务；同名节已有时先比较，不产生重复 TOML 节或 JSON key。不覆盖整文件。保留已有 env，允许输出路径限用户明确授权目录。

按 [客户端说明](CLIENT_CONFIG_CN.md) 完全退出/重启客户端，再确认 Skill、MCP 可发现；让 Agent 读 pack-rules/AGENT_CONTEXT.md、实际调用 system_status，再创建真实测试文件。**MANUAL TEST REQUIRED**：新安装后的客户端重载尚未本轮自动验证。依据：[官方 MCP 配置](https://developers.openai.com/zh-Hans/docs/extend/mcp)、[技能发现与重启](https://developers.openai.com/zh-Hans/docs/build-skills)。

安装器从不写客户端配置；Overview WARN 不等于完整端到端 ready。缺依赖、COM或完整性故障均真实退出失败。失败保留 runtime、规则、Skill 暂存、runs 并打印写入范围，无自动事务回滚；保留日志诊断，别删除共享软件。

## 诊断 / 卸载

```powershell
.\setup.bat -InstallRoot "$env:LOCALAPPDATA\Landscape-Agent-Pack-v0.1.0-beta" -DiagnosticOnly
```

此模式不安装、不修复损坏文件。规则缺失/变动最终 FAIL。绘图 smoke 要求 CAD 文档为空，请自行保存关闭；程序仍保持运行，不由安装器关闭用户图纸。

卸载前备份生成图纸。只移除确认由本项目创建的独立安装根、新建且未修改的 Skill、自己合并的 MCP 节；不删现有 Skill、共享依赖或 SU 插件。

## SketchUp 可选项

[Ringo](https://github.com/Ringophilia/Ringo-Sketchup-MCP) 1.3.2 官方固定提交 `2dd54d945b0e7a5d1843d58a94a33f5c8875df01`，按上游 README 手动安装，不覆盖已有扩展。本机验证使用既有兼容修改，详见 RINGO_LOCAL_PATCH_REPORT.md；Beta 不自动应用该补丁，不保证原版组合。`-RunSketchUpSmoke` 仅检测既有 bridge/info，不做 box / DWG 导入完整验收。Ruby eval 本次没有开启。
