# MCBE Probe Editor — 开发进度与实现说明

> 记录当前实现状态、工程结构、核心数据结构与技术细节，供正式测试与后续开发参考。
> 设计需求见 [plan.md](plan.md)，使用说明见 [README.md](README.md)，组件库字段标准见 [DATABASE.md](DATABASE.md)。

最后更新：第八轮改动完成（关联槽位、空模板库、方块材质链、模型定位、贴图路径规范、清理）。数据标准见 [DATABASE.md](DATABASE.md)，使用说明见 [README.md](README.md)。功能通过脚本自检，人工界面测试仍需逐页验证。

---

## 一、总体状态

| 模块 | 状态 | 说明 |
|---|---|---|
| 探测（probe） | ✅ 完成 | 385 对象 / 2850 引用 / 11 条告警（含悬空引用） |
| 索引与浏览 | ✅ 完成 | 对象列表、对象详情、引用树、告警/notes |
| 组件数据库 | ✅ 完成 | 临时库/正式库、按版本分桶、提升、文档核实；正式库已填充 11 桶 / 1423 条 |
| 组件编辑器 | ✅ 完成 | 组件增删改、代码区、语言键、贴图、模型关联 |
| 资产编辑 | ✅ 完成 | 像素画（alpha 规则）、模型命名空间改写 |
| 结构工具 | ✅ 完成 | fv2→fv1 降版本、幂等、备份、转后自检 |
| 未绑定视图 | ✅ 完成 | 分页、类型过滤、搜索 |
| 导出 | ✅ 完成 | zip / mcaddon / 仅改动文件 |
| 文件浏览 | ✅ 完成 | 特殊文件仅在此可见 |
| 工程配套 | ✅ 完成 | requirements / README / run.py / .gitignore |
| 多语言 UI | ✅ 完成 | zh / en 各 242 键、双向对齐，顶栏切换 |
| 示例库 | ✅ 完成 | project / local / official 三类示例，下拉选择 + 填入 + 复制 + 存为示例；存**真实取值**；同桶多值合并并标注来源对象 |
| scope 编辑 | ✅ 完成 | components / component_groups.组 / events 三区独立增删改 |
| 组件组组件库 | ✅ 完成 | 组内独有组件并入版本桶，组件组与顶层共用组件表 / 组件库 |
| 新建对象 | ✅ 完成 | identifier 与路径全自动推导，主文件由空模板生成，附加产物全可选 |
| 关联槽位 | ✅ 完成 | 按 kind 固定槽位表，支持关联 / 新建 / 打开，主体与共享登记文件分离 |
| 空模板库 | ✅ 完成 | `db/official/templates/<kind>/<fv>.json`，每个现存版本一份骨架 |
| 包信息编辑 | ✅ 完成 | manifest 独立页面（双包分栏 / 校验 / 模板），不进对象索引 |
| 导出目录 | ✅ 完成 | 产物统一落到工程根 output/项目名/ |

**路由总数：64**（不含 `static`）。页面与 API 已通过脚本级自检（fails: 0），**界面交互仍待人工验证**（见第十三节待办）。

---

## 二、工程结构

```
MCBE-Probe-Editor/
├── run.py                     启动入口（根目录运行）
├── requirements.txt           Flask>=3.0, Pillow>=10.0
├── README.md                  使用说明
├── PROGRESS.md                本文档
├── plan.md                    设计需求
├── DATABASE.md                组件库数据标准（临时库 / 正式库）
├── .gitignore
├── mcbe_probe_editor/
│   ├── app.py                 Flask 入口 + 9 个蓝图注册
│   ├── routes/
│   │   ├── project.py         项目导入 / 工作区 / 探测触发
│   │   ├── index.py           对象索引 / 树 / 未绑定(旧) API
│   │   ├── editor.py          组件 / 语言键 / 文件保存
│   │   ├── browser.py         文件浏览 / 原始下载
│   │   ├── asset.py           贴图读写 / 模型关联
│   │   ├── export.py          zip / mcaddon / changes
│   │   ├── structure.py       结构版本检查 / 降版本
│   │   ├── db.py              组件数据库 浏览/提升/核实/文档
│   │   ├── unbound.py         未绑定项分页视图
│   │   ├── manifest.py        包信息（manifest）编辑
│   │   ├── objects.py         新建对象
│   │   └── i18n.py            界面语言字典接口
│   ├── services/
│   │   ├── probe.py           探测核心（namespace/引用/告警）
│   │   ├── workspace.py       工作区创建 / 导入 / 路径解析
│   │   ├── store.py           文件读写 / 改动记录 / 语言文件
│   │   ├── pipeline.py        探测流水线（probe→index→临时库）
│   │   ├── database.py        组件数据库（临时/正式/查询/提升）
│   │   ├── texture.py         贴图 alpha 规则 / 像素画
│   │   ├── structure.py       结构 NBT 解析与降版本
│   │   ├── manifest.py        manifest 校验 / 模板 / 读写
│   │   ├── objects.py         新建对象（标准写法生成）
│   │   └── i18n.py            语言字典（zh / en）
│   ├── templates/             10 个页面模板
│   ├── static/{css,js}/       app.css + 9 个页面脚本
│   ├── workspaces/            工作区（gitignore）
│   └── db/official/           正式组件库（gitignore）
└── tools/                     探测原型与自检脚本
```

### 分层原则

```
routes（HTTP + 参数校验）
   ↓
services（业务逻辑，无 HTTP 依赖）
   ↓
文件系统 / 工作区
```

- `services` 之间无循环依赖：`pipeline` 依赖 `probe`/`workspace`/`store`/`database`；`routes` 只依赖 `services`。
- JSON 读写全部经 `store`，带原子写（临时文件 + `os.replace`）与路径穿越防护。

---

## 三、核心数据结构

### 3.1 工作区

```
workspaces/<project_id>/
├── meta.json            项目元信息（名称/来源/统计/包 manifest）
├── source/
│   ├── behavior_pack/   行为包文件副本（copy=True 时）
│   └── resource_pack/   资源包文件副本
├── index.json           对象索引表
├── db/temp/             临时组件库（探测时生成）
├── edits/changes.json   改动记录
└── exports/             导出产物
```

`copy=False` 时不复制源包，`resolve_pack_dir` 回退到 `meta.sources` 记录的原始路径（只读场景，写回会污染源目录，故写测试用 `copy=True`）。

### 3.2 index.json（对象索引表）

```json
{
  "packs": { "behavior": {...}, "resource": {...} },
  "stats": { "objects": 385, "kinds": {...}, "references": 2850,
             "warnings": 11, "notes": 863, "lang_keys_bound": 1395,
             "unbound": 208 },
  "objects": {
    "items:sword_b": {
      "kind": "item",
      "kinds": ["item"],
      "namespace": "items",
      "name": "sword_b",
      "primary": { "pack": "behavior", "path": "items/items_sword_b.json",
                   "format_version": "1.21.50", "kind": "item" },
      "references": [
        { "role": "resource_item", "pack": "resource", "path": "items/items_sword_b.json",
          "format_version": "1.10" },
        { "role": "lang", "pack": "resource", "path": "texts/zh_CN.lang",
          "keys": ["item.items:sword_b.name"] },
        { "role": "texture_index", "pack": "resource",
          "path": "textures/item_texture.json", "keys": ["sword_b"] },
        { "role": "texture", "pack": "resource",
          "path": "textures/items/sword_b.png", "resolved": true },
        { "role": "recipe", "pack": "behavior", "path": "recipes/sword_b.json",
          "format_version": "1.12" }
      ],
      "warnings": [],
      "notes": []
    }
  },
  "special_files": [ { "pack": "behavior", "path": "functions/tick.json",
                       "reason": "package_config" } ],
  "structures": [ { "pack": "behavior", "path": "structures/x.mcstructure",
                    "size": 10027 } ],
  "unbound": [ { "kind": "lang_key", "key": "taoism.loading.1", ... } ],
  "vanilla_recipes": [ ... ],
  "file_errors": []
}
```

**role 取值**：`primary` / `primary_<kind>` / `resource_item` / `block_ref` / `client_entity` / `attachable` / `lang` / `texture_index` / `texture` / `entity_texture` / `geometry` / `recipe` / `spawn_rules` / `feature` / `feature_rule` / `loot_table` / `trading` / `animation` / `animation_controller` / `render_controller` / `particle` / `model` / `material` / `function` / `sounds`。

### 3.3 组件数据库

**临时库**：`workspaces/<pid>/db/temp/`
```
inventory.json                     探测清单（文件级）
components/<kind>/<fv>.json        组件桶
```

**正式库**：`mcbe_probe_editor/db/official/`（跨项目共享）
```
components/<kind>/<fv>.json
docs/<kind>/<component>.md
```

**桶内组件条目**：
```json
{
  "kind": "item",
  "format_version": "1.21.50",
  "components": {
    "minecraft:max_stack_size": {
      "value_type": "integer",
      "default": 64,
      "example": 64,
      "examples": [
        { "label": "probe", "source": "project", "value": 64, "origin": null }
      ],
      "note": "",
      "description": "",
      "doc_ref": null,
      "verified": false,
      "source": "probe",
      "added_in": null,
      "deprecated": false
    }
  }
}
```

> `value_type` 由实际值推断（`infer_value_type`）；`default` / `example` / `examples[].value` 存**真实取值**（`clip_value`，超过 8000 字符才退化为 `summarize_value` 摘要）；`note`、`description`、`verified`、`doc_ref` 等由「提升 + 文档核实」流程补全。

#### 短期库与长期库（示例 / 注释）

| 维度 | 短期（临时库 temp） | 长期（正式库 official） |
|---|---|---|
| 来源 | 本次探测到的实际组件 | 提升 + 文档核实后的沉淀 |
| `example` | 本模组实际取值（快速参考） | 官方示例值（核实后可覆盖） |
| `note` | 空 | 用法/注释说明，由文档核实写入 |
| `verified` | 恒为 false | 核实后为 true |
| 生命周期 | 载入模组时创建，退出释放 | 本地长久保存，跨项目共享 |

**编写组件时的行为**：编辑器「从数据库添加」与「编辑组件」弹窗会同时展示 `example` 与 `note`，并按来源标注「正式库 ✓ / 临时库」。正式库缺少官方示例时，回退使用实际值作为示例，保证任何条目都有可参考样例。

### 3.4 改动记录

`workspaces/<pid>/edits/changes.json`：
```json
{
  "project_id": "...",
  "changes": [
    { "pack": "behavior", "path": "items/items_sword_b.json",
      "op": "modify", "time": "...", "times": 3 }
  ]
}
```
- `op`：`add` / `modify` / `delete`。
- 同一文件多次改动合并为一条，`times` 累加。
- 特殊文件与备份目录不记入。

---

## 四、探测规则（技术细节）

### 4.1 namespace 探测

**必须从文件内容探测，不依赖目录名**。实测 `items/` 目录内混有 `items:`、`ny:`、`fanart:`、`construction:` 多个 namespace。

优先级：
1. `description.identifier`
2. 语言键前缀映射
3. 贴图索引键反查
4. 文件名兜底

### 4.2 主文件识别

读取顶层键判定类型：

| 顶层键 | kind | role（行为包） | role（资源包） |
|---|---|---|---|
| `minecraft:item` | item | primary | resource_item |
| `minecraft:block` | block | primary | block_ref |
| `minecraft:entity` | entity | primary | — |
| `minecraft:client_entity` | entity | — | client_entity |
| `minecraft:attachable` | item | — | attachable |

- 同 identifier 同时存在于 items 与 entities（如 `construction:core`）→ 记为**多 kind 对象**（`kinds` 数组），不算冲突。
- 同 kind 重复 primary → `duplicate_primary` 告警。

### 4.3 format_version

- 每个文件只取一个 `format_version`，记录在引用项上。
- `fv_of()` 兼容数字（`1.10`）、字符串（`"1.21.50"`）、数组（`[1,2,0]`）。
- 缺失 → `"unknown"` 桶 + `missing_format_version` 告警。
- **各版本互相独立**，查询精确命中，不回落低版本。

### 4.4a 语言名反查（lang_name）

探测时记录每个对象第一条非空语言值，写入索引 `lang_name`（截断 120 字符），全部值拼接后写入 `lang_text`（截断 4000）。用途：

- 对象列表在 identifier 下方显示中文名
- 搜索框可命中语言键名、语言值、中文名
- 语言键编辑区展示可读名称

### 4.4 语言键归属

前缀映射：`item.`→item、`entity.`→entity、`tile.`→block、`action.hint.exit.`→entity。

匹配时先剥前缀，再去 `.name` 后缀，然后：
1. 直接比对 `namespace:name`
2. 首个 `.` 替换为 `:` 再比对

兼容 `item.items:x.name=` 与 `item.items:x=` 两种写法，不强制规范化。

### 4.5 贴图关联链

```
物品 minecraft:icon 组件值
  → item_texture.json 的 texture_data 键
    → 贴图路径（自动补 .png/.tga 后缀并校验存在）
```

`icon` 兼容 4 种写法：`string` / `{texture}` / `{textures:string}` / `{textures:{...}}` / `{textures:[...]}`。

### 4.6 配方关联

1. 优先按 `description.identifier` 匹配对象。
2. 失败则回退按 `result.item`（或 `output.item`，支持数组取首个）匹配。
3. 结果为原版物品（`minecraft:` 前缀且非本包对象）→ 归入 `vanilla_recipes`，不算未绑定。
4. 仍失败 → `unbound`。

> 修复点：`recipe_furnace` 的结果字段是 `output` 而非 `result`，已兼容。

### 4.7 原版引用白名单

`animation.humanoid.*`、`animation.zombie.*`、`controller.animation.*` 等原版内置动画/控制器前缀命中时，只记 `notes` 不记 `warnings`。白名单覆盖 70+ 实体前缀 + 1.21.4+ 的 `spear` 系列。

### 4.8 特殊文件

| 文件/目录 | reason | 处理 |
|---|---|---|
| `pack_icon.png` / `pack_icon1.png` | pack_icon | 原样保留 |
| `functions/tick.json` | package_config | 原样保留 |
| `lines/` | assets | 原样保留 |
| `blocks.json` / `sounds.json` / `sound_definitions.json` | pack_config | 原样保留 |
| `item_texture.json` / `terrain_texture.json` | texture_index | 原样保留 |
| `.bak` / `.bk` / `_fv2_backup/` | — | 跳过不探测 |

特殊文件不进入对象模型、不加载进编辑器，**仅在文件浏览视图中可见**。

---

### 4.9 组件组（component_groups）提取

标准写法中 `component_groups.<组名>` 的**组体本身就是组件集合**，没有 `components` 包装层：

```json
"component_groups": {
  "bow": { "minecraft:transformation": { "into": "t:bow_mob" } }
}
```

- `database.extract_group_components()` 会把**只出现在组件组里**的组件并入版本桶，
  保证组件组的「+ 添加」与顶层 `components` 一致。
- 同时兼容少数带 `components` 包装层的写法，只挑 `minecraft:*` 键。
- 写入时 `routes/editor.py::_resolve_scope` 对 `component_groups.<组>` **直接返回组体**，
  不创建 `components` 层，避免产生非标准结构。

---

## 五、编辑器与资产

### 5.1 组件编辑

- 编辑器层次：对象 → 文件分组（role + fv）→ description / components → 组件 → 属性。
- 组件来源分 `origin=official`（正式库，可能带 `verified`）与 `origin=temp`（文件内实际值），合并视图用 `in_use` 标记。
- 支持：单组件编辑（JSON 值）、删除、从数据库添加、整文件代码区编辑。
- 「+ 添加」先弹出**组件清单**（`#add-modal`）：按当前文件 `kind + format_version` 拉
  `/api/project/<pid>/components` 合并视图，列出组件名 / 值类型 / 示例预览 / 来源
  （正式库 / 临时库），支持实时搜索；点选后自动带入组件名与示例值。
- 组件组（`component_groups.<组>`）与顶层 `components` 共用同一套组件表与组件库。
- 保存前校验 JSON 合法性，非法阻断。

### 5.2 语言键编辑

- 只处理该对象自己的键，不回写其他对象的行。
- 保留原始行序与写法，只替换匹配行的值。
- `store.update_lang_keys` 返回 `(new_text, applied, missing)`。

### 5.3 像素画

- 画布尺寸：宽高各自 1–256（默认 16×16），可保留内容重设。
- **alpha 规则**：绘制的半透明（1..254）若原像素不是半透明，强制改为 255；原半透明像素可原样写回。返回 `fixed_pixels` 计数。
- 色板 16 色 + 自定义取色 + 去色（灰度）+ 橡皮。
- 支持 `?pack=&path=` URL 参数直载。

### 5.4 模型关联

- 仅做命名空间改写，不本地渲染。
- 兼容两种 `.geo.json` 形态：
  - 1.16+：`minecraft:geometry = [{description:{identifier}}]`
  - 1.12：`{"geometry.xxx": {...}}`（键即标识）
- 改写目标：`geometry.<namespace>.<name>`，与对象标识一致。

---

## 六、结构降版本（技术细节）

### 6.1 转换规则（fv2 → fv1）

| 项 | fv2 | fv1 |
|---|---|---|
| `format_version` | `2` | `1` |
| `block_indices` | `List<IntArray>`（`TAG_List` 元素 `TAG_Int_Array`） | 两层 `List<List<Int>>`（外层 `TAG_List`，内层 `TAG_Int`） |
| 图层 | 可能单层 | 固定两层（方块层 + 液体层） |

### 6.2 关键约束

- **`-1` 必须原样保留**：`-1` 是「结构空位」，放置时跳过、保留目标位置原方块；空气索引则会清除方块。二者不可混同。
- 缺液体层 → 补一层全 `-1`；已有液体层 → 保留原值，不丢弃已有水。
- 只改容器编码，不动 `palette` 方块内容、方块实体、`entities`、坐标。

### 6.3 工程约束

- **幂等**：只处理 `format_version == 2`，已是 fv1 直接跳过。
- **备份**：转换前复制到同目录 `_fv2_backup/`（文件名带时间戳）。
- **转后自检**：重新解析，校验层数=2、长度=cells、索引为 `-1` 或落在 palette 范围内。
- 失败则抛错且不落盘。

### 6.4 已修复 bug

- `_get()` 返回 `(tag_type, value)` 二元组，代码曾误写 `size[2]`，应为 `size[1][2]`。三处（`inspect_raw` / `check_v1` / `downgrade_root`）已修。
- 修复后 25 个真实结构全部正确解析为 fv1、2 层、带调色板与空位统计。

---

## 七、导出

| 模式 | 产物 | 说明 |
|---|---|---|
| `zip` | `*_<ts>.zip` | 行为包 + 资源包按原包目录名打包 |
| `mcaddon` | `*_<ts>.mcaddon` | 同上，改后缀 |
| `changes` | `*_changes_<ts>/` 目录 | 仅改动文件 + `_changes.json` 清单 |

- 包顶层名优先级：`meta.sources` 原始目录名 → `meta.pack_manifest` 中对应 `type` 的 `root`
  （mcaddon 导入的项目该字段为空，靠这一级兜底）→ 默认 `behavior_pack` / `resource_pack`。
  实测 TaoismV5 导出为 `Taoism_B/`、`Taoism_R/`。
- 导出产物在**工程根** `output/<project_id>/`，可通过 `/export/dl` 下载。
- `changes` 模式保持包内相对结构：

```
Taoism_B/items/items_sword_b.json
Taoism_R/texts/zh_CN.lang
_changes.json
```

---

## 八、验证结果

### 8.1 探测（Taoism Craft 真实数据）

| 指标 | 数值 |
|---|---|
| 对象 | 385（item 223 / entity 159 / block 3） |
| 引用 | 2850 |
| 警告 | 11（源数据问题 + 悬空 geometry / 动画控制器引用） |
| notes | 863（原版内置引用，已降级） |
| 语言键绑定 | 1395 |
| 特殊文件 | 19 |
| 结构 | 25（全部 fv1） |
| 未绑定 | 480（动画控制器/模型/语言键等） |
| 文件错误 | 0 |

**7 条真实警告**：
1. `items:fbusket` — `items_busket.json` 与 `items_fbusket.json` 同 identifier 重复注册
2. `items:sebooka` — 行为包主文件缺失（仅有 `.bk` 备份）
3–7. `controller.animation.guide`(×2) / `forcefield` / `peddler` / `dread` — 全库无定义，模组悬空引用

### 8.2 回归测试（全部通过）

- **页面/API**：22 项（含 302 重定向、路径穿越返回 400）
- **写回链路**：组件改/增/删、语言键、改动记录、导出 mcaddon（1639 条目）、导出 changes、贴图 alpha 原样写回
- **结构**：25 个真实结构检查通过
- **数据库**：桶查询、提升、文档写入、核实标记、正式库桶生成
- **未绑定**：分页、类型过滤、搜索
- **第五轮补充**：页面/API 21 项、写回链路、导出（包顶层 `Taoism_B` / `Taoism_R`）、
  组件组端到端（合成项目：入库 / 接口 / 读取 / 写入 / 删除）、`node --check` 11 个前端脚本

---

## 九、已知限制

1. **正式库为种子数据**：`db/official/` 已填充 11 桶 / 1423 条（全部 `verified`），但 item 1.16.0 仅 20 条、缺官方默认值；未收录组件仍需人工补充。详见 [DATABASE.md](DATABASE.md) 第 10 节。
2. **`value_type` 为推断值**：来自实际数据，非官方 schema 定义；`enum` 类型不会被自动识别。
3. **模型编辑外链 Blockbench**：本地不做模型渲染/编辑，仅改写 `geometry` 命名空间。
4. **结构不解析方块语义**：只处理版本与容器编码，方块内容原样保留。
5. **多 locale 语言键**：对象编辑页会列出所有 locale 中的该对象键，按文件回写；无 locale 选择器。
6. **写回会污染源目录**：`copy=False` 的工作区直接写原始路径，正式使用应保持默认 `copy=True`。
7. **组件组包装层**：标准写法无 `components` 包装层，工具兼容两种；若历史文件被写成
   `group.components = {...}`，仍可读写，但不会主动改写回标准形态。
8. **示例值上限**：`clip_value` 超过 8000 字符退化为 `{keys, key_count}` 摘要，
   此时示例不是可直接回填的真实值。

---

## 十、后续可选事项

1. **正式库查漏补缺**：item 1.16.0 缺官方默认值与完整组件清单；文档未收录的组件可继续通过「提升 + 核实」补充。
2. **UI 打磨**：编辑器组件表的类型提示、未绑定项到对象的跳转、导出进度反馈。
3. **启动试运行**：`python run.py` 打开浏览器实测交互。
4. **测试脚本整理**：`tools/` 下的临时补丁脚本（`patch_*.py`）可在正式测试后归档或删除。

---

## 十一、启动方式

```bash
pip install -r requirements.txt
python run.py
# http://127.0.0.1:5000/
```

自检脚本：
```bash
python tools/probe.py <behavior_pack> [resource_pack] -o index.json
python tools/e2e_test.py         # 探测 + 临时库
python tools/page_test.py        # 页面/API + 写回 + 导出
python tools/structure_test.py   # 结构检查/降版本
python tools/db_test.py          # 未绑定 + 组件数据库
```

---

## 十二、近期改动（第四轮 / 第五轮）

以下为在此前版本基础上新增/修复的内容，均已通过脚本自检。

### 12.1 示例库（跨项目共享）

正式库（`db/official/`）= 本地库，条目新增 `examples` 数组：

```json
"minecraft:max_stack_size": {
  "examples": [
    {"label": "probe",  "source": "project",  "value": 64, "origin": "TaoismV5"},
    {"label": "manual", "source": "local",    "value": 16, "origin": null},
    {"label": "doc",    "source": "official", "value": 64, "origin": "wiki"}
  ]
}
```

| source | 含义 | 产生方式 |
|---|---|---|
| `project` | 本项目当前文件实际值 | 探测时自动收录 |
| `local` | 本地库沉淀 | 手动「存为示例」；提升时并入 |
| `official` | 官方文档核实 | 文档核实流程写入 |

- 去重按 `(source, JSON(value))` 指纹，单组件最多 60 条。
- 编辑器弹窗顶部：示例下拉框（标注来源）+ 填入 / 复制 / 存为示例。
- API：`GET /db/examples`、`POST /db/examples/add`。

### 12.2 scope 编辑（组件组 / 事件）

| scope | 落盘位置 |
|---|---|
| `components` | `minecraft:entity.components` |
| `component_groups.<组名>` | `…component_groups.<组>`（组体直接是组件集合） |
| `events` | `…events` |

统一入口 `POST /edit/<ident>/entry`，支持 `op=set / delete / set_group`
（`set_group` 用于整组替换）。

### 12.3 新建对象

索引页「新建对象」：kind / namespace / name / format_version
+ 可选（资源包注册 / 语言键 / 贴图索引登记）。创建后自动重探测。

| kind | 行为包主文件 | 资源包注册 |
|---|---|---|
| item | `items/<name>.json` | `items/<name>.json`（1.10） |
| entity | `entities/<name>.json`（含 groups/events 骨架） | `entity/<name>.entity.json` |
| block | `blocks/<name>.json` | `blocks/<name>.json` |

同名文件存在则拒绝（400）。

### 12.4 包信息（manifest）独立页

`/project/<pid>/manifest`，行为包 / 资源包分栏，支持编辑、校验、生成模板。
校验项：`header.{name,uuid,version}`、uuid 格式、version 三元整数数组、
`modules` 非空且每项含 uuid。**不进对象索引**，保存后重探测。

### 12.5 多语言 UI

- 字典 `services/i18n.py`，zh / en 各 242 键，双向无缺失。
- `/api/i18n` 取字典；`POST /api/ui-lang` 切换（存 session）。
- 模板用 `data-i18n` / `data-i18n-ph`；脚本用 `t()` / `tf()`。

### 12.6 导出目录

产物改到**工程根** `output/<project_id>/`（与 `workspaces/` 同级）。
接口返回完整 `output` 路径，UI 提示实际落点。
包顶层名对 mcaddon 导入的项目取 `meta.pack_manifest` 的 `root`（见第七节）。

### 12.7 界面细节修复

| 问题 | 处理 |
|---|---|
| 超长组件值撑破布局 | 超过 200 字符折叠为摘要 + 「展开」 |
| 语言键只显示中文 | 改为 `key -> [{locale, pack, path, value}]`，逐 locale 读写 |
| 像素画尺寸固定 | 宽高任意 1–256，支持保留内容重设 |
| 像素画无颜色记忆 | 最近颜色存 localStorage（最多 20） |
| 像素画无撤回 | 撤回/重做栈（40 步）+ Ctrl+Z / Ctrl+Y |
| 导出按钮无反应 | `prompt()` 改模态框三选一 |
| FormData 被 JSON 化 | `api()` 识别 FormData 跳过序列化 |
| 静态资源缓存 | 关闭长缓存 + 模板加 `?v=` 版本参数 |

### 12.8 第五轮修复

| 问题 | 根因 | 处理 |
|---|---|---|
| 页面 `<title>` 显示 `<span ...>` 原始标记 | 各页 `{% block title %}` 内嵌 `<span data-i18n>`，`applyI18n` 作用不到 `<title>` | 改为服务端 `{{ i18n_dict["..."] }}` 纯文本 |
| 示例显示 `{keys, key_count}` 而非真实值 | `build_entry` 把 `summarize_value()` 摘要写进 `default` / `example` / `examples[].value` | 新增 `clip_value`（≤8000 字符存真实值，超出才摘要） |
| 「+ 添加」没有组件清单 | `#add-modal` / `#add-list` / `#add-search` 存在，但 `editor.js` 从未引用，直接弹空白 JSON | 新增 `openAddFromDb` / `renderAddList`，按 kind+fv 拉组件库，可搜索点选 |
| 组件组名显示 `undefined` | `scopeLabel` 用 `s.split(".", 1)[1]`；JS 的 `split(sep, limit)` 第二参数是「数组最大长度」，恒返回单元素 | 改为 `s.slice("component_groups.".length)` |
| 组件组内容恒为空 | `scopeList` 读 `grp.components`，而标准写法组体直接是组件集合 | 新增 `groupItems()`，双形态兼容 |
| 组件组没有组件库 | `extract_components` 只取顶层 `components`，组内独有组件从未入库 | 新增 `extract_group_components()`，`build_temp` 并入版本桶 |
| 写入组件组生成非标准结构 | `_resolve_scope` 主动创建 `grp["components"]` | 直接返回组体本身 |
| 导出顶层目录被兜底成 `behavior_pack` | `_pack_top` 只读 `meta.sources`，mcaddon 导入项目该字段为 `null` | 增加 `meta.pack_manifest` 回退 |
| 临时库只增不减 | `clear_temp` 定义但零调用，陈旧桶持续堆积 | `run_probe` 重建前先 `db.clear_temp` |
| 文件浏览页改过的文件不可编辑 | `editable` 判定含 `key not in changed` | 仅按扩展名 + 特殊文件判定，`changed` 只做高亮 |
| `texture/new` 尺寸限制过死 | 硬编码 16/32/64/128，与画布页 1–256 不一致 | 放开为 1–256，非整数返回 400 |

---

### 12.9 第六轮修复

| 问题 | 根因 | 处理 |
|---|---|---|
| 编辑组件时示例只显示当前对象的取值 | `build_temp()` 用 `if cname not in bucket` 判断，同 `(kind, fv)` 桶内同名组件只留第一个值，其余对象取值全部丢弃 | 新增 `add_project_value()` / `add_project_example()`，按值指纹去重追加示例（上限 60）；顶层组件与组内组件统一走该逻辑 |
| 示例无法区分来自哪个对象 | 临时库示例不带来源，`list_examples()` 写死 `label="current"` / `origin=None` | `build_entry()` 增加 `origin` 参数，`list_examples()` 透传 `label` / `origin` / `added`；前端新增 `exampleOrigin()`，下拉显示 `[本项目 · entity:arrow]` |
| 提升到正式库覆盖原来源对象 | `promote_to_official()` 无条件写 `origin = project_id` | 改为仅当 `origin` 为空才回填 |
| 对象索引页「重新探测」返回 404 | `index.js` 请求 `/api/project/<pid>/probe`（单数），后端只注册了 `/api/projects/<pid>/probe`（复数） | `api_probe` 增加路由别名，两种路径并存 |

**实测**（重建 TaoismV5 后）：`item/1.21.50` 的 `minecraft:icon` 示例 1 → **47**，`minecraft:durability` 1 → **12**；`entity/1.16.0` 的 `minecraft:timer` 1 → **12**；`entity/1.8.0` 的 `minecraft:collision_box` 1 → **14**。

> 临时库只覆盖主文件（`primary`），资源侧注册文件与客户端实体文件里的组件不入桶，详见 [DATABASE.md](DATABASE.md) 第 10 节。

---


### 12.10 第七轮：正式库填充

`db/official/` 从空库填充为可用种子库，覆盖 **3 类 × 4 个 format_version，共 11 个桶、1423 条组件**，全部 `verified: true`。

| kind | 1.12.0 | 1.16.0 | 1.21.0 | 1.26.0 |
|---|---|---|---|---|
| entity | 244 | 263 | 359 | 350 |
| item | — | 20 | 30 | 44 |
| block | 8 | 30 | 36 | 39 |

- `docs/` 改为按 **(kind, component) 跨版本聚合**，同一组件各版本占一节，共 **476 份**（entity 374 / item 50 / block 52）。
- 示例 **1446 条**：`official` 1399（文档 / schema 抓取）+ `project` 47（项目实际值，24 条 probe 条目带入）。
- `source`：`manual` 1399（官方文档 / schema）+ `probe` 24（官方未收录、经人工确认后入库）。
- `description` 已填 1267 条（英文原文）；`note` 全部有值；`added_in` 未填；`deprecated` 全为 false。
- 人工剔除 `minecraft:player.exhaustion` / `.experience` / `.level` / `.saturation`（属玩家属性，非实体组件），逻辑固化在 `finalize.py` 的 `REMOVE` 常量。

数据源、版本映射、构建脚本顺序、人工确认清单与 `verified` 语义见 [DATABASE.md](DATABASE.md) 第 10 节。

---

### 12.11 第八轮：关联槽位与新建体系

本轮把「模糊的 references 列表」升级为「有名字、有状态、可操作的固定关联位置」，并按实测模组规则校正每类对象的对应关系。

#### 新增模块

| 文件 | 职责 |
|---|---|
| `services/slots.py` | 槽位定义表 + `build_slots()`：按 kind 从 references 聚合出固定槽位 |
| `services/templates.py` | 空模板库 `db/official/templates/<kind>/<fv>.json`，`materialize()` 填充 identifier |

#### 槽位表（全部可选，状态 linked / optional / pending）

| kind | 槽位 |
|---|---|
| item | 资源包注册、attachable（含贴图）、attachable 动画、attachable 动画控制器、attachable 模型、贴图、配方 |
| entity | 实体资源注册、模型、动画、动画控制器（行为包）、动画控制器（资源包）、贴图、生成规则、掉落表、交易表、声音、渲染控制器 |
| block | 贴图、blocks.json 登记、terrain_texture.json 登记、feature、feature_rule、掉落表、配方 |

关键校正点：

| 项 | 规则 |
|---|---|
| 语言键 | **不是槽位**——写在共享 `texts/<locale>.lang` 固定位置，按对象自己的键读写 |
| 掉落表 | 仅 entity / block |
| 配方 | item / block 可多个 |
| 物品贴图 | **主体是 png**，`item_texture.json` 仅作登记媒介 |
| 方块贴图 | **主体是 png，可多张**；`blocks.json` 与 `terrain_texture.json` 是两个共享登记文件；六面地址是键名，不等于六张图 |
| 实体动画控制器 | 行为包与资源包是**两个独立物**，分两个槽 |
| geometry | 引用了名字但未解析到文件 → `pending`（待指定） |

#### 探测增强（`services/probe.py`）

| 新增 | 说明 |
|---|---|
| `link_block_materials()` | `blocks.json` 按键归属 → 六个贴图键 → `terrain_texture.json` → png；兼容 1.21+ `minecraft:material_instances` |
| `link_features()` | 两遍关联：`replace_rules.places_block` 挂方块，再 `places_feature` 经 feature 二级命中 |
| `link_assets()` geometry 部分 | 扫 `models/` 的 `minecraft:geometry[].description.identifier` 与 1.12 键名，geometry 引用带 pack/path/format_version/resolved |
| `link_item_textures()` | 物品贴图兜底：索引键 == 对象名 或约定路径存在即挂接，不强依赖 `minecraft:icon` |
| `_ctrl` 按 pack 分桶 | 同名控制器在行为包 / 资源包分别记录，role 拆为 `animation_controller_behavior` / `_resource` |
| `collect_render_controllers()` | 收集并索引 render_controllers |
| `finalize()` 输出 slots | 并剔除已被引用的 unbound 项 |

#### 新建体系（`services/objects.py` 重写）

- identifier 一律由 `namespace:name` 推导，用户不手写。
- 路径全部按模组规则固定，唯一例外是动画控制器可指定多个不同名文件。
- 主文件由空模板生成（0 组件），版本可自选。
- 贴图新规则：`textures/<类别>/<namespace>/<name>.png`，目录自动创建；已有贴图不迁移。

| 类别 | 新贴图路径 | 空白尺寸 |
|---|---|---|
| item | `textures/items/<ns>/<name>.png` | 16×16 |
| entity | `textures/entity/<ns>/<name>.png` | 64×64 |
| attachable | `textures/attachable/<ns>/<name>.png` | 16×16 |
| block | `textures/blocks/<name>.png` | 16×16 |

- 新增 `workspace.ensure_pack_dir()`，单包项目也能建另一侧目录。
- 新增 `register_item_texture()`，把任意 png 登记进 `item_texture.json`。
- 「同时创建」选项默认**全部不勾选**（`with_resource` / `with_lang` / `with_texture` 默认 False）。
- 语言键写入规则对齐实测：item 无 `.name`，entity / block 带 `.name`。

#### 槽位 API（`routes/editor.py`）

| 方法 | 路径 | 作用 |
|---|---|---|
| GET | `/edit/<ident>/slots` | 槽位详情 + 候选文件（图片槽扫 png/tga，登记槽给文件本身） |
| POST | `/edit/<ident>/slots/link` | 关联已有文件：注册类对齐 identifier、模型改写 geometry、动画写入宿主、方块贴图六面统一切换 |
| POST | `/edit/<ident>/slots/create` | 按规则自动建文件，全部 `can_create` 槽位均有骨架模板 |

- 新增骨架模板 7 个：animation / loot_table / trading / feature / feature_rule / recipe / render_controller。
- `EXACT_FILE_SLOTS = {"blocks_json", "terrain_texture"}`：候选就是文件本身，不递归目录。
- `EDITABLE_JSON_ROLES` 补入 geometry / blocks_json / terrain_texture / animation 系列，使它们在文件分组中可编辑。

#### 前端

- 编辑页「文件分组」上方新增「关联引用」表：槽位 / 状态徽标 / 当前关联（路径 + 版本 + keys）/ 操作（关联、新建）。
- 「打开」按钮智能路由：`.png` / `.tga` → 像素画编辑器；其他 JSON → 切文件标签并滚动到代码区。
- 关联弹窗：候选下拉 + 手填路径；新建弹窗：动画控制器可填多个逗号分隔名。
- 新建对象弹窗：版本下拉（来自模板库）+「查看模板代码」「复制模板代码」，打开时重置所有「同时创建」选项为不勾选。
- 槽位标签走 i18n（`slot.<key>`），状态含 `slot.state.linked` / `.optional` / `.pending`。

#### 方块贴图索引修复

**现象**：方块点「新建」生成贴图后，贴图槽仍是 `optional`，新图未被索引。

**根因（两处叠加）**

| # | 问题 | 表现 |
|---|---|---|
| 1 | `terrain_texture.json` 按约定造 `<name>_up` 等六个键，而 `blocks.json` 可能使用**自定义键名**（如 `sixface_top` / `sixface_side` / `sixface_side2`） | 新图落进 `blocks.json` 根本不引用的孤儿键，探测扫不到 |
| 2 | 新建走「只补缺失键」，关联走「无条件覆盖六面」 | 对已有完整贴图映射的方块，新建不生效；关联又破坏原有独立贴图 |

**修复**（`routes/editor.py`）

| 函数 | 变化 |
|---|---|
| `_ensure_blocks_json()` | 返回 `(face -> texkey 映射, 写入文件列表)`，**保留已有自定义键名**，只补缺失面 |
| `_block_texture_keys()` | 从映射取出该方块实际使用的全部贴图键（含非标准面键，去重） |
| `_ensure_terrain()` | 改为按传入的 `texkeys` 写，**不再自己造键** |
| `_existing_block_keys()` | 只读：从 `blocks.json` 取该方块的现状键名 |
| `_link_block_texture()` | 增加 `overwrite` 参数，区分新建与关联 |

**语义**（键名一律沿用 `blocks.json` 已有命名，不破坏既有结构）

| 操作 | 行为 |
|---|---|
| 新建贴图 | 生成空白 png，**接管该方块全部贴图键** |
| 关联贴图 | 该方块全部贴图键统一切换到指定 png |
| blocks_json 槽新建 | 补条目 + 按实际键名补 terrain |
| terrain_texture 槽新建 | 只补 `blocks.json` 现存的键，不新增键 |

**验证**

```
TaoismV5 真实方块（只读，未被改动）
  blocks:ball          texture=linked(3)  blocks_json=linked  terrain=linked
    bfront.png / bside.png / bup.png  resolved=True
  blocks:cinnabar_ore  texture=linked(1)  blocks_json=linked  terrain=linked
  blocks:framework     texture=linked(1)  blocks_json=linked  terrain=linked

自定义键名方块（sixface_top / _side / _side2）
  新建贴图 → 三个自定义键全部指向 sixface.png，未产生 sixface_up 孤儿键
  关联新图 → 三个自定义键统一切换到 newface.png

全新方块完整链路
  新建贴图 → chain.png + blocks.json + terrain_texture.json
  index roles → ['block_texture', 'blocks_json', 'terrain_texture']
  slots → texture=linked, blocks_json=linked, terrain_texture=linked
```

#### 清理

- 删除 `tools/` 下 40+ 个一次性补丁与检查脚本，保留 17 个正式脚本。
- 删除测试工作区残留与 `db_test.py` 的提升副作用（`components/block/1.17.3.json` 及对应测试文档）。
- TaoismV5 内 7 处测试创建的对象与贴图已删除，`edits/changes.json` 重置；重新探测后恢复 385 对象 / 2850 引用。

## 十三、待办事项

### 13.1 必做（阻塞交付）

1. **界面人工测试未完成**：本轮改动均为脚本级自检，需逐页实际点击验证。
   重点：关联槽位的关联/新建/打开、新建对象弹窗（模板查看与复制）、
   贴图槽的像素画跳转、geometry 待指定显示。
2. **后端需重启**：`services/{database,pipeline,workspace}.py` 与
   `routes/{editor,export,asset,browser}.py` 均有改动，旧进程不会自动加载。
3. **浏览器强刷**：`Ctrl+F5` 清 `editor.js` / `app.css` 缓存。
4. **重新探测一次**：临时库已改为「重建前释放」，历史桶内容（旧 `key_count` 摘要）
   需重新探测后才会变成真实值。TaoismV5 已于第六轮重建；其他项目需各自点一次「重新探测」（该按钮已在第六轮修好）。

### 13.2 功能待完善

4. **正式库仍需查漏补缺**：已填充 11 桶 1423 条，但 item 1.16.0 仅 20 条且缺默认值；
   未收录组件需人工补充文档后入库。
5. **`description` 覆盖不完整**：1423 条中 1267 条有说明（英文原文），其余 156 条为空。
6. **`value_type` 为推断值**：`enum` 无法自动识别，复杂对象仅给 key 摘要。
7. **像素画不支持多帧 / 动画贴图**：仅单帧 PNG。
8. **模型仍依赖 Blockbench 外链**：本地只改写 geometry 命名空间，不渲染。
9. **结构降版本缺 fv2 样本**：当前 25 个结构均为 fv1，真实降级路径未实测。
10. **未绑定项无跳转**：列表项不能跳到对应对象或文件。
11. **语言键无批量操作**：不能一次为多个 locale 新增键。
12. **i18n 需同步维护**：新增 UI 文案时必须同时补 zh / en 两个字典。
13. **示例只覆盖主文件**：临时库仅遍历 `primary`，资源侧注册文件（`resource_item`）与客户端实体（`client_entity`）里的组件不入桶，编辑这些文件时示例下拉可能为空。详见 [DATABASE.md](DATABASE.md) 第 10 节。

### 13.3 工程清理

14. `tools/` 保留 17 个正式脚本：`probe.py`、`e2e_test.py`、`page_test.py`、
    `structure_test.py`、`db_test.py`、`test_upload.py`、`verify_r4a/b/c.py`、
    `update_progress.py`，以及构建正式库的 5 个脚本与 `official_item116_fields.json`。
15. 一次性诊断脚本（`analyze.py`、`check_js.py`、`diagnose.py`、`scan2.py`、
    `scan_residue.py`、`struct_diag.py`）已于第五轮删除。
16. `mcbe_probe_editor/workspaces/`、`output/`、根目录 `_*.txt` 的测试残留已清理。

### 13.4 风险提示

- `copy=False` 的工作区直接写**源模组目录**，正式使用请保持默认 `copy=True`。
- 组件「提升到正式库」与「文档核实」会**永久写入**本地库，
  测试时注意先确认项目是否正确。
- 特殊文件（`tick.json`、`lines/` 等）只能在文件浏览页查看，
  刻意不提供编辑入口，避免误改。
