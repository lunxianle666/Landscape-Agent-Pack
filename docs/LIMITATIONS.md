# RC1.1 限制
审核范围为 AutoCAD 临时几何主链。创建工具仍可能因 generated Color/color 大小写差异返回错误；Guard 只在新增句柄、数量与关键几何匹配时报告 SUCCESS_WITH_FALSE_ERROR，未修第三方代码。绕过 Guard 的直连调用仍可能假失败，禁止盲目重试。

Guard 仅覆盖实测七类创建与 block_insert 的同类签名；拒绝未核验的额外属性参数。Hatch 后验范围限简单矩形，Dimension 为线性旋转标注的测量、旋转、法向和文本中点投影核查；COM 旋转标注不暴露扩展线原始端点，本版不声称完整标注样式/端点验收。并发编辑、未知状态或不匹配一律 REVIEW_REQUIRED。

SketchUp 可选，默认不启动、不连接。本轮没有验证官方未修改 Ringo 与当前 Codex/TRAE 客户端组合；历史本机 Ringo 有 schema 调整。缺少许可证的 autocad-dwg-redraw 继续不分发、不安装。

Layout/PDF Beta、截图不稳定、复杂景观图与完整施工图不在本轮测试范围。历史 WARNING/PARTIAL/PASS_WITH_ISSUES 保留。另一台 Windows 与 TRAE 实际配置导入仍需后续用户审核，不能将本机干净目录演练称作跨机器测试。
