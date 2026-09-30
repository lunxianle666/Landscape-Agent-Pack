# 已测环境与证据范围
历史实测：Windows、AutoCAD 2025、Python 3.12.10 x64、AutoCAD MCP Pro 1.5.1、SketchUp 2023 / 23.0.367、Ringo 1.3.2。

2026-09-18 的 AutoCAD 基础与景观压力测试报告为 PASS_WITH_ISSUES，Layout/PDF 子项 PARTIAL。2026-09-17 的 CAD→SketchUp 压力测试总体 PARTIAL，详见 Skill 内匿名摘要。

这些是历史证据，不是所有用户环境保证。本轮安装演练、连接与临时 DWG 结果见 RC1.1 构建报告 docs/RC1_1_BUILD_REPORT.md 及 tests/evidence/rc1.1-summary.json。未修改 Ringo 官方版本与另一台 Windows 尚待验收。

## v0.2.0 — 2026-09-30
Windows / Python 3.12.10 / AutoCAD 2025 / SketchUp Pro 2023 23.0.367 / Ruby 2.7.2 / existing locally compatible Ringo 1.3.2. AutoCAD Core, Geometry QA, PDF plotting, native CAD→SU and SKP save/close/reopen/readback have local evidence. A/B/C real production chains and visual QA remain PASS_WITH_WARNINGS for semantic limitations. Clean SketchUp restart/reconnect and fixture ownership safety passed. Clean checkout / venv validation is PARTIAL_FRESH_ENV, not pristine-machine installation, unmodified Ringo validation or all-version compatibility. Codex desktop discovery/config reload remains unverified. See V02_RC2_ACCEPTANCE.md, V02_RC3_OWNERSHIP.md and final V02_RELEASE_NOTES_DRAFT.md.
