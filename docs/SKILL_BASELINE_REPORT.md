# SketchUp Skill 发布基线差异报告

公开 MIT 基线提交：`cc28ffd4b9daea890fbe78fd3737c9669d042446`。比较依据为内容和逐文件哈希，不按修改时间。

| 文件 | codex | agents | 本机 repository | 公开提交 |
|---|---|---|---|---|
| LICENSE | 缺失 | 缺失 | e92a20b1318ed440cdfbe5c1bd1b8c7a82d780e3e250c264d4d8c345e34f865a | e92a20b1318ed440cdfbe5c1bd1b8c7a82d780e3e250c264d4d8c345e34f865a |
| SKILL.md | 21e8ecad34073b9c90ad8dfe5cc3151436137ace982807dbe2ec6eb44098330c | 70e57d8b39c2dcf73dbe028ac071442031aae6360735d3a74b9a3ed328f4e3ef | 70e57d8b39c2dcf73dbe028ac071442031aae6360735d3a74b9a3ed328f4e3ef | 70e57d8b39c2dcf73dbe028ac071442031aae6360735d3a74b9a3ed328f4e3ef |
| docs/LIMITATIONS.md | 缺失 | e0ee644aab66629869c536f8e16489505d375ee00ce6f810987c9bb55ae73077 | e0ee644aab66629869c536f8e16489505d375ee00ce6f810987c9bb55ae73077 | e0ee644aab66629869c536f8e16489505d375ee00ce6f810987c9bb55ae73077 |
| docs/QUICK_START.md | 缺失 | 缺失 | 9be6671a772f6fd0b51d8103e786489ead0cf0871104beb6a26c564b7b1c7f5f | 9be6671a772f6fd0b51d8103e786489ead0cf0871104beb6a26c564b7b1c7f5f |
| docs/QUICK_START.zh-CN.md | 缺失 | 缺失 | c27ceff24bfdd019bb898c49f4e3a11045ba2dda94401ddbca3ece502de16eba | c27ceff24bfdd019bb898c49f4e3a11045ba2dda94401ddbca3ece502de16eba |
| docs/TESTED_ENVIRONMENT.md | 缺失 | cda04731ace82dac3da04ce33de4ac10131d754e2f575502c26e0a0b2cfaf983 | cda04731ace82dac3da04ce33de4ac10131d754e2f575502c26e0a0b2cfaf983 | cda04731ace82dac3da04ce33de4ac10131d754e2f575502c26e0a0b2cfaf983 |
| docs/TROUBLESHOOTING.md | 缺失 | 缺失 | 6b7e65dc483a373634203123c6d67762ff060e0c786b9efb9488fd8d9dcda882 | 6b7e65dc483a373634203123c6d67762ff060e0c786b9efb9488fd8d9dcda882 |

## 取舍
codex 与本机 repository 的核心流程相同；差异集中在依据与工具段。codex 增加私人证据目录、机器路径、固定 profile/port 和课程情境，不构成需要合并的通用能力。公开版已有动态路径发现、匿名验证和 schema 兼容限制，应保留。
本发布副本采用固定公开提交的 SKILL 和必要 docs，保留原 LICENSE。仅将“不分发 autocad Skill”的独立仓库表述调整为本 Pack 的授权待确认状态。未合并私有路径或临时测试内容。