---
name: sketchup-from-cad-landscape
description: 根据真实景观 CAD/DWG 总平建立 SketchUp 基础模型，用于景观设计、场地模型和 CAD 总平转 SU。复用已有 AutoCAD workflow、COM、Ringo MCP 和 Ruby API，执行预检、保留原图、安全清图、原生导入、曲线精度检查、分阶段恢复及保存重开验收。
---

# 景观 CAD → SketchUp 生产 SOP

本 Skill 只编排既有能力，不提供新控制层。默认顺序：PRE-FLIGHT → Audit → CLEAN → Native Import → CAD_REFERENCE → 确定部分三维化 → Curve Fidelity → Block/Component → Health/Overlay → Save/Reopen → Report。先暴露系统问题，局部设计歧义不妨碍确定部分。用中文简洁沟通，将待确认问题合并，先读 CAD 信息再询问缺失参数。

## 依据与工具

匿名化历史验证摘要见 `docs/TESTED_ENVIRONMENT.md`，已知限制见 `docs/LIMITATIONS.md`。历史结果不是每个新项目的验收结果，原始私人报告与固定示例脚本不随本仓库分发。需要追溯当前项目时，读取该项目授权的审计与验证记录。

采样偏差不是经证明的全局 Hausdorff 上界；历史 PARTIAL 不改写为 COMPLETE。新 SOP 的面积阈值不追溯改写旧报告评级。固定示例几何脚本不当作任意 DWG 通用生成器运行。

- 先阅读当前环境已有的 AutoCAD automation workflow/skill，组合其 Source DWG profiling/audit workflow；本任务不默认重绘原图。历史环境使用 `autocad-dwg-redraw`，本 Pack 的该第三方 Skill 授权尚待确认，当前不分发其源码。若没有该 Skill，使用具有同等源实体审计能力的既有 AutoCAD automation workflow。避免无条件调用 `--restart-autocad`，保护用户未保存文档。
- AutoCAD + Python/pywin32 COM：提取真实 ModelSpace、实体与 Block 数据，在 CLEAN 操作。动态核实实际 Python 运行时，避免 WindowsApps 占位程序。AutoCAD 2025 为实测版本，不代表其他版本已验证或必然不兼容。
- 外部依赖 [Ringo-Sketchup-MCP](https://github.com/Ringophilia/Ringo-Sketchup-MCP)，由 Ringophilia 项目维护；历史实测 1.3.2，本项目只引用，不提供其控制层或代码。先调用 `bridge_status`，确认 profile_id/profile_name/port 对应目标实例，再 `model_get_info` 确认路径、单位、编辑上下文、能力；未确认实例不得写入。
- 连接拒绝先检查 SketchUp 是否还在欢迎页，以及既有 `扩展程序 → Ringo SketchUp MCP → Start Server` 是否启动。根据当前实例动态确定 profile/port，不假定本机默认值。Ruby 可用性须按上游文档和当前 bridge 状态检查；历史测试曾以进程环境 `SKETCHUP_ENABLE_RUBY_EVAL=1` 临时启用，不能据此假定持久配置开启；仅在已有授权下按既有方式启用，随后回读能力，不输出连接 token。
- SketchUp 2023 实测版本 23.0.367；通过既有 MCP 通用工具、`sketchup_run_ruby` 与 SketchUp Ruby API 使用原生 DWG importer，不添加模型专属服务器接口。Ruby 能力须以当前状态为准，不能凭安装存在推定已启用。历史测试使用本地 Node Schema 兼容修复，细节见 Tested Environment，不把未经修改的所有客户端组合宣称已验证。
- 动态发现 AutoCAD、SketchUp、Python 与 MCP 的安装位置，结合用户提供的项目目录确定输入输出。正常时不重装、不回滚兼容修改、不重写底层、不重跑大型压力测试。
- COM 权限要匹配 AutoCAD 进程；通用 ProgID 不可用时核实当前版本的 ProgID，历史 AutoCAD 2025 使用 `AutoCAD.Application.25`。权限故障不等于 DWG 损坏；必要时沿已有提升方式运行受限操作。COM Documents 包装异常可重新 dynamic Dispatch，勿重启并丢失有效成果。

## CHECKPOINT 0：PRE-FLIGHT CHECK

收到 DWG 后禁止立即完整建模。先只读保护 RAW，记录绝对路径、大小、修改时间及可行时 SHA-256；禁止对 RAW 清图或保存修改。后续所有 CAD 修改只在 `<project>_SU_CLEAN.dwg`，已有同名文件须保护或采用合理版本名。

逐项检查并保存简短内部结果：

1. DWG 可正常打开；2. 单位明确；3. ModelSpace 正常；4. 图层可识别；
5. 主边界存在；6. 建筑/道路/铺装/水体等主体可识别；7. 严重自交范围；8. 大量断线范围；
9. 异常 Z；10. Block 可读；11. Arc/Circle/Spline 源参数可读；12. 世界坐标/大坐标合理；
13. 关键设计参数是否缺失；14. AutoCAD COM 正常；15. Ringo MCP 连通；16. SketchUp 2023 可控制；
17. 原生 DWG importer 可用；18. 输出目录可写。

importer 能力检查与 CP2 的小规模实际原生导入验证衔接，未真实验证不能声称该 DWG 导入通过。读取并记录 CAD 曲线参数、关键控制点与 Block 变换，避免到细部阶段才发现无法提取。启动软件不等于连接、导入或几何通过。

给出开工判断：

- `READY`：关键条件满足，继续。
- `READY_WITH_REVIEW`：局部缺高、语义歧义或可隔离对象，先做确定部分，汇总待确认。
- `BLOCKED`：读图/单位/COM/MCP/importer/主体几何等全局阻塞，或所有必要设计参数缺失；禁止大规模建模，立即说明根因及最小解决办法。局部曲线参数缺失只阻塞受影响对象。

CAD 是 XY 的唯一几何基准：位置、边界、半径、弧形、旋转、比例及相对关系来自实际实体。不得截图描摹、视觉猜测、修改设计边界或导入失败后凭提示词造替代图。
Z/高度优先级：CAD 明确标高 → 剖面/立面 → 设计说明 → 用户明确参数 → 已确认项目规则。冲突须确认；关键高度缺失标 `REVIEW_REQUIRED`，不猜高度，不因此停掉全部确定工作。

## CHECKPOINT 1：Audit + CLEAN

内部审计 Units/Layers/Handles；Line、LWPolyline/Polyline、Arc、Circle、Spline、BlockReference、Hatch、Text/MText、Dimension；闭合、重复、部分重叠、缺口、自交、Z 污染、图层语义冲突、短边、大坐标、Unicode 名称，以及 Block 插入/旋转/缩放。追踪 Handle/Layer/Type、源参数与完整嵌套世界变换，不仅记录包围盒。常规项目不输出巨大 Audit。

| 类别 | 行动 |
| --- | --- |
| `SAFE_AUTO_FIX` | 在 CLEAN 修复有语义证据的同层 exact duplicate；明确应闭合且 gap ≤0.1 mm；已确认二维边界的 Z 污染；隔离干扰 Hatch/注释。记录源 Handle、处理前后及依据，保持几何对应 |
| `REVIEW_REQUIRED` | >0.1 mm gap、部分重叠、图层冲突、不明确开放线、重复植物、相交功能边界、缺高度、墙中心线/边线不明：保留、隔离、等待确认 |
| `INVALID` | 严重自交、损坏或无法形成合法区域：隔离，不强制造面 |

`STOP GUESSING` 强制作用于具有多个合理设计解释的对象：隔离 → 记录 Handle/Layer/Type/候选解释 → 继续确定内容 → 合并询问 → 按用户确认继续。禁止默删重复植物、靠图层名字单独判定用途或凭缺口大小改变设计。Z 清零需证明二维语义，不能把明确标高当污染。

Hatch 不是默认三维边界；Text/MText/Dimension 在 CAD 用于读取设计信息，不作为 Face 边界，也不能依赖 importer 完整保留。隔离应保留来源信息。
短边在 CAD 阶段发现：实测 0.01 mm 可能丢失，0.05/0.5/10 mm 示例保留不构成通用保证。若涉及关键边界，先确认安全等效修复或阻塞该对象；不得统一删除短边或偷偷放大模型。
保存 CLEAN 与清图/待确认记录作为 CP1；SKP 阶段文件从 CP2 起创建。

## CHECKPOINT 2：Native Import + CAD_REFERENCE

用 SketchUp 2023 原生 DWG importer 导入 CLEAN。立刻核实单位、世界 Bounds、Tags、实体数量、完整 Transformation 与关键锚点/相对距离；解释过滤和离散导致的数量变化，不要求类型数量机械相等。导入位置、单位或主体失败时禁止继续大规模三维化；不得静默平移、缩放掩盖误差。

将实际原生结果放入独立可显示/隐藏的 `CAD_REFERENCE` Group/Component，默认保留至最终 SKP，与 MODEL 裸几何隔离。不能用重建曲线替换原生参考并冒称 importer 精度提高。缺失注释/空图层须区分 importer 丢失与后续补充空 Tag。
通过早期定位验收后保存有用的 CP2 SKP。

## CHECKPOINT 3：确定的主要区域与建筑

从实际 CAD/参考拓扑构建建筑、道路、铺装、水体、墙、台阶等确定部分，保留孔洞与多 Loop。形成 Face 先验证边界再按已确认 Z 三维化。正式对象为 Group 或 Component，内部边/面保持 Untagged，Tags 给容器。
按需要建立 `MODEL_BUILDING`、`MODEL_ROAD`、`MODEL_PAVING`、`MODEL_WATER`、`MODEL_WALL`、`MODEL_STEP`、`MODEL_TREE`、`MODEL_SHRUB`、`MODEL_FURNITURE`，不造无意义 Tags。
将源 Handle/图层、变换及参数来源关联到 MODEL 对象，保存主要区域有效成果。

## CHECKPOINT 4：Curve Fidelity + Block/细部

直线/Polyline 定位生产目标 **≤0.1 mm**。超过时查 Units、Transformation、Import、Geometry conversion，不简单接受或舍入结果。

关键 Arc/Circle/Spline、曲线道路、水体、弧形墙必须 `Curve Fidelity Check`。优先匹配原生边和拓扑；必要时只在 MODEL 重建，依据真实 CAD 参数：

- Circle：center/radius；Arc：center/radius/start/end angle/法向。
- Polyline 弧段：原始顶点、bulge、闭合状态与坐标系。
- Spline：实际可读 degree/control points/knots/weights/closed 等参数；不能假定每种 Spline 都能读取、按控制点连线冒充曲线或将 SU 离散 Edge 当 CAD 原始参数。
- 记录源 Handle、匹配参考 Edge IDs、世界变换、源参数、重建方式/公差，并标明 `curve reconstructed from original CAD parameters`；CAD_REFERENCE 仍保留原生结果。

默认关键硬质景观 **≤0.5 mm**，普通景观曲线 **≤1.0 mm**，用户更严要求优先。按半径/曲率/误差自适应分段，不统一 24/48/96，不无意义堆面数。圆/弧用弦高计算控制误差；同时核对端点、Bounds、双向采样点到连续曲线/折线距离，曲线道路/墙另查宽度/厚度截面。仅顶点一致不能证明弧中间精度。采样说明密度/方法与局限；Spline COM 控制点包络不一定是紧曲线 Bounds，不能直接将其差异定为世界坐标误差。

重要区域用实际 CAD Area ↔ SU Face Area（含孔洞扣减）验收，不用 bbox 面积：**≤0.1% PASS；>0.1% 且 ≤0.5% WARNING；>0.5% REVIEW/FAIL**。报告绝对 mm² 和百分比；面积通过不掩盖局部边界错误。面积缩放应用实际世界变换。

BlockReference → 可复用 ComponentDefinition + Instances，保持插入点、旋转、比例、定义身份和嵌套变换；通过几何/定义关联识别名称后缀 `#1`，不把它当乱码或新设计类型。不要全爆炸成独立高模。
树木/灯具/座椅等默认轻量 Placeholder，保证位置、类型及变换；只有用户提供组件才替换，不自动下载大量高模。重复植物有歧义保留待确认。数量分别报告 MODEL 与 CAD_REFERENCE，Group 定义、唯一定义及按路径展开实例不能混为同一统计。

## CHECKPOINT 5：Health + OVERLAY CHECK + Save/Reopen

检查 reversed faces、loose geometry、duplicate faces、expected solid 的合法性、empty groups、tiny edges、异常巨大 Bounds、Tags、组件与定义/实例数量。区分计划保留的二维面与应为实体的对象；实体底面的正常法向不当作反面错误。安全修复与待确认分开，不能为了健康统计默删歧义对象。
CAD_REFERENCE + MODEL 叠加检查以数值为主、视觉辅助；为使用需要保存参考/模型/叠加场景或视图，不机械要求每次完整压力测试输出。报告检查范围，局部重复面检查不宣称全部相交检测通过。

保存少量有用阶段版本，最终 `<project>_SU_MODEL.skp`，未授权不得覆盖已有模型。保存后真实关闭/重开该 SKP，回读 CAD_REFERENCE、Tags、Groups、Components、Bounds、关键尺寸/曲线、Block instances、变换与来源关联。事先保护用户其他未保存模型。
比较重开前后结构与关键几何，明确浮点容差；实测面法向/面积可能出现极小浮点变化，不把它误报结构损坏，也不靠舍入掩盖真实位移。确认磁盘文件与重开结果，不把 Save 返回成功当 Reopen 成功。
最后核对 RAW 路径/大小/mtime/hash 未变；缺少 hash 时说明替代证据，不能声称 hash 验证。

## 失败保护与恢复

- 任一阶段失败先保住有效成果，记录失败阶段/对象/错误与 AutoCAD、Import、Geometry、MCP、SketchUp 层；局部修复并复验，从最近 CHECKPOINT 继续，不因一个对象丢掉全部模型。
- MCP timeout 不证明未执行：先查实际状态/请求队列/对象数量再决定重试，防止重复对象。重连后重新确认实例、模型与会话引用。
- 用短小、可恢复的对象级操作；Ruby MCP 已包默认 transaction 时不要嵌套 `start_operation`。失败局部回滚/清理须证明对象属于本次失败，不删除既有成果。
- 单位错、非统一偏移、主体大面积造面失败、参考/模型错位、MCP 异常、模型损坏、CLEAN 非预期改图、RAW 被修改、曲线远超公差：停止扩大错误，先查根因。全局问题阻塞整体；局部问题隔离并继续其他已验证部分。根因不明不强制完成。

## 最终报告与状态

生产报告保持简洁：输入 DWG、CLEAN、Auto Fix、Review Items、MODEL Groups/Components、最大线性/曲线/面积误差及检查覆盖/方法、SKP、Reopen、RAW 保护结果、最终状态。未经测量写未验证，不引用历史误差冒充本项目数值。

- `COMPLETE`：约定范围完成，验收与重开通过，无未解决关键问题。
- `COMPLETE_WITH_REVIEW_ITEMS`：确定且约定可交付部分完成并验收，明确保留待确认对象/设计事项与影响，不把尚未建成必需内容写成完成。
- `PARTIAL`：必需部分未完成或局部验收未通过，但存在有效成果；说明已完成、缺失及恢复点。
- `BLOCKED`：全局条件不满足、不能继续；尽早说明阻塞与下一步。

最简调用：`$sketchup-from-cad-landscape 根据这个 DWG 建立景观 SU 基础模型。先预检，缺失设计参数合并询问，保留原图，最终保存并重开验证。`
