# LAP 维护审查 · 2026-11-16

审查基线：`main`、`origin/main` 和远程正式 tag `v0.2.0` 均指向 `ac378d8`；本机原工作区无未提交改动，忽略的历史记录保留。工作在 `codex/lap-maintenance-20261116` 的独立 Git worktree。提交 `2304b7c`（Phase 3）和 `5ebc8d4`（Bridge WIP）均在 main 历史。公开 [PR #1](https://github.com/lunxianle666/Landscape-Agent-Pack/pull/1) 尚在审阅，改动涉及 README、安装文档及清单，合并时需协调重叠内容并重新生成摘要。未改动该 PR。

## 组件与验证清单

| 位置 | 入口、依赖与成熟度 |
| --- | --- |
| `AGENT_CONTEXT.md`、`standards/`、`prompts/`、`templates/` | 规则入口、CAD 安全与景观流程、提示词、项目和报告模板。 |
| `skills/` | **1 个正式 Skill**：`sketchup-from-cad-landscape/SKILL.md`（固定 MIT 基线）；`autocad-dwg-redraw/PROVENANCE.md` 只记录来源，无可加载 Skill。 |
| `guards/` | `creation_guard.py` 对显式包裹的创建请求做去重/后验；`document-state-check.py` 核对文档，不是 MCP 中间件。 |
| `landscape_agent_pack/cad/` | `core`、`angles`、`annotation`、`retry` 负责经验证范围内的 COM；`geometry_qa` 检查离线 DXF；`plot` 出 PDF；`pdf_qa`、`visual_qa` 和 `delivery` 分别负责客观 PDF 检查、证据绑定和交付门禁。结果通过共享 `result.py` 表达。 |
| `landscape_agent_pack/bridge/` | 可选：`contracts`、`client`、`errors`、`validation`；`native_import.rb`、`sketchup_session.rb`、`persistence.rb`。依赖独立 SketchUp/Ringo 实例。 |
| `setup.bat`、`installer/`、`config/` | `install.ps1`、`check-environment.ps1`、`environment_probe.py`、`generate-mcp-config.ps1`、`verify-dependency.py`；独立 venv 与配置模板，不代写客户端配置。`build-manifest.py`、`verify-rules.py`、`package-candidate.py`、`build-v02-candidate.py` 为安装校验／打包工具。 |
| `tests/unit/` | 文档归属、Core/几何、Plot/PDF、交付证据、Bridge、视觉证据、Skill 与导入及文件清单。 |
| `tests/smoke/` | `test_*.py` 离线验证创建守护、文档守护、完整性。`smoke_test.py`、`reproduce_creations.py` 和 `acceptance_v2.py` 是需另行运行的现场工具。 |
| `tests/integration/` | `autocad_core_live.py`、`cad_delivery_live.py`、`bridge_fixture_cad.py`、`bridge_live.py`、`full_chain_live.py`、`production_cad_live.py` 与其 `production_types.rb`。需独立的真实软件环境。 |
| `tests/fixtures/`、`tests/evidence/`、`examples/` | 合成几何 JSON、历史脱敏证据摘要、离线 DXF 生成示例；私人图纸不分发。 |
| `.github/workflows/offline-tests.yml` | Windows / Python 3.12，语法、导入、测试、完整性和最小示例。无商业软件、无发布步骤。 |

## WorkBuddy 整合矩阵

指定候选目录不存在，未找到可用的 `HANDOFF_TO_CODEX.md`。已核对归档 SHA-256
`e7c9e97bb83f7d995925cef376c7f4edf53479dd925daf9c2b7c15cd81f56d70`，并检查恢复候选源码和本机 Skill 条目；五份恢复的 SKILL.md 与现存本机文件逐一比较，SHA-256 均吻合。移交包未发现明确的分发许可证；以下判定以读取源码、比对现有实现和证据为准，未执行候选的 COM 写入或清理脚本。详见 [此前源码审查](V02_WORKBUDDY_REVIEW.md)。

| Skill | 当前状态 | 与现有功能关系 | 是否整合 | 具体处理方案 | 验证结果 |
| --- | --- | --- | --- | --- | --- |
| `autocad-com-automation` | 候选；部分 Win/COM 配方有历史验证 | COM 附着、读重试、DIMSTYLE、DXF、PC3 已有；Leader、Ellipse 和字体度量是增量 | 不复制 | 复用 LAP Core；Leader 重试和标注降级可能重复写入；Ellipse 示例坐标约定不一致，字体常数需独立标定。拒绝杀进程/删锁。 | LAP 回归通过；候选新增配方未在本次上机验收。 |
| `autocad-com-automation-v1-stable` | 外部冻结快照 | 与主候选和 LAP Core 高度重叠 | 不整合 | 留作只读历史基线，不删除、不覆盖；冻结标签只代表当时的 WorkBuddy 范围。 | 读取冻结说明及源码；未执行其中的全局清理做法。 |
| `cad-geometry-qa` | 拒绝直接收录 | 基础越界、重复、退化已覆盖；图框栏位、极端曲线、前后边界与文字规则仍有增量 | 不复制 | 候选有项目硬编码、导入副作用、异常漏报、开放线收尾和顶层状态问题。保留合成用例思路，本轮修复 LAP 自身漏判。 | 离线 DXF 正/反例通过；不视为候选脚本验收。 |
| `landscape-sheetset-pipeline` | 推迟 | LAP 有单图/多 PDF 校验，但没有 Mother Plan 驱动的跨图派生 | 暂缓 | `wb_cad`、`wb_common`、builder 缺少可独立验收的分发闭环；11 幅锚点、节点索引、标高和图框资料与原项目绑定。未来先做一个双图合成项目。 | 仅复核历史报告和流程；候选未独立运行。 |
| `landscape-visual-qa` | 关键原则已吸收 | LAP 已把实际渲染复核与数值判断拆开；视觉记录绑定源文件和图片 SHA-256 | 已有实现；不添加重复 Skill | 保留现有记录器；固定缺陷数量、主观硬评分和项目标定阈值不移植。 | 证据篡改、未审、失败观察和警告保留已测；本轮未重做 A/B/C 人工视觉。 |

附带 `landscape-design`、实验几何、历史回归套件与视觉代理脚本也已识别。设计说明与工作流标准部分重叠；回归/代理脚本使用特定图框常数、共享依赖或历史基线，未移植。候选源码没有进入此分支。

## Bridge 证据与技术边界

`5ebc8d4` 的 `EXPERIMENTAL / BLOCK_BRIDGE / NOT ACCEPTED` 是历史冻结。后续版本引入带认证和限时的 Ringo 客户端、显式工作区/来源 hash/毫米单位校验和 SKP 保存、File New、磁盘重开。读回时 Ruby 将世界变换后的英寸内部坐标转换成 mm；原生导入保留坐标原点并核对 CAD 图层 / SU Tags。详见 [历史 WIP](PHASE4_BRIDGE_WIP.md)、[验收记录](V02_RC2_ACCEPTANCE.md) 与 [文档归属回归](V02_RC3_OWNERSHIP.md)。

本轮复核了既有现场结果与磁盘产物：冷启动 fixture 16 项通过、SKP SHA-256 与结果一致；A/B/C 三份结果仍是 `PASS_WITH_WARNINGS`，各自有原生导入、正常关闭模型、重开、持久化以及源文件不变的记录。MM、坐标、Tags、采样几何与存盘前后数值属于此次历史证据范围。弧/圆经过离散，宽多段线会变轮廓，注释/填充/标注语义不能保证。绘图可能含重合边，单向采样不能证实一一对应或完整拓扑。

本分支没改 Ruby 导入与保存实现，也未把 Bridge 接入默认 AutoCAD 流程。本轮检查时桌面软件及目标监听未运行；发现的候选 CAD/SU 可执行文件签名校验均为 `HashMismatch`，未执行。故本分支真实软件 E2E 为 **NOT EXECUTED**。使用可信软件/兼容扩展、明确归属的空白测试文档和授权的隔离目录，按 [复现命令](V02_BRIDGE.md#reproduction) 重新完成 CAD→导入→SKP 保存→正常关闭→磁盘重开→几何验证。DXF importer、任意 3D、XREF、复杂曲线、完整建模保留在未验证或实验范围。

## 本轮验证

- 干净 worktree 中新建 Python 3.12 venv，从上游安装固定的直接开发依赖；
  语法检查、导入、Skill 结构、DXF/PDF 合成数据和 Windows 路径测试均走此环境。
- 历史证据只读回放：当前校验器使用已记录的 before/after 读取冷启动 fixture（147 条边）
  和 A/B/C（6655/5917/3777 条边），回读最大坐标变化均为 0 mm；三份历史真实 DXF 和 PDF
  也用本分支检查器离线复跑通过。没有重新执行 CAD/SketchUp 或生成新 SKP。
- 测试替身用于 COM 文档归属、DWG lifecycle 证据和 Ringo 错误响应等；这些测试不能证明商业软件链已运行。

## 风险与后续

- **P0（下个稳定版本前）**：合并时协调 PR #1；在可信 AutoCAD/SketchUp 环境重跑 CAD 交付和完整 Bridge 流程，核对真实 PDF 交付及 SKP 持久化门禁；让当前提交的 Windows CI 跑绿。在把 PDF 栈作为预装、托管或分发能力前按 [上游条款](../THIRD_PARTY_NOTICES.md) 确认方案。
- **P1**：在独立 Windows 环境验证安装器、首次客户端发现和未修改的上游 Ringo；记录下限版本和失败恢复。关注角度/短边、宽线和 DXF 的可测范围；COM 同进程阻塞不意味着可安全取消。现有工具保留失败运行产物；每次运行使用新目录，通用 Result.write 和固定报告名没有统一的不覆盖保证。
- **P2**：先定义 Mother Plan 与双图锚点的输入输出契约再做多图幅；通用右栏侵入/前后边界、Leader/Ellipse 与自动化视觉代理据合法可复现数据单独验收。复杂三维或 NX/CAM 另外规划。

关键字扫描未发现常见格式的 API Token 或私钥；扫描不能证明没有所有凭据。此次仅脱敏当前维护树里的账户路径和本机绝对位置，历史对象及旧版 ZIP 未重写。开发分支的清单版本与正式版分开。
