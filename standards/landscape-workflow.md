# 统一景观工作流

默认工作流是 **阶段 A：AutoCAD-only，独立成立**。阶段 B 是用户明确要求且 SketchUp/Ringo 可用时才执行的可选后续；Node / Ringo / SketchUp 不是 AutoCAD 主链的前置条件。

## 阶段 A：AutoCAD-only（默认，独立完成）

项目简报 → 只读预检 → RAW 哈希与来源记录 → CLEAN 副本 → 景观基础绘制/清图 → 独立几何核查 → 保存 → 关闭 → 重开 → 分项验收。

## 阶段 B：CAD → SketchUp（可选后续）

在阶段 A 完成的 CLEAN DWG 上：原生 DWG 导入 SketchUp → CAD_REFERENCE / MODEL 分离 → 确定部分三维化 → 保存重开 → 报告。未明确请求时不启动、不连接 SketchUp。

单位、场地边界、尺寸、公差、图层含义和设计参数须有依据。缺少数据或多种语义时 REVIEW_REQUIRED。公开示例几何只能用于测试，不能代替任意输入 DWG。状态分别为 PASS / WARNING / FAIL / PARTIAL，不以平均分隐藏失败。
