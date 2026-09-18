# 三关验收

新机器、新安装、怀疑没装好时，按这三关走。任何一关 FAIL 就停下来处理，不要跳步。

## 第一关：Release / SHA256

从 Release 下载 Windows ZIP（不要选 Source code），在 PowerShell 校验：

```powershell
Get-FileHash -Algorithm SHA256 .\Landscape-Agent-Pack-<版本>-windows.zip
```

与 Release 公布值比对，不一致就停止。解压后应能看到 `AGENT_CONTEXT.md`、`setup.bat`、`standards\`、`guards\`。

**PASS**：哈希一致，目录结构完整。

## 第二关：backend=com / connected=true

打开 AutoCAD（正常权限），运行 `setup.bat`，按 `CLIENT_CONFIG_CN.md` 合并 MCP 片段并重载客户端。让 Agent 实际调用 `system_status` 回读：

- `backend=com`
- `connected=true`
- ProgID 正确

**PASS**：有 Agent 实际回读证据，不是口头说"连上了"。

## 第三关：真实 DWG 保存→关闭→重开

让 Agent 在新文件或测试副本上画最小图形，经 Creation Guard 创建，然后：

1. 保存 DWG
2. 关闭该文档
3. 重新打开
4. 回读实体数量、坐标、半径、单位，与保存前一致

**PASS**：重开后几何一致，原来的用户图纸没被关闭或修改。

---

任意一关 SKIPPED（如 SketchUp 未运行）不影响 AutoCAD 主链；FAIL 才需要处理。
