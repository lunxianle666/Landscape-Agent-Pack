# 客户端配置说明（Codex / TRAE / 豆包）

> 面向普通用户。告诉你 MCP 片段在哪、怎么合并、怎么不覆盖原配置、怎么让 Agent 读取规则、怎么确认真的连上了 AutoCAD。

## 先理解一件事：普通聊天 AI ≠ 能画图的 Agent

- 普通豆包网页聊天、普通对话 AI 只能给建议。
- 要真正操作本机 AutoCAD，需要：**支持本地 MCP 的 Agent 环境** + **已配置的 autocad MCP 服务** + **打开的合法 AutoCAD**。
- 只发仓库链接不会自动获得这些能力。

Agent 环境就绪后，第一步永远是让它读 `AGENT_CONTEXT.md`（仓库根目录），并按里面的格式输出 `LANDSCAPE_AGENT_PACK_CONTEXT ...` 确认块。

---

## Codex

1. **前置**：使用支持本地 MCP 的 Codex 版本。
2. **安装器生成片段**：运行 `setup.bat` 后，在安装目录的 `runs\<时间戳>\config\` 下找到 `codex-autocad.toml`。里面 `command`、`CAD_PROGID`、`ALLOWED_PATHS` 已是你本机真实路径。
3. **不覆盖原配置**：Codex 配置文件一般在 `%USERPROFILE%\.codex\config.toml`（或 `CODEX_HOME` 指定目录）。先备份，再**只合并 `[mcp_servers.autocad]` 这一节**，不要替换整个文件。同名服务已存在先比较，不重复追加 TOML 节。不存在的目录由用户在确认目标后创建，不推测其他客户端路径。
4. **让 Agent 读规则**：在对话里说"读取本仓库根目录的 `AGENT_CONTEXT.md`，按里面的格式输出确认块，先不绘图"。
5. **重载**：完全退出 Codex 再打开。本 Beta 新安装后的客户端重载仍为 MANUAL TEST REQUIRED；依据：[官方技能文档](https://developers.openai.com/zh-Hans/docs/build-skills)、[MCP 配置](https://developers.openai.com/zh-Hans/docs/extend/mcp)。当前 Agent 的既有 MCP 调用成功不等于新配置重载通过。
6. **确认 connected=true**：让 Agent 调用 `system_status`，要求实际回读 `backend=com`、`connected=true`。只看到"能调用工具"不算数。

---

## TRAE / 豆包

1. **前置**：豆包模型要跑在支持本地 MCP 的 TRAE（或同类 Agent 客户端）里，不能只在网页聊天里用。当前 RC **未完成 TRAE 客户端运行验收**，菜单路径以你版本为准。
2. **安装器生成片段**：`runs\<时间戳>\config\trae-autocad.json`。
3. **导入**：在 TRAE 的 MCP / 本地 MCP 设置里导入这段 JSON，**只合并 `autocad` 这一个 server**，保留其他已有配置；先备份。
4. **让 Agent 读规则**：在对话里同样让它读 `AGENT_CONTEXT.md` 并输出确认块。
5. **确认启用**：在 MCP 列表里看到 `autocad` 已连接，再让 Agent 实际回读 `system_status`。
6. 如果当前 TRAE 版本不支持标准 stdio MCP，不要硬凑，记录现象，按 `docs/TROUBLESHOOTING_CN.md` 处理。

---

## 通用自检

- [ ] 已备份原客户端配置
- [ ] 只合并了 `autocad` 一个 server
- [ ] `command` 路径在资源管理器里点得开
- [ ] 客户端已完全重启
- [ ] Agent 实际输出了 `backend=com connected=true`
- [ ] Agent 已读 `AGENT_CONTEXT.md` 并输出确认块

任何一项没做到，不要进入日常绘图。
