# Landscape Agent Pack 是怎么工作的？

你提出设计意图，AI负责理解与规划，Agent负责操作软件，Landscape Agent Pack提供景观工作流与安全规则，MCP负责连接AutoCAD或可选的SketchUp。AI再根据实际文件检查结果，你决定是否继续修改。

## 核心架构

```text
用户：想法、要求与最终选择
↓
AI Model：理解、设计与执行规划
↓
Agent：本机工具与操作执行
↓
Landscape Agent Pack：景观工作流与安全规则
↓
MCP：AutoCAD MCP Pro / 可选 Ringo
↓
AutoCAD / 可选 SketchUp
↓
实际结果：DWG / 模型与测量证据
↓
AI检查和继续修改（受用户确认的目标与范围约束）
↕
用户反馈、确认与验收
```

这是职责示意图，不是所有调用必须经过的技术代理链。Pack的规则指导Agent如何操作，MCP才是软件连接；遵守规则需要Agent实际读取并执行。当前配置仍直接连接上游MCP，Guard要显式使用，不能自动拦截绕过它的原始调用。

在Codex / TRAE等客户端中，AI Model与Agent Runtime通常在同一个客户端内协作。用户可以在同一段对话中讨论、确认、执行，不需要人为拆成两个软件或反复搬运提示词。如果分开使用聊天AI和本机Agent，需要把确认后的要求、尺寸、保留对象和验收方式完整交给执行端。

## 各角色做什么

| 角色 | 你可以怎样理解 | 职责 |
|---|---|---|
| 用户 | 设计意图的提出者 | 提供场地条件、想法、约束、不能修改的内容与最终目标，选择方案并验收 |
| AI Model | 理解与规划的部分 | 理解要求，提出景观方案、合理参数和假设，安排执行顺序，读取Agent证据，判断问题并提出修改 |
| Agent | 有本机工具权限的执行环境 | 按授权运行终端、读写文件、调用MCP、操作软件并返回实际结果 |
| Landscape Agent Pack | 专业工作流层 | 提供景观执行顺序、图层组织与Block使用原则、Guard、安全检查、保存重开与验收规则，以及可选CAD→SketchUp工作流 |
| MCP | 连接专业软件的工具接口 | AutoCAD MCP Pro连接AutoCAD；Ringo SketchUp MCP连接可选SketchUp |

用户不需要学COM、pywin32、MCP函数名或AutoCAD ActiveX。直接说设计任务即可。Pack提供工作流原则与有限验证实现，不意味着已内置所有项目的标准图层库、构件库或通用景观自动检查器。

AI模型可以是GPT、豆包、Claude、Gemini等符合所用Agent要求的模型。模型能否在某个客户端使用，由该客户端的实际支持决定；本项目不提供模型服务，也不保证任意组合都可用。

## 三个使用组合

1. **Codex + GPT + Landscape Agent Pack + AutoCAD MCP Pro + AutoCAD**：对应目前优先使用的组合；本RC证据重点是已测环境下的AutoCAD COM主链与Guard、最小几何和保存重开，不能扩大为全部设计任务已验收。
2. **TRAE + 豆包 + Landscape Agent Pack + AutoCAD MCP Pro + AutoCAD**：如果当前TRAE版本确实提供兼容豆包模型、本地命令和MCP权限，可按此架构尝试；本RC未完成该组合的客户端运行验收，不能声称稳定支持。
3. **其他支持本地MCP的Agent + 兼容模型 + Landscape Agent Pack**：目标是按实际能力适配；先完成连接与最小测试，再做正式任务副本。

**架构兼容目标不等于已经实测。**本项目希望做到Agent-agnostic、Model-agnostic，即尽量不绑定某个Agent或模型，具体兼容性仍以[实际测试记录](TESTED_ENVIRONMENT.md)为准。

## 正常使用的完整过程

1. 用户说：“我要做一个30×20m校园口袋公园，南侧主入口，中央休息区，北侧廊架，绿地率不低于45%。”
2. AI理解要求，先规划功能、主要尺寸与坐标，列出假设及关键缺项。
3. 用户确认方案和执行范围。常规次要参数可由AI提出并标明假设；真实边界、冻结对象、正式尺寸和相互矛盾的要求不能猜。
4. Agent读取Pack的规则，检查环境与目标文件，只在授权的新文件或副本中执行。支持的创建操作使用Guard，报错先核查实际状态，不盲目重复。
5. AI根据真实实体、测量与保存重开证据检查，报告通过、失败和未验证项目。
6. 用户说：“休息区感觉太小，帮我扩大一点，但不要减少太多绿地。”AI先给出调整范围与面积影响，必要时确认新的绿地目标，再由Agent只改相关对象并复核。

自动操作只在确认过的任务范围内进行。影响设计选择、冻结内容或安全目标的变化，应回到用户确认；不要每画一条线都打断讨论，也不要擅自改整个方案。

## 用户保留设计控制权

推荐的是用户 ↔ AI ↔ Agent反复迭代，而不是把一次生成当作最终作业。用户负责设计意图与最终选择，AI负责方案建议和执行规划，Agent负责软件操作。AI的自检不是用户或专业审核的替代。

普通豆包网页聊天可以帮助想方案、整理任务，但未必能操作本机AutoCAD。要让豆包模型参与本机绘图，需要符合条件的Agent环境及已配置的本地工具；仅在聊天框发送仓库链接不会自动获得这些能力。

## 当前RC边界

- AutoCAD模型空间基础工作流是主要已验证能力；完整Landscape绘图仍为实验阶段。
- SketchUp为Experimental / optional，当前RC未完成运行时Smoke Test；默认不启动、不连接。
- Layout / PDF为Beta，截图及部分Dimension有兼容限制。
- 其他AutoCAD版本不视为全部验证，跨客户端结果须重新测试。

开始使用：[小白手册](BEGINNER_USAGE_CN.md) · [设计意图模板](../prompts/QUICK_PROMPTS_CN.md#最推荐直接告诉ai你的想法) · [限制说明](LIMITATIONS.md) · [Guard规则](../guards/README.md)
