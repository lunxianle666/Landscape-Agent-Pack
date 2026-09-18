# Landscape Agent Pack · V0.1-RC1.1
Landscape Agent Pack 是一个 Windows 风景园林 AI Agent 工作流包。学生可以通过支持 MCP 的 AI Agent（如 Codex / TRAE），用自然语言进行景观 CAD 基础工作，并复用统一的设计规则与安全检查。

```text
AI Agent
↓
Landscape Agent Pack（工作流规则、安装器与 Guard）
↓
AutoCAD MCP Pro
↓
AutoCAD
可选组件：
AI Agent
↓
Ringo SketchUp MCP
↓
SketchUp
```

你需要自行合法安装 AutoCAD；使用可选建模工作流时自行合法安装 SketchUp。本项目不包含 AutoCAD、SketchUp、破解软件、商业软件安装包、Python 环境或第三方 MCP 源码。

RC1.1 审核范围是 AutoCAD 主链：独立安装、MCP/Discovery、临时矩形和圆、保存关闭重开、真实几何复核。SketchUp 默认不连接、不启动；未运行记为 SKIPPED_NOT_RUNNING，不影响 AutoCAD 主链。第三方 autocad-dwg-redraw 缺少确认授权，继续排除，不是本版必需组件。

## 第一次使用
解压完整目录，阅读 [Windows 安装说明](docs/INSTALL_WINDOWS.md)，再运行 setup.bat。已有同名 Skill 时拒绝覆盖。RC 演练请指定独立 Skill 目标目录。

安装器建立独立本机虚拟环境，从 PyPI 安装 `autocad-mcp-pro[com]==1.5.1`。只生成配置片段，由用户检查后合并，不覆盖原配置。临时绘图需 `-RunGeometrySmoke` 且 AutoCAD 文档集合为空；不自动关闭用户图纸。

## 已知创建假失败
AutoCAD 2025 类型库生成包装暴露小写 color，上游返回值提取读取大写 Color，可能在对象已创建后报错。自有 [Creation Guard](guards/README.md) 检查句柄差集与关键几何，确认后返回 SUCCESS_WITH_FALSE_ERROR，保留原错误，同一操作 ID 禁止重复调用。它是明确使用的调用包装，不会自动拦截绕过 Guard 的原始 MCP 调用。

实测版本：AutoCAD 2025、Python 3.12.10、AutoCAD MCP Pro 1.5.1；历史可选环境为 SketchUp 2023 / Ringo 1.3.2。模型空间为实验验证；Layout/PDF 为 Beta，截图不稳定，完整施工图仍在发展。本版不测试这些能力，不承诺一键万能。

[快速开始](docs/QUICK_START_CN.md) · [限制](docs/LIMITATIONS.md) · [安全规则](standards/autocad-safety-rules.md) · [第三方声明](THIRD_PARTY_NOTICES.md)

## 当前成熟度

这是 Release Candidate，不是稳定版。当前实测环境为 Windows、AutoCAD 2025、Python 3.12.10、AutoCAD MCP Pro 1.5.1（COM backend）。

| 能力 | 当前状态 |
|---|---|
| AutoCAD 模型空间基础绘图 | 可用，实验验证通过 |
| Guard Layer | 可用；必须通过 Guard 包装调用，不能自动拦截原始 MCP 调用 |
| 保存 → 关闭 → 重开及几何复核 | 已验证 |
| Landscape 绘图 | 实验阶段 |
| Layout / PDF | Beta，当前 RC 未测试 |
| SketchUp / Ringo | 可选组件，当前 RC 未完成运行时 Smoke Test |

其他 AutoCAD 版本可能需要适配；未验证所有版本，也不承诺无人值守完整施工图流程已稳定。Guard 的重复操作凭据仅在当前进程内有效，重启后需重新核查句柄。

[当前 RC1.1 验证报告](docs/RC1_1_BUILD_REPORT.md) · [匿名测试摘要](tests/evidence/rc1.1-summary.json) · [预发行版下载](https://github.com/lunxianle666/Landscape-Agent-Pack/releases/tag/v0.1.0-rc1)

Release 附件保留已审核 RC1.1 ZIP，仓库的首次发布仅补充 README 并清理文档空白；附件 SHA256 以 Release Notes 为准。
