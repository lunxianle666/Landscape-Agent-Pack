# AutoCAD 1.5.1 Agent Guard Layer
这些规则来自本机实验，不修改 MCP 源码。

| 操作 | 已发现风险 | Agent 必须检查 |
|---|---|---|
| Trim / Extend | 快速模式曾剪错对象或静默空操作；经典模式的保留/删除侧语义有风险 | 默认不用于核心几何；只在副本和明确选择上测试并回读 |
| drawing_close / open | RPC_E_CALL_REJECTED 可能是假失败 | 核实文档集合、路径和状态；禁止盲目重试下一活动文档 |
| system_get_variable / set_variable | Application/Document 调用问题，设置可能失败 | 在授权目标 Document 独立回读；默认值正确不能证明设置工具成功 |
| drawing_save_as | 曾保存成 AC1015 老格式 | 优先 drawing_save；核实文件头与目标版本 |
| DXF 导出 | 活动文档可能变化 | 比较导出前后 ActiveDocument，全程核实目标 |
| Layout/PDF | Beta，冷重开空白、视口异常 | 单独验收，失败保留 PARTIAL |
| 截图 | 捕获异常或不稳定 | 不以截图证明几何正确 |
| 保存 | 内存成功不等于磁盘持久化 | 保存后重开核对实体、参数、单位和来源 |

RAW 保持原样，只在 CLEAN 修改；记录每项修复与理由。歧义几何标记 REVIEW_REQUIRED，不猜测。源 DWG 实体是 CAD→SketchUp XY 唯一基准，曲线采样误差与线性误差分别报告。

RC1 新发现：entity_create_polyline / circle 在独立 venv 的 AutoCAD 类型包装中返回 Color 属性缺失。工具可能已创建实体，Guard 必须动态包装目标实体并核查实际状态，不能盲目重试，也不能把原工具 FAIL 改成 PASS。RC1 原始测试曾为 PARTIAL；RC1.1 七类对象的后验验证与错误原文见 tests/evidence/creation-reproduction.json。临时绘图仅允许文档集合为空。

RC1.1 创建策略：Line/Polyline/Circle/Text/Block/Hatch/Dimension 通过自有 creation_guard.guarded_create 包装，先快照后调用、一次创建后核查。新增句柄与关键几何匹配且原工具报错时 SUCCESS_WITH_FALSE_ERROR；保留错误，禁止重复创建。无法确认则 REVIEW_REQUIRED 或真实无实体失败，不自动 Fork 或重试。
