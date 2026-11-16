# Landscape Agent Pack

Landscape Agent Pack（LAP）是面向景观设计师、学生和 CAD 自动化维护者的 Windows Agent 工作包。它把 AutoCAD 建图、存盘复验和图纸 QA 放进一套可检查的流程，并可选把 DWG 导入 SketchUp 作为建模参考。跑完后用真实文件和数值证据核对结果，原图和未授权的工作文档继续保留。

**当前公开发行版：[v0.2.0](https://github.com/lunxianle666/Landscape-Agent-Pack/releases/tag/v0.2.0)**（`ac378d8`）。本分支的修复见 [Unreleased](CHANGELOG.md#unreleased)。

| 能力 | 已验证范围与前提 |
| --- | --- |
| AutoCAD 建图、图层、文字、标注、DWG/DXF 保存重开 | v0.2.0 在 Windows / AutoCAD 2025 验收；Python COM 用 pywin32，Agent MCP 路径另需配置 AutoCAD MCP Pro。 |
| DXF 几何 QA | Python + ezdxf，可离线检查图层、坐标范围、部分退化和重复实体。 |
| PDF 出图与交付门禁 | AutoCAD PC3 出图；PyMuPDF 离线检查尺寸、非空及矢量。视觉意见需实际阅读结果图，并单独记录。 |
| 可选 DWG → SketchUp | v0.2.0 在 SketchUp Pro 2023 和兼容 Ringo 1.3.2 上实测原生导入、保存、关闭模型、磁盘重开、数值回读。真实图纸结果为 **PASS_WITH_WARNINGS**。 |
| 多图幅施工图编排、完整三维建模或 CAD 无损转换 | 未收录或未验收。DWG→SketchUp 产生的是 `CAD_REFERENCE`；DXF 导入、SPLINE、ELLIPSE、XREF 与任意 3D 仍属实验或超出当前验收范围。 |

## 先跑一个离线示例

在 Windows PowerShell 中，从本分支的仓库根目录运行。Python 3.12 x64 即可；离线示例只需要 ezdxf，不依赖 AutoCAD、SketchUp 或 Agent 配置。

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install ezdxf==1.4.4
.\.venv\Scripts\python.exe -B -m examples.geometry_qa
```

[示例源码](examples/geometry_qa.py) 临时生成一份 1000 × 500 mm 的闭合矩形 DXF，用中文文件名测试读写，并输出 JSON。预期 `status: PASS`、`model_bbox: [0, 0, 1000, 500]`、`entity_count: 1`。运行结束后会清理示例 DXF。使用 v0.2.0 下载包时，按安装指南运行它已有的离线测试；这个示例随维护分支新增。

## 接入实际软件

1. 从 [v0.2.0 Release](https://github.com/lunxianle666/Landscape-Agent-Pack/releases/tag/v0.2.0) 下载正式 ZIP 和 SHA-256 文件，校验后解压；也可从源码使用独立 Python 环境。按 [Windows 安装说明](docs/INSTALL_WINDOWS.md) 选择规则/MCP 安装或 Python 运行路径。
2. 让 Agent 读取 [AGENT_CONTEXT.md](AGENT_CONTEXT.md)，再实际确认 AutoCAD 后端、目标文档与授权输出目录。仓库内可加载的 **1 个 Skill** 是 [sketchup-from-cad-landscape](skills/sketchup-from-cad-landscape/SKILL.md)，仅在走可选 SketchUp 链时读取。
3. 在独立目录用公开测试脚本生成自己的 CAD fixture。依次复验绘图、保存、正常关闭、磁盘重开和几何；如走 Bridge，先确认 Ringo 实例及干净的测试 SKP。见 [Bridge 复现](docs/V02_BRIDGE.md#reproduction)。

图块变换、图层和曲线只在已记录样例及容差范围内验证。注释、尺寸、填充与宽线不保证保留原 CAD 语义。曲线离散和抽样检查不能证明完整拓扑。全新机器、未修改的上游 Ringo、其他软件版本及桌面客户端重载仍待验证。真实项目资料保留在本地，公开仓库提供 [验收摘要](docs/V02_RC2_ACCEPTANCE.md) 和可生成的合成数据。

[已知限制](docs/LIMITATIONS.md) · [故障排查](docs/TROUBLESHOOTING_CN.md) · [维护审查和候选矩阵](docs/MAINTENANCE_AUDIT.md) · [贡献指南](CONTRIBUTING.md) · [变更记录](CHANGELOG.md) · [历史 Beta](https://github.com/lunxianle666/Landscape-Agent-Pack/releases/tag/v0.1.0-beta)

LAP 自有代码采用 [MIT](LICENSE)。SketchUp Skill 保留自身许可，外部依赖适用各自条款：[第三方声明](THIRD_PARTY_NOTICES.md)。提交 [Issue](https://github.com/lunxianle666/Landscape-Agent-Pack/issues) 时请提供软件版本、复现步骤与已脱敏的错误信息。
