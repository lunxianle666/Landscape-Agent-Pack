# Beta 验收范围与复现

最终发布 ZIP 是验收对象，维护者先运行 build-manifest.py、package-candidate.py，再在解压副本串行运行 tests/smoke/acceptance_v2.py。它要求真实 CAD 已启动且无用户文档，会创建隔离输出与 runtime；不应在生产绘图期间运行。程序会以不符合预期的测试退出码判失败。

8 项完整性测试包含 clean、删除、改单字符、空规则、无关文件、manifest 缺失、JSON 损坏、必需规则条目遗漏。11 项安全回归独立执行；安装后规则故障再经真实 DiagnosticOnly 检查。

AutoCAD 最小链验证矩形 1000×500 mm、圆半径100 mm、2实体、INSUNITS=4、Guard重放零修改、真实DWG保存关闭重开和另一个Python进程COM回读。后者不是脱离AutoCAD的纯DWG解析器。测试不得并行，共享CAD文档集合。

SketchUp 验证需既有本机兼容Ringo，Agent实际创建box、保存SKP、关闭模型到新模型、UI重新打开后测bounds与solid。简单DWG链使用本轮CAD实际文件、原生导入、保留CAD_REFERENCE，从实际4条矩形边推导顶点再extrude300mm，保存重开核对实体。模板人物单独计数。不等于完整进程退出重启或复杂景观完成。

RC3 实际结果：box PASS；简单 DWG 原生 UI 导入多次尝试后 MCP 仍只读到模板对象，未取得 CAD_REFERENCE，标 FAIL / REVIEW REQUIRED，原因尚未定位。后续三维生成与 SKP 重开 NOT TESTED，不拿 RC2 历史 PASS 替代。README 已将 SketchUp 整体 Experimental，不将其作为 Beta 主要 Verified 功能。

原始证据与 outputs/验收报告-RC3.md 仅留本地，含机器路径不得公开。发布附件只允许源包ZIP及checksum。公开下载反向验证另行匿名下载实际Release asset，比较ZIP hash、解压manifest与checksum，并执行安全smoke。

全新Windows、中文账户、客户端新配置实际重载明确 NOT TESTED / MANUAL TEST REQUIRED，不充当PASS。它们不是本轮用户定义的自动Beta blocker；已发现的确定安装/核心链/完整性/隐私/配置破坏/许可故障才阻止发布。
