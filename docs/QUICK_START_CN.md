# 学生快速开始
1. 先备份课程图纸，确认单位、边界和设计要求。
2. 安装本 Pack，检查各连接结果；连接失败先看故障说明。
3. 检查并合并生成的 AutoCAD 配置片段，重新加载 AI 客户端。
4. 提示 Agent：“先检查 AutoCAD 连接、实际图纸单位和当前文档；只在新副本工作，列出缺失设计参数，不猜测。”
5. CAD→SketchUp 时提示：“以真实 DWG 实体为 XY 唯一依据，保留 CAD_REFERENCE，在 MODEL 建模，保存重开并逐项验收。”

第一次仅用临时测试图。不要让 Agent 自动关闭其他图纸；不要以截图代替几何验收。详细设计参数写入 templates/project-brief.md。

创建任务提示：“使用本 Pack Creation Guard，先记录句柄集合；若返回 SUCCESS_WITH_FALSE_ERROR 不要重复创建，保留原始错误。SketchUp 是可选组件，本次未要求就不要启动或连接。”
