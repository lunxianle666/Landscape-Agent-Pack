# 贡献指南

先用公开合成 fixture 或最小脚本复现问题，再在分支上提交针对性修改。Issue 或 PR 请记录 Python、AutoCAD、SketchUp、Ringo 的实际版本（按用到的组件填写）、复现命令、预期与实际结果。图纸与截图须可公开；不要提交客户文件、安装目录、配置、鉴权信息或用户目录路径。

从仓库根目录运行 Windows PowerShell：

```powershell
py -3.12 -m venv .venv
$lapPython = '.\.venv\Scripts\python.exe'
& $lapPython -m pip install -r requirements-v02-dev.txt
& $lapPython -m pip check
& $lapPython -m compileall -q landscape_agent_pack guards installer examples tests
& $lapPython -m unittest discover -s tests/unit -v
& $lapPython -m unittest discover -s tests/smoke -v
& $lapPython installer/verify-rules.py --root .
& $lapPython -B -m examples.geometry_qa
```

- `AGENT_CONTEXT.md` 是规则入口。新增正式 Skill 时，使用 `skills/<name>/SKILL.md`，声明同名 `name`、`description`，提供明确的依赖与验收条件及许可。优先复用 `landscape_agent_pack/cad`、`guards` 和独立的 `bridge` 模块。
- 修改 COM 写入或原生导入后，使用合法软件和独立工作区执行 [真实用例](docs/V02_BRIDGE.md#reproduction)。技术数值通过、人工图面复核、Mock 和真实软件验收请分别记录。不重放结果不确定的写操作；不要启动全局清理或关闭已有用户文档。
- 生成的图纸、模型、运行日志与临时配置放在已忽略的 `runs/` 或 `outputs/`。可公开示例优先用脚本生成。
- 维护人员更新源码完整性清单：先暂存待分发文件，再用 `python installer/build-manifest.py --version <当前清单版本>` 重新生成并暂存 `manifest.json` 和 `SHA256SUMS.txt`。已有正式 Tag 的清单和文件保留原样。用户遇到校验失败时应重新获取可信版本。
- GitHub Actions 只跑离线检查。真实端到端、发布与 Tag 创建是单独的维护操作。
