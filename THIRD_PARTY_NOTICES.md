# 第三方声明
项目根 MIT 仅覆盖 Landscape Agent Pack 自有安装器、守护和文档。SketchUp Skill 保留原 MIT 与版权声明。未分发 AutoCAD MCP Pro、Ringo、Python、Node 或其依赖源码/二进制。

| 项目 | 版本 / 许可证 | 上游 | 用途 |
|---|---|---|---|
| AutoCAD MCP Pro | 1.5.1 / MIT | https://github.com/U-C4N/Autocad-MCP | COM stdio MCP，安装时由 PyPI 获取 |
| Ringo SketchUp MCP | 1.3.2 / MIT | https://github.com/Ringophilia/Ringo-Sketchup-MCP | SketchUp 桥，按固定官方提交手动安装 |
| sketchup-from-cad-landscape | 固定提交 / MIT | https://github.com/lunxianle666/sketchup-from-cad-landscape | 已分发工作流 Skill，保留其 LICENSE |
| autocad-dwg-redraw | 未发现许可证 / 不收录 | https://github.com/pengxiaoan/autocad-dwg-redraw-skill | 当前未分发代码，也未安装 |
| ezdxf | 1.4.4 / MIT | https://github.com/mozman/ezdxf | AutoCAD MCP 依赖 |
| FastMCP | 3.4.7 / Apache-2.0 | https://github.com/PrefectHQ/fastmcp | MCP 服务框架 |
| Pydantic | 2.13.5 / MIT | https://github.com/pydantic/pydantic | 数据校验 |
| Pillow | 12.3.0 / MIT-CMU | https://github.com/python-pillow/Pillow | COM extra 图像功能 |
| pywin32 | 312 / PSF 元数据及组件独立许可证 | https://github.com/mhammond/pywin32 | Windows COM；包内包括不同授权组件 |
| Python MCP SDK | 本机依赖版本 / 独立元数据 | https://github.com/modelcontextprotocol/python-sdk | Smoke Test 的 MCP 客户端 |
| MCP TypeScript SDK / zod | 本机 1.30.0 / 3.25.76；MIT 元数据 | https://github.com/modelcontextprotocol/typescript-sdk / https://github.com/colinhacks/zod | Ringo 运行依赖 |

详尽的本机传递依赖版本、许可证表达式、组件许可证位置及状态在 installer/dependency-manifest.json。该清单不是所有组件完成法律审核的声明，也不锁定全部传递依赖。安装演练的新环境另行记录实际解析版本。不得将全部依赖概括为 MIT。

AutoCAD 属于 Autodesk，SketchUp 属于 Trimble；用户需自行合法安装。本项目不分发 Windows 字体、真实项目图纸或第三方软件本体。
