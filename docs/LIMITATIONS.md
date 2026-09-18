# RC2 限制

RC2 已独立验证 AutoCAD 主链：空文档集合下新建临时 DWG、闭合矩形 1000×500 mm、圆直径 200 mm、Creation Guard 后验、保存为 AC1032、关闭、重开并几何复核一致。Python 3.12.10、AutoCAD 2025（ProgID AutoCAD.Application.25）、AutoCAD MCP Pro 1.5.1 COM backend 为本机实测版本；其他 AutoCAD 版本与其他 Windows 机器尚未跨机器验证。

创建工具仍可能因 generated Color/color 大小写差异返回错误；Guard 只在新增句柄、数量与关键几何匹配时报告 SUCCESS_WITH_FALSE_ERROR，未修第三方 AutoCAD MCP Pro 上游代码。绕过 Guard 的直连调用仍可能假失败，禁止盲目重试。Guard 必须显式包装调用，不是 MCP 自动中间件。

Guard 仅覆盖实测创建与 block_insert 的同类签名；拒绝未核验的额外属性参数。Hatch 后验范围限简单矩形，Dimension 为线性旋转标注的测量、旋转、法向和文本中点投影核查；COM 旋转标注不暴露扩展线原始端点，本版不声称完整标注样式/端点验收。并发编辑、未知状态或不匹配一律 REVIEW_REQUIRED。

SketchUp 可选，默认不启动、不连接。RC2 未完成 SketchUp/Ringo 运行时验收；历史本机 Ringo 有 schema 调整。缺少许可证的 autocad-dwg-redraw 继续不分发、不安装。

Layout/PDF Beta、截图不稳定、复杂景观图与完整施工图不在 RC2 测试范围。TRAE 等真实客户端配置导入仍未完成验收；不能将本机干净目录演练称作跨机器测试。RC1 / RC1.1 历史 WARNING/PARTIAL/PASS_WITH_ISSUES 保留为来源记录。
