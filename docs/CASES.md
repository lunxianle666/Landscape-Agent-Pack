# 验收案例：输入、操作与证据边界

这些案例整理自已公开的历史验收记录，是 v0.2.0 正式版的证据索引，不是本次文档维护新增的 CAD/SU 测试。结论保留原记录的限定范围。正式版身份见 [Release](https://github.com/lunxianle666/Landscape-Agent-Pack/releases/tag/v0.2.0)。

## 案例 1：三个景观总平的 CAD→SketchUp 参考几何链

- **输入**：A 街角口袋公园、B 居住区中庭、C 滨水湿地公园的正式 DWG 副本，单位 mm；源实体数分别为 392 / 117 / 249。输入文件未公开。
- **操作**：隔离工作目录，记录源哈希；源 DXF 数值 QA、实际 PDF 出图、原生 DWG 导入、保留 CAD_REFERENCE、保存 SKP、File New、磁盘重开与回读。
- **输出**：历史运行生成 PDF、SKP、数值报告及绑定源文件/图像哈希的视觉检查记录；这些产物位于未分发的 runs，仓库没有提供对应截图或演示。
- **验证方法**：前后源哈希不变；单位/边界检查；A/B/C 分别采样 18723 / 7575 / 5502 点；保存前后坐标、数量、Tags 与元数据比较；另行检查 CAD PDF 栅格图及 SU 顶视图（C 另有轴测图）。
- **结果**：三条链均为 **PASS_WITH_WARNINGS**。A/B 最大采样距离约 0.642496 / 0.856661 mm，满足当次 1 mm 容差；C 宽线中心线原始最大差 1500 mm 保留警告，另行边界抽样匹配不能替代宽度语义。三者重开回读坐标无实测变化（容差 1e-6 mm）。SU 技术视觉 QA 为 **VISUAL_PASS_WITH_WARNINGS**，注释/填充丢失仍可见。
- **边界**：采样为单向源到导入边的距离检查，重合边可能掩盖缺失实体；不是一一对应、完整拓扑或全局曲线证明，也不是设计审批或成品三维建模。

公开依据：[RC2 production / visual QA 记录](V02_RC2_ACCEPTANCE.md)。该摘要披露源哈希与测量方法，但没有公开源图、完整运行 JSON 和所查看图像，无法从本仓库完整复现 A/B/C 历史结果。

## 案例 2：最小夹具与用户文档保护

- **输入**：代码生成的八实体 mm 夹具、独立测试工作目录与已保存的空白 startup.skp；另一个隔离测试使用含一条 PaperSpace 线的既有文档替身。
- **操作**：显式创建并记录测试文档 COM 身份；生成 DWG/DXF；原生导入与 SKP 保存/重开；关闭操作只针对能证明归属且干净的文档。存在既有文档时拒绝创建夹具。
- **输出**：历史运行记录 DWG/DXF/SKP、回读结果和 ownership-audit.json；运行产物未公开。
- **验证方法**：八实体及 INSUNITS=4 回读；检查既有文档 COM 身份和 PaperSpace 线句柄仍在；十项 ownership 单元回归检查拒绝、保留和归属判定。Bridge 最小回归还检查导入单位、坐标及持久化。
- **结果**：历史限定环境中的归属保护与最小回归通过；不扩大 CAD 实体支持。独立 venv/checkout 演练仍为 **PARTIAL_FRESH_ENV**，Codex 桌面发现与配置重载未验证。

公开依据：[RC3 ownership 记录](V02_RC3_OWNERSHIP.md)、[RC2 冷启动与 fresh environment](V02_RC2_ACCEPTANCE.md)。相关代码为 [CAD 夹具](../tests/integration/bridge_fixture_cad.py)、[Bridge 检查](../tests/integration/bridge_live.py)、[归属单元测试](../tests/unit/test_fixture_ownership.py)。具备合法桌面软件、兼容插件、授权配置和自备空白 SKP 后，可按 [最小工作流](V02_BRIDGE.md#reproduction) 做新的限定验证；公开代码不等于已证明跨机器完整复现。

## 如何阅读更早的记录

[Beta 验收](BETA_ACCEPTANCE.md) 和 [独立 Skill 匿名压力测试](../skills/sketchup-from-cad-landscape/docs/TESTED_ENVIRONMENT.md) 分别属于旧 Beta 与 2026-09-17 独立组件，包含 FAIL / PARTIAL 等原始结论；不能用 v0.2.0 的后续结果反写它们。版本关系见 [历史说明](HISTORY.md)。
