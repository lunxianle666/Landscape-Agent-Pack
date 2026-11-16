# 历史版本与验收记录

当前使用请从 [首页](../README.md) 和 [v0.2.0 安装指南](INSTALL_WINDOWS.md) 开始。本页只解释历史版本，不将旧安装/测试状态作为当前能力结论。

## 已发布的历史 Beta / RC

| 版本 | 远程状态 | 对应提交 | 历史入口 |
| --- | --- | --- | --- |
| v0.1.0-beta | GitHub prerelease | `d3295bf58402e84c09800460d86ab74dd9f9a342` | [附件与发行说明](https://github.com/lunxianle666/Landscape-Agent-Pack/releases/tag/v0.1.0-beta)、[原版安装指南](https://github.com/lunxianle666/Landscape-Agent-Pack/blob/v0.1.0-beta/docs/INSTALL_WINDOWS.md) |
| v0.1.0-rc2 | GitHub prerelease | `4f61fe1201ea0b87cfa1cdff03c5da50c82b67d5` | [附件与发行说明](https://github.com/lunxianle666/Landscape-Agent-Pack/releases/tag/v0.1.0-rc2) |
| v0.1.0-rc1 | GitHub prerelease，附件为 RC1.1 Windows 包 | `8b9225ac665f5dfd3f5144b93a3eb7e799f445b6` | [附件与发行说明](https://github.com/lunxianle666/Landscape-Agent-Pack/releases/tag/v0.1.0-rc1) |

截至 2026-10-30，当前正式 Release 为 [v0.2.0](https://github.com/lunxianle666/Landscape-Agent-Pack/releases/tag/v0.2.0)，Tag 解引用为 `ac378d84ce4bbb9489ee4664b0db3e498e0359fa`。v0.2.0-rc1/rc2/rc3 是本地候选检查点，不是上述 GitHub Release；不要混淆两个系列的 RC2。

## 旧 Beta 安装步骤（仅用于历史排错）

从 Beta Release 获取 `Landscape-Agent-Pack-v0.1.0-beta.zip` 与 `.zip.sha256`，比较 SHA-256 后完整解压，按包内安装指南操作。不要把 Beta 改名为 v0.2.0，或混用不同版本的 manifest、规则与附件。需要保留历史安装时使用独立短目录，例如：

```powershell
.\setup.bat -InstallRoot 'D:\AI-Tools\Landscape-Agent-Pack-beta'
.\setup.bat -InstallRoot 'D:\AI-Tools\Landscape-Agent-Pack-beta' -DiagnosticOnly
```

客户端仍需人工备份、合并单个 MCP 服务节并重启验证。历史 `-RunGeometrySmoke` 会生成真实 DWG；需先自行保存关闭已有 CAD 文档。Beta 的 SketchUp box 通过不等于 DWG→SKP 通过，当次简单 DWG 原生导入仍为 FAIL / REVIEW REQUIRED。详见 [Beta 验收原文](BETA_ACCEPTANCE.md)。

## 历史证据如何适用于正式版

- [v0.2 早期验收](V02_ACCEPTANCE_REPORT.md)、[恢复审计](V02_RECOVERY_AUDIT.md)：保留各检查点当时的状态，后续结论按 RC2/RC3 与正式发行说明阅读。
- [v0.2 RC2](V02_RC2_ACCEPTANCE.md)：正式版引用的生产参考几何、视觉 QA、冷启动和 PARTIAL_FRESH_ENV 证据；文中“未发布”描述当时检查点。
- [v0.2 RC3](V02_RC3_OWNERSHIP.md)：正式版引用的夹具归属安全证据；没有重跑 RC2 大项目，也没有扩大实体支持。
- [v0.2.0 正式发行说明](V02_RELEASE_NOTES_DRAFT.md)：汇总上述范围；旧文件名为链接兼容保留。
- [独立 Skill 基线](SKILL_BASELINE_REPORT.md)：采用公开提交 `cc28ffd4b9daea890fbe78fd3737c9669d042446`，其 2026-09-17 压力测试仍为 PARTIAL，不能升级为 Pack 的全功能保证。

历史验收原文和已发布附件不在本次维护中改写或替换。后续文档提交和重新计算的源码校验清单也不改变正式 Tag/ZIP 的身份，见 [完整性约定](INTEGRITY.md)。
