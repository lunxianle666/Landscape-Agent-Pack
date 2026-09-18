# 自有 Creation Guard
所有实现为本 Pack 全新自有代码，未复制 autocad-dwg-redraw 或 AutoCAD MCP Pro 源码。

creation_guard.py 的 guarded_create(session, app, doc, tool, arguments, operation_id=...) 只调用一次上游创建工具，使用动态 COM 回读：
1. 确认调用前后是同一已授权目标文档。
2. 对比 ModelSpace 数量与句柄集合，检查现有实体没有变化。
3. 必须正好新增一个句柄，类型和关键几何匹配请求。
4. 原 MCP 报错而实体确认存在时返回 SUCCESS_WITH_FALSE_ERROR，保留 raw_mcp 和 error_original。
5. 同一 session/operation_id 再调用返回缓存凭据，mutation_calls=0、duplicate_blocked=true。新建重复几何必须使用明确的新操作 ID，不能把失败重试伪装成新操作。

无新增实体为 FAIL_NO_ENTITY_CREATED；传输超时、目标改变、额外实体或几何不符为 REVIEW_REQUIRED。两者都禁止自动重复创建。缓存是当前 Guard 进程内的操作凭据，不是跨进程持久化去重服务；重启后应重新核查现有句柄。

Smoke Test 已使用此包装。配置仍直连官方 MCP，Guard 不会自动拦截绕过此函数的调用；Agent 应先读安全规则，按此包装执行有后验核查的创建任务。

支持 Line、Polyline、Circle、Text、Block Reference、简单矩形 Hatch、Linear Dimension。拒绝未验证的可选参数。Dimension 核查测量值、旋转、法向、文本中点投影，不声称原始端点可由旋转标注 COM 完整读取。

document-state-check.py 只读获取文档信息，不启动、保存、关闭用户图纸。原始输出含本机路径，禁止上传。
