# Landscape Agent Pack

Windows 景观 CAD / SketchUp 的 Agent 工作流包：保护原图和用户文档，以真实几何、文件保存重开和数值/视觉 QA 检查自动化结果。适合已有合法桌面软件、愿意审核输出的景观学生、设计人员和自动化维护者。

**当前正式版：[v0.2.0](https://github.com/lunxianle666/Landscape-Agent-Pack/releases/tag/v0.2.0)**（2026-09-30，提交 [`ac378d8`](https://github.com/lunxianle666/Landscape-Agent-Pack/commit/ac378d84ce4bbb9489ee4664b0db3e498e0359fa)）。

[下载正式 ZIP](https://github.com/lunxianle666/Landscape-Agent-Pack/releases/download/v0.2.0/Landscape-Agent-Pack-v0.2.0.zip) · [SHA-256 校验文件](https://github.com/lunxianle666/Landscape-Agent-Pack/releases/download/v0.2.0/Landscape-Agent-Pack-v0.2.0.zip.sha256) · [Windows 安装与开始](docs/INSTALL_WINDOWS.md)

## 解决什么问题

- AutoCAD 调用报错后，先验证实际新增实体，避免盲目重放写入；Guard 必须显式使用。
- CAD→SketchUp 原生导入后，保留 `CAD_REFERENCE`，核对单位、边界、采样几何和保存重开结果。
- 将数值 QA、技术视觉 QA 和待审事项分别记录，让“调用成功”有可检查的文件与几何依据。

它提供受约束的自动化和验收流程；设计参数、缺失语义与最终设计审批仍需人工判断。

## 如何开始

1. 从上方正式 Release 下载 ZIP 与校验文件，校验后完整解压；不要在 ZIP 预览中运行。
2. 按 [安装指南](docs/INSTALL_WINDOWS.md) 选择路径：只安装规则/MCP 用 `setup.bat`；运行 v0.2.0 Python Core、QA 和 Bridge 则使用独立 venv 与源码工作流。安装器不会自动配置完整 Core/Bridge 环境。
3. 先做只读环境/实例确认，再在新建、明确归属的测试目录运行最小流程。已有图纸自行保存关闭，不能把配置文件存在当作客户端已连接。

已测组合为 Windows、Python 3.12.10、AutoCAD 2025、SketchUp Pro 2023 23.0.367 与既有兼容 Ringo 1.3.2。软件、插件和客户端配置需自行准备。详见 [工作流与排错](docs/V02_BRIDGE.md)、[客户端配置](docs/CLIENT_CONFIG_CN.md)。旧 Beta/RC 安装入口见 [历史版本说明](docs/HISTORY.md)。

## 实际验证了什么

以下是 v0.2.0 所依据的历史本机验收，未在本次文档维护中重跑 CAD/SU：

| 范围 | 公开记录的结果 | 证据 |
| --- | --- | --- |
| AutoCAD Core、Geometry QA、PDF plotting、原生 DWG→SU、SKP 保存/关闭/磁盘重开回读 | 本机限定范围通过；数值与视觉 QA 分开记录 | [验收案例](docs/CASES.md)、[RC2 验收](docs/V02_RC2_ACCEPTANCE.md) |
| A/B/C 三个真实景观项目参考几何链 | **PASS_WITH_WARNINGS**，保留注释、填充、曲线和宽线语义限制 | [案例与方法](docs/CASES.md) |
| SketchUp 进程冷启动、Bridge 重连、文档归属保护 | 限定测试通过；不证明 Codex 桌面重载/发现 | [RC2](docs/V02_RC2_ACCEPTANCE.md)、[RC3 ownership](docs/V02_RC3_OWNERSHIP.md) |
| 干净 checkout、独立 venv、临时配置 | **PARTIAL_FRESH_ENV**，仍使用本机既有软件和兼容插件 | [已测环境](docs/TESTED_ENVIRONMENT.md) |

公开仓库提供验收摘要和部分测试代码；真实项目 DWG/SKP、运行报告、截图和演示未随正式包公开，不能凭摘要完整复现历史项目。案例页标明输入、操作、输出、验证方法和证据缺口。

## 限制

- `CAD_REFERENCE` 是参考几何，不是完成的三维景观模型；不保证完整 CAD 无损转换。
- TEXT / MTEXT / DIMENSION / HATCH 不保证语义保留；Circle / Arc / bulged polyline 为离散几何与部分语义支持；宽线不完整保留中心线/宽度语义。
- SPLINE / ELLIPSE / XREF / 任意 3D 尚未验证；采样检查不构成全局曲线、拓扑或设计正确性证明。
- 本机 Ringo 有既有兼容调整，未分发补丁。原版插件安装、另一台机器、其他 CAD/SU 版本、Codex 桌面发现/配置重载仍待实测。
- 规则安装器需人工备份、合并客户端配置并重启；传递依赖未全量锁定。Manifest 是完整性校验，不是数字签名。

参阅 [完整限制](docs/LIMITATIONS.md)、[Ringo 兼容记录](docs/RINGO_LOCAL_PATCH_REPORT.md)、[完整性约定](docs/INTEGRITY.md)。

## 维护范围与组件关系

本仓库是继续维护的主项目，优先处理文档准确性、兼容性和有明确输入/步骤/证据的可复现缺陷，不承诺新增设计能力或扩大兼容矩阵。

[sketchup-from-cad-landscape](https://github.com/lunxianle666/sketchup-from-cad-landscape) 保留为冻结的历史独立指令型 Skill。本 Pack 已纳入其固定公开基线 `cc28ffd4b9daea890fbe78fd3737c9669d042446` 的 Skill、必要文档与 LICENSE；不是运行时追踪独立仓库 main。适配范围见 [基线报告](docs/SKILL_BASELINE_REPORT.md)。新用户需要规则、Core/QA/Bridge 和集中维护入口时选择本 Pack；已有完整工具栈、只需历史 Skill 时仍可使用独立组件，避免重复安装同名 Skill。

[正式发行说明](docs/V02_RELEASE_NOTES_DRAFT.md)（保留旧文件名） · [CHANGELOG](CHANGELOG.md) · [历史验收入口](docs/HISTORY.md) · [WorkBuddy 源码审核](docs/V02_WORKBUDDY_REVIEW.md)

自有代码采用 [MIT](LICENSE)，第三方见 [声明](THIRD_PARTY_NOTICES.md)。反馈请使用 [Issues](https://github.com/lunxianle666/Landscape-Agent-Pack/issues)，提供版本、软件组合、复现步骤和脱敏错误；不要上传凭据、私人配置或未获授权的项目图纸。
