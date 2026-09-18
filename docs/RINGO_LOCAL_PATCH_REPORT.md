# Ringo 本机修改报告
上游：https://github.com/Ringophilia/Ringo-Sketchup-MCP
版本：1.3.2；本机 HEAD：2dd54d945b0e7a5d1843d58a94a33f5c8875df01。
修改：将 vec、positive、materials_set.color 的同构 Zod tuple 改为 z.array(...).length(3)，保持数值范围和长度限制。不是 Ruby/SketchUp 几何修改。
原因：历史 Codex 工具解析器拒绝 tuple 产生的数组 items schema。历史测试中修复有效；这不证明当前所有 Codex/TRAE 版本仍需要该修改，也不属于 SketchUp 2023 本体兼容修复。
当前策略：固定官方提交，仅提供安装说明；不分发或自动应用此补丁。当前 patched 本机桥连接结果不计为官方未修改版本验收。
未跟踪 scripts/codex-su2023-test.mjs 是本机测试脚本，不收录。
差异摘要：
```diff
diff --git a/src/mcp-server.ts b/src/mcp-server.ts
index 55d642d..99fee30 100644
--- a/src/mcp-server.ts
+++ b/src/mcp-server.ts
@@ -8,8 +8,10 @@ import { open } from 'node:fs/promises';
 import { resolve } from 'node:path';

 const n = z.number().finite();
-const vec = z.tuple([n,n,n]);
-const positive = z.tuple([n.positive(),n.positive(),n.positive()]);
+// Homogeneous fixed-length arrays retain validation and avoid tuple schemas
+// whose array-valued items are rejected by the current Codex tool parser.
+const vec = z.array(n).length(3);
+const positive = z.array(n.positive()).length(3);
 const unit = z.enum(['mm','cm','m','in','ft']).default('mm');
 const id = z.number().int().positive().safe();
 const ref = {entity_id: id.optional(), model_id: z.string().optional(), path: z.array(id).min(1).max(32).optional()};
@@ -37,7 +39,7 @@ const defs: Array<{name:string; method:string; description:string; schema:z.ZodR
 {name:'entity_make_unique',method:'entity.make_unique',description:'Make a component instance or group independent of shared geometry.',schema:ref},
 {name:'entity_set_material',method:'entity.set_material',description:'Assign material to an instance or its direct faces. Faces scope makes instances unique first.',schema:{...ref,material:name,color:vec.optional(),scope:z.enum(['instance','faces']).default('instance')}},
 {name:'materials_list',method:'materials.list',description:'List material color, alpha and texture status.',schema:{},read:true},
-{name:'materials_set',method:'materials.set',description:'Create/update material. Optional PBR roughness gracefully falls back on older SketchUp.',schema:{...modelRef,name,color:z.tuple([n.min(0).max(255),n.min(0).max(255),n.min(0).max(255)]).optional(),alpha:n.min(0).max(1).optional(),texture:z.string().optional(),roughness:n.min(0).max(1).optional()}},
+{name:'materials_set',method:'materials.set',description:'Create/update material. Optional PBR roughness gracefully falls back on older SketchUp.',schema:{...modelRef,name,color:z.array(n.min(0).max(255)).length(3).optional(),alpha:n.min(0).max(1).optional(),texture:z.string().optional(),roughness:n.min(0).max(1).optional()}},
 {name:'tags_list',method:'tags.list',description:'List tags and visibility.',schema:{},read:true},
 {name:'tags_set',method:'tags.set',description:'Create a tag or set its visibility.',schema:{...modelRef,name,visible:z.boolean().optional()}},
 {name:'scenes_list',method:'scene.list',description:'List saved SketchUp scenes.',schema:{},read:true},

```
若后续独立验证证明必要，可以制作注明 MIT 来源的独立 patch，另行审核。
