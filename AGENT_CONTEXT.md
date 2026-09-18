# AGENT_CONTEXT.md · Landscape Agent Pack 规则入口

> 本文件是 Landscape Agent Pack 给 Agent 的**唯一规则入口**。任何支持本地 MCP 的 Agent（Codex / TRAE / 其他）在执行 AutoCAD 或 SketchUp 任务**之前**，必须先读本文件，再按第 2 节读取规则文件。规则不是自动拦截层，Agent 必须实际读取并遵守。

## 1. 项目作用与默认工作流

Landscape Agent Pack 是 AI Agent 与 AutoCAD / 可选 SketchUp 之间的景观工作流层。它提供规则、安全检查和验收顺序，不替代 AutoCAD，也不自带 CAD 引擎。

- **默认工作流：AutoCAD-only（独立成立）**。本机有合法 AutoCAD + 已配置的 AutoCAD MCP Pro 即可完成模型空间绘图、保存、关闭、重开与几何复核。
- **可选后续：CAD → SketchUp**。仅当用户明确要求、且 SketchUp / Ringo 通过本机环境检查时才进入。Node / Ringo / SketchUp 缺失**只影响可选 SketchUp，不影响 AutoCAD 主链**。

## 2. 执行前必读规则文件

按顺序读取（相对本 Pack 根目录）：

1. `standards/autocad-safety-rules.md` — AutoCAD 操作风险与必读检查项。
2. `standards/landscape-workflow.md` — 统一工作流与状态判定（PASS / WARNING / FAIL / PARTIAL / REVIEW_REQUIRED）。
3. `guards/README.md` — Creation Guard 用法。
4. `docs/LIMITATIONS.md` — 当前 RC 限制。
5. `docs/THREE_STEP_CHECK_CN.md` — 三步验收清单。

用户明确要求 CAD→SketchUp 时，再读 `skills/sketchup-from-cad-landscape/SKILL.md`。

## 3. 执行硬约束

- **先读后做**：未读完上述规则不开始绘图或修改。
- **重要 DWG 先复制**：不直接改用户唯一正式 DWG；RAW 源文件保持原样，修改只在新文件或 CLEAN 副本。
- **创建必走 Guard**：Line / Polyline / Circle / Text / Block Ref / Hatch / Linear Dimension 必须经 `guards/creation_guard.py` 的 `guarded_create` 包装，传唯一 `operation_id`；`SUCCESS_WITH_FALSE_ERROR` 表示对象已核实创建但原 MCP 报错仍保留，**禁止重复创建**。
- **保存≠持久化**：保存后必须关闭并重开，回读实体、参数、单位，确认磁盘 DWG 正确。
- **不自动关闭用户图纸**：检测到用户已有打开文档时，测试类操作拒绝继续。
- **Layout / PDF 是 Beta**：截图不稳定，不以截图代替几何验收；不为自动出图无限调试，先交付正确模型空间 DWG。
- **歧义即 REVIEW_REQUIRED**：缺单位、缺边界、语义不明时询问用户，不猜测。

## 4. Guard 的真实能力边界（防止虚假声称）

- Guard 是**调用包装 + 后验检查**，不是 MCP 自动中间件。
- 配置仍直连上游 MCP；绕过 `guarded_create` 的原始 MCP 调用**不会被自动拦截**。
- Guard 的重复操作凭据只在当前进程内有效，重启后要重新核查句柄。
- 因此 Agent 输出 `rules_loaded=true` 只表示"规则文件已读取"，**不表示 Guard 已经成为 MCP 自动拦截层**。

## 5. 规则加载确认格式

Agent 读完规则后，开始任务前必须输出：

```text
LANDSCAPE_AGENT_PACK_CONTEXT
mode=autocad
rules_loaded=true
guard_policy_loaded=true
autocad_mcp_required=true
sketchup_optional=true
```

进入 CAD→SketchUp 时把 `mode` 改为 `cad-to-sketchup`。任何文件读不到就如实写 `rules_loaded=false` 并说明缺哪份，**不要伪造 PASS**。

用户也可以随时运行只读校验：

```powershell
python installer\verify-rules.py
```

## 6. 为什么普通聊天 AI 不能直接画图

普通豆包网页聊天、普通对话 AI 只能给建议。要真正操作本机 AutoCAD，必须满足：支持本地 MCP 的 Agent 环境 + 已配置 autocad MCP 服务 + 打开的合法 AutoCAD。只发仓库链接不会自动获得这些能力。
