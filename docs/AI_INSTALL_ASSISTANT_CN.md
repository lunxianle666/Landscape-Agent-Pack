# AI安装与配置总指令

仅第一次安装、换电脑或修复环境时使用。日常绘图不需要重复发送安装总提示词，改用[小白使用手册](BEGINNER_USAGE_CN.md)和[提示词速查表](../prompts/QUICK_PROMPTS_CN.md)。

这是基于仓库当前安装器提炼的短指令，不是用户那份未提供全文的长篇总提示词。普通聊天 AI 可以解释步骤；只有获得本机工具权限的 Agent 才能实际检查和执行。

## 直接复制给AI

```text
请按 Landscape Agent Pack 当前RC的安装说明，协助我在Windows上安装和配置。
先读取仓库README、docs/INSTALL_WINDOWS.md、docs/LIMITATIONS.md，不编造不存在的功能。
先说明你能否实际访问本机；不能时给我短步骤，不声称已执行。
检查Python、合法已安装的AutoCAD、ProgID、权限完整性和RUNASADMIN冲突，只诊断，不改注册表或关闭用户图纸。
从官方GitHub Release下载Windows ZIP，核对该Release公布的SHA256；不一致就停止。
通过setup.bat安装固定依赖autocad-mcp-pro[com]==1.5.1，不复制site-packages，不覆盖已有Skill或客户端配置。冲突先报告并使用独立安装目标。
找到安装器生成的MCP片段，说明给当前客户端如何合并；已有配置先备份，只合并autocad服务，不输出任何认证凭据。
配置COM backend和用户明确允许的测试目录，重载客户端，再实际检查backend=com、connected=true。
做最小绘图Smoke Test前提醒我自行保存并关闭所有图纸。只测试临时矩形、圆、保存、关闭、重开与几何复核，使用本Pack Guard并保留原始错误，不盲目重复创建。
SketchUp可选，本次默认不启动或连接；只有我明确要求并通过环境检查才连接既有SketchUp/Ringo。
最后报告已执行步骤、安装结果、本机日志位置、测试结果和待处理问题。不要上传配置、日志或图纸；不要为了Layout/PDF扩展调试。
```

## 安装后配置怎么理解

安装器生成配置片段，**不会自动完成 AI 客户端配置**。让 AI 根据本机安装结果找出 `runs` 下的 `codex-autocad.toml` 或 `trae-autocad.json`，检查命令路径与允许目录，再协助合并。不要把示例里的 `<PATH>` 直接当作真实路径使用。

Codex 可通过 `config.toml` 中的 `[mcp_servers.autocad]` 配置本地服务；备份后仅合并这一服务，随后重载客户端。具体配置方式见[官方 OpenAI MCP 文档](https://developers.openai.com/codex/mcp/)，本仓库片段见[Codex模板](../config/codex.toml.example)。TRAE 使用[JSON模板](../config/trae-mcp.json.example)按当前版本的本地 MCP 设置导入；该客户端未完成本 RC 验收，不保证菜单或导入行为一致。

默认允许目录仅为临时绘图测试目录。日常项目要由你明确选择并授权新的项目目录，保留正式源文件。无需开启整个磁盘的写入范围。

## 测试成功后

看到 AutoCAD 主链通过，才进入日常使用。SketchUp 未运行时 `SKIPPED_NOT_RUNNING` 可以接受。出现真实失败或无法确认的结果，先按[故障排查](TROUBLESHOOTING_CN.md)只读诊断，不重复安装。
