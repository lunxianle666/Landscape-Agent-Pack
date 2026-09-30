# Changelog

## v0.2.0 — release preparation, 2026-09-30

- Verified AutoCAD Core, Geometry QA, PDF plotting, CAD→SketchUp Bridge,
  SKP persistence and save/close/reopen/readback on the tested workstation.
- A/B/C real landscape production chains and numeric/visual QA passed with
  explicit semantic warnings; clean SketchUp restart and Bridge reconnect passed.
- Fixture ownership is based on explicit creation records and COM identity;
  existing pre-test documents survive teardown. Ownership regressions: 10 PASS.
- Windows clean checkout / isolated venv validation: PARTIAL_FRESH_ENV.
- WorkBuddy source review complete: autocad-com-automation DUPLICATE,
  cad-geometry-qa REJECT, landscape-sheetset-pipeline DEFER,
  landscape-visual-qa ACCEPT_WITH_CHANGES. No whole Skill was copied.
- TEXT/MTEXT/DIMENSION/HATCH semantics are not fully preserved. Circle/Arc/bulged
  polyline support is tessellated/partial; wide-line centerlines do not preserve
  full width semantics. SPLINE/ELLIPSE/XREF/arbitrary 3D remain unverified.
- No full lossless CAD conversion, finished 3D landscape generation, pristine
  machine installation or all-version AutoCAD/SketchUp compatibility claim.
- Deterministic official v0.2.0 package is rebuilt from the release-prep commit.
  RC1/RC2/RC3 and their historical evidence remain intact. No remote publication.

### Historical prerelease records

The entries below describe their original checkpoints; later source recovery
and production acceptance are recorded above and in the final release notes.


## v0.2.0-rc3 — local ownership safety candidate, unpublished

- Remove inferred ownership and default-document dismissal from the CAD fixture.
- Record the fixture-created document reference and pre-test COM identities;
  close only the proven owned document and verify existing references survive.
- Retain uncertain or dirty documents with cleanup warnings. Attaching to or
  launching AutoCAD grants no document ownership; no application shutdown added.
- Add ten ownership regressions and an isolated live create/save/close/reopen
  check, including preservation of an existing PaperSpace document.
- Preserve RC1/RC2 archives; generate an independently verified deterministic
  RC3 package. Bridge and production validation implementations are unchanged.
- RC2 production evidence and its capability/fresh-environment limitations remain
  valid. No main merge, push, tag or release publication.

## v0.2.0-rc1 — local review candidate, unpublished

- Add bounded authenticated Ringo protocol 3 client; submitted mutation failures
  retain unknown outcomes and are never replayed automatically.
- Complete real native DWG import, Chinese SKP save, File New, disk reopen and
  numerical readback; verify 147 edges, units, tags, coordinates and curves.
- Replace Model-ID closure assumptions with actual path/reference checks for
  SketchUp 2023; run Save/Close/Open outside Ruby transactions.
- Add same-source CAD geometry QA/PDF/SU persistence regression, real server
  rejection/timeout tests and failure-only unit transport tests.
- Require finite bridge tolerances and bounded COM read retry in fixture
  preflight. Phase 2/3 implementation remains unchanged.
- Add explicit-version tracked-file manifest generation and deterministic,
  independently extracted candidate packaging. Runtime evidence is excluded.
- WorkBuddy review DEFER: handoff source absent. Formal design review,
  cross-machine installation and arbitrary production CAD remain unverified.
- No main merge, tag, push or release publication.

## v0.1.0-beta

### Added

- 版本化 manifest、关键文件 SHA-256 与目录校验；独立 ZIP 解压验证和 ZIP checksum。
- 完整性 8 项回归、可追溯本机验收 runner、陌生用户安装与人工客户端配置说明。

### Fixed

- 默认安装因既有不同 Skill 中止：保留原件并暂存新 Skill、明确 WARN。
- 规则缺失误报 PASS：校验退出码传播至最终诊断 FAIL。
- 规则内容变化无法检测：比较发布期 SHA-256，缺失、单字符修改及空文件 FAIL。
- PowerShell 5.1 中文编码与子进程 hash 兼容问题；重复安装安全复用。

### Verified scope

- AutoCAD 2025 核心 MCP/COM 链、Guard、真实 DWG 保存关闭重开、独立 Python COM 几何回读。
- 11 项安全回归与 8 项完整性回归。
- 本机既有兼容 Ringo 下 SketchUp 2023 box 保存关闭模型重开通过。RC2 的简单 DWG→SKP 历史通过不替代本轮结果。

### Known Limitations

- 全新 Windows、中文 Windows 账户、完整权限/依赖异常矩阵及其他 Agent 未验收。
- 客户端配置人工 merge / backup / restart；新安装后真实 Skill/MCP 重载 MANUAL TEST REQUIRED。
- 不覆盖升级旧版本，无复杂事务自动回滚；失败保留并列写入范围。
- 复杂景观、全局曲线验收 Experimental；未分发本机 Ringo schema 修改。
- 本轮简单 DWG 原生 UI 导入未产生可验收参考实体：FAIL / REVIEW REQUIRED，原因未确认，未继续替代建模。SketchUp 整体 Experimental；不承诺当前 DWG→SKP 可用。
- 传递依赖未全量锁定；manifest 不是签名；AutoCAD 重绘 Skill 授权未定，不分发。
