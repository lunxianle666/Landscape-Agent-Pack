# Changelog

## v0.1.0-beta

### Added

- 版本化 manifest、关键文件 SHA-256 与目录校验；独立 ZIP 解压验证和 ZIP checksum。
- 完整性 8 项回归、可追溯本机验收 runner、陌生用户安装与人工客户端配置说明。

### Fixed

- 默认安装因既有不同 Skill 中止：保留原件并暂存新 Skill、明确 WARN。
- 规则缺失误报 PASS：校验退出码传播至最终诊断 FAIL。
- 规则内容变化无法检测：比较发布期 SHA-256，缺失、单字符修改及空文件 FAIL。
- PowerShell 5.1 中文编码与子进程 hash 兼容问题；重复安装安全复用。

### Verified scope

- AutoCAD 2025 核心 MCP/COM 链、Guard、真实 DWG 保存关闭重开、独立 Python COM 几何回读。
- 11 项安全回归与 8 项完整性回归。
- 本机既有兼容 Ringo 下 SketchUp 2023 box 保存关闭模型重开通过。RC2 的简单 DWG→SKP 历史通过不替代本轮结果。

### Known Limitations

- 全新 Windows、中文 Windows 账户、完整权限/依赖异常矩阵及其他 Agent 未验收。
- 客户端配置人工 merge / backup / restart；新安装后真实 Skill/MCP 重载 MANUAL TEST REQUIRED。
- 不覆盖升级旧版本，无复杂事务自动回滚；失败保留并列写入范围。
- 复杂景观、全局曲线验收 Experimental；未分发本机 Ringo schema 修改。
- 本轮简单 DWG 原生 UI 导入未产生可验收参考实体：FAIL / REVIEW REQUIRED，原因未确认，未继续替代建模。SketchUp 整体 Experimental；不承诺当前 DWG→SKP 可用。
- 传递依赖未全量锁定；manifest 不是签名；AutoCAD 重绘 Skill 授权未定，不分发。
