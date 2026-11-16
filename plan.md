# MCBE Probe Editor 设计指标/概念

基本功能：自动探测组件并长久化，自动引用查询，组件数据库，组件编辑器。

> 本版为补充完善版：在原有需求基础上，补充了「命名/探测/版本/数据库存储标准/编辑器结构/工程结构」等实现级规范。标注「补充」的段落为新增或细化内容。

---

## 0. 术语与约定（补充）

- **对象（Object）**：一个可独立编辑的注册实体，如一个物品/实体/方块/结构。唯一标识 `namespace:name`。
- **对象类型（kind）**：`item` / `entity` / `block` / `structure`，后续可扩展。
- **引用文件（referenced file）**：与某对象关联、承载其部分信息的文件（语言、贴图、模型、掉落表等）。
- **主文件（primary file）**：承载对象 `description.identifier` 与主组件的文件（如行为包 `items/*.json`）。
- **format_version**：文件级版本声明，决定该文件使用哪个版本的组件/结构定义。
- **namespace**：对象标识前缀（冒号前）。**同一对象的所有引用文件必须使用同一 namespace。**
- **特殊文件（special file）**：不属于一般对象模型、也不进入编辑器的文件（如 `functions/tick.json`、资源包 `lines/` 等）。原样保留，仅在文件浏览视图中可见。

---

## 数据结构

使用对象结构，对象暂时包含实体、物品、方块和结构，待添加。以这类数据为基础，自动探测关联文件。

使用时对象标识均使用 `namespace:name` 结构，与模组实际标识一致/同步。文件名建议使用标准写法（创建时），不强制要求已有文件跟随标准。

注意所有资产文件均有 format version 设定，因此不同组件需要根据版本储存和使用。对象的不同引用文件不需要版本全部一致，只需要引用正确。

如：获取对象基本位置（文件），根据文件标注版本选择组件数据库，不同引用文件均需要先加载对应版本。

对象允许缺失引用。如物品类不一定需要资源包注册信息，可提示可添加成分。

所有信息均使用对象元素和引用链接来处理。

### 0.1 版本规则（补充）

- **一个对象的某一个文件，内部仅允许出现一个 `format_version`。** 不限制具体是哪个版本。
- 同一对象的**不同引用文件**可以有各自的 `format_version`，互不强求一致。
- 组件/结构定义的加载**以文件自身的 `format_version` 为准**，而不是以对象或项目的版本为准。
- **各版本之间互相独立，不存在继承/覆盖关系。** 选定某一版本，就只使用该版本的组件定义，不从低版本继承默认值，也不做跨版本合并。高版本新增组件不会自动出现在低版本组件表中，反之亦然。
- 若某文件缺失 `format_version`，归入 `unknown` 版本桶，并在索引中标记为 `warning: missing_format_version`。

### 0.2 命名与 namespace 探测（补充）

- **namespace 必须从文件内容探测**，不能依赖目录名（实测：`items/` 下存在 `items:`、`ny:`、`fanart:`、`construction:`；`entities/` 下存在 `entity:`、`taoism:`）。
- 探测来源按优先级：
  1. `description.identifier`（item/entity/block/attachable 等）
  2. 语言键前缀（`item.<identifier>.name`）
  3. 贴图索引键（需结合组件值反查）
  4. 文件名（仅在无法从内容探测时兜底）
- namespace 变更/冲突：同一对象在不同文件中探测到不同 namespace 时，以**主文件**为准，其余标记 `warning: namespace_mismatch`，并在 UI 中提示人工确认。

### 0.3 文件标准写法（补充，创建时采用）

参考已有模组项目惯例，新建对象时建议：

| 内容 | 建议路径 |
|---|---|
| 行为包物品 | `behavior/items/<name>.json`（或 `<ns>_<name>.json`） |
| 行为包实体 | `behavior/entities/<name>.json` |
| 行为包方块 | `behavior/blocks/<name>.json` |
| 行为包配方 | `behavior/recipes/<name>.json` |
| 实体资源注册 | `resource/entity/<name>.entity.json` |
| 资源包物品 | `resource/items/<ns>_<name>.json` |
| attachable | `resource/attachables/<name>.entity.json` |
| 掉落表 | `behavior/loot_tables/<类别>/<name>.json` |
| 贴图 | `resource/textures/<类别>/<name>.png` |
| 语言 | `resource/texts/<locale>.lang` |

> 已有文件不强制改名，仅新建时采用标准写法。

### 物品

位于行为包/items，此类文件包含 description 用于描述注册信息，components 包含基本属性。

可能关联的文件：

- 语言键：资源包/texts
- 资源包注册信息：资源包/items
- 贴图文件：任意
- 贴图索引：资源包/textures/item_texture
- attachable 模型注册信息：资源包/attachables
- attachable 模型/贴图：任意
- attachable 动画：资源包/animation_controllers，animations

> 补充：物品资源侧注册文件（1.10 格式）与行为侧物品文件（1.21.x 格式）结构完全不同，二者分属不同版本桶。贴图关联链为：`minecraft:icon` 组件值 → `item_texture.json` 的 `texture_data` 键 → 贴图路径。

### 实体

位于行为包/entities，此文件包括 description 注册信息，animation_controller 动画控制器，components 基本属性，components_groups 分组属性，events 事件控制器。

可能关联的文件：

- 动画控制器：行为包/animation_controllers
- 函数：行为包/functions
- 掉落表默认位置：行为包/loot_tables
- 交易表默认位置：行为包/trading
- 生成控制器：行为包/spawn_rules
- 实体资源注册信息：资源包/entity
- 实体模型、动画控制器、动画、贴图同上，此类信息在资源包注册信息中引用
- 实体声音控制器：资源包/sounds.json，sounds 目录
- 语言键同上

### 方块/结构

在 blocks/structures。

可能相关的文件：

- 行为包 features，feature_rules，loot_tables
- 资源包 blocks.json，贴图

> 补充：`.mcstructure` 为二进制 NBT，**不解析内容**，只做路径/引用管理与版本处理。版本处理见 4.3 结构降版本工具。

### 其他

- recipes 不一定有结构化标识，需要分开控制。
- 资源包、行为包 manifest 和 icon 均单独控制。
- `manifest.json` 用于识别包类型（`data`/`resources`）、uuid、版本、依赖关系，作为工作区初始化依据。

### 0.4 特殊文件（补充）

以下文件/目录**不属于一般对象模型**，规则统一为：

- **原样保留**（不解析、不改写、不参与组件提取）。
- **不加载进编辑器**（不出现在对象列表、不出现在组件表）。
- **仅在文件浏览视图中可见**，可在其中查看原文/下载。

已确认的特殊文件：

| 文件/目录 | 说明 |
|---|---|
| `functions/tick.json` | 无 identifier 的包级配置（`{"values":[...]}`） |
| `resource/lines/` | 资源包内的文档/图片素材（如 `.md`、`.png`），非模组运行时内容 |
| `pack_icon.png` / `pack_icon1.png` | 包图标，随 manifest 单独控制 |
| `sounds/` 下音频文件本身 | 只作为被引用资源管理，不进入组件编辑 |
| `.bak` / `.bk` / `_fv2_backup/` 等备份产物 | 视为工程残留，不探测 |

> 判定原则：能被对象模型描述、且会被游戏加载解析的，才进编辑器；其余一律归入特殊文件或纯资源。

---

## 工作流

导入 mcaddon 或指定目录，在项目目录创建工作区，开始探测基本文件，获取对象注册数据/namespace。

根据 namespace 查询所有文件是否属于该对象。

整理成索引表。

### 1.1 工作区结构（补充）

```
workspace/<project_id>/
  meta.json                # 项目元信息、导入时间、源路径
  source/
    behavior_pack/         # 导入的行为包原始文件
    resource_pack/         # 导入的资源包原始文件
  index.json               # 对象索引表（见下）
  db/                      # 临时组件数据库（JSON）
  edits/                   # 改动记录（见导出）
```

### 1.2 索引表结构（补充，JSON）

```json
{
  "project_id": "taoism",
  "packs": {
    "behavior": {"uuid": "...", "version": [5,4,0], "min_engine_version": [1,8,0]},
    "resource": {"uuid": "...", "version": [5,4,0]}
  },
  "objects": {
    "items:sword_b": {
      "kind": "item",
      "namespace": "items",
      "name": "sword_b",
      "primary": {"pack": "behavior", "path": "items/items_sword_b.json", "format_version": "1.21.50"},
      "references": [
        {"role": "resource_item", "pack": "resource", "path": "items/items_sword_b.json", "format_version": "1.10"},
        {"role": "lang", "pack": "resource", "path": "texts/zh_CN.lang", "keys": ["item.items:sword_b.name"]},
        {"role": "texture_index", "pack": "resource", "path": "textures/item_texture.json", "keys": ["sword_b"]},
        {"role": "texture", "pack": "resource", "path": "textures/items/sword_b.png"}
      ],
      "warnings": []
    }
  },
  "special_files": [
    {"pack": "behavior", "path": "functions/tick.json", "reason": "package_config"},
    {"pack": "resource", "path": "lines/guidebook.md", "reason": "assets"}
  ]
}
```

### 1.3 探测规则（补充）

- 遍历 `source/` 下所有 `.json` / `.lang`。
- 主文件：含 `minecraft:item` / `minecraft:entity` / `minecraft:block` / `minecraft:client_entity` / `minecraft:attachable` 等顶层键者，读取 `description.identifier`。
- 语言文件：按 `<prefix>.<identifier>[.name]=<value>` 解析，兼容无 `.name` 的写法；一个语言文件可归属多个对象。
- 贴图索引：解析 `texture_data`，键为用户侧引用名；对象归属通过组件值（如 `minecraft:icon`）反查，而非直接匹配 identifier。
- 引用型文件（loot_tables、spawn_rules、features、functions、trading 等）：优先按路径/命名关联，其次按文件内 `description.identifier` 或引用字段关联。
- 多对象共享文件（如语言、贴图索引）：**同一文件可被多个对象引用**，索引中以 `keys` 区分归属范围，不复制文件。
- 特殊文件（见 0.4）：探测时识别并写入 `special_files`，不参与对象归属，不进入组件提取。

### 1.4 语言键归属（补充）

- 语言键归属对象时，按键前缀映射对象类型：

| 键前缀 | 归属类型 | 示例 |
|---|---|---|
| `item.` | item | `item.items:sword_b.name=宝剑` |
| `entity.` | entity | `entity.entity:partner.name=同伴` |
| `tile.` | block | `tile.blocks:ball.name=硬化篮球` |
| `action.hint.exit.` | entity（交互提示） | `action.hint.exit.entity:sword=乘坐` |
| 其他（如 `taoism.loading.*`、`addon.get.items`） | 包级文本 | 归入特殊文本，不进对象 |

- 同一个键可能带 `.name` 后缀，也可能不带（`item.items:sword_b.name` 与 `item.items:talisman` 并存），解析时**两者都要兼容**。
- 键本身的写法（是否带 `.name`、是否带后缀）**不做强制规范化**，保持原样读写。

---

### 储存

根据索引表的信息读取实际文件，提取组件信息，分版本储存到临时数据库。

临时数据库在经过文档核实后转存到正式数据库，编辑时允许同时查询临时数据库和正式数据库。

核实有关内容加上独立文档，此部分由 agent 完成。

临时数据库仅在载入模组时创建，退出时释放，正式数据库长久本地保存。

### 2.1 存储格式标准（补充，统一 JSON）

**临时数据库**（载入时生成，退出释放）：

```
db/temp/<project_id>/
  inventory.json                 # 本次探测到的组件清单与来源
  components/
    item/<format_version>.json
    entity/<format_version>.json
    block/<format_version>.json
  structures/
    <format_version>.json
```

**正式数据库**（长久本地保存）：

```
db/official/
  components/
    item/<format_version>.json
    entity/<format_version>.json
    block/<format_version>.json
  docs/
    item/<component_key>.md      # agent 核实的独立文档
  meta.json                      # 版本、来源、核实状态摘要
```

**组件条目标准结构**（`components/<kind>/<format_version>.json`）：

```json
{
  "kind": "item",
  "format_version": "1.21.50",
  "components": {
    "minecraft:max_stack_size": {
      "value_type": "integer",
      "default": 64,
      "min": 1,
      "max": 64,
      "description": "最大堆叠数量",
      "doc_ref": "docs/item/minecraft_max_stack_size.md",
      "verified": true,
      "source": "manual",
      "added_in": "1.20.0",
      "deprecated": false
    }
  }
}
```

- `value_type`：`integer` / `float` / `boolean` / `string` / `enum` / `object` / `array` / `any`。
- `doc_ref`：指向 `docs/` 下独立文档。
- `verified`：是否经过文档核实。
- 同一 `format_version` 下同名组件以「最后写入为准」，但保留 `source` 字段区分人工/自动。
- **按版本分文件存放，各版本文件互相独立，不做继承与合并**（见 0.1）。查询时按文件 `format_version` 精确命中对应桶；无对应桶则视为该版本暂无组件定义，不回落低版本。

### 2.2 核实流程（补充）

- 触发：手动触发或工具批量触发；agent 读取组件来源与官方文档，写入 `docs/` 并提供摘要。
- 产出：对应 `docs/<kind>/<component>.md` + 组件条目 `verified: true`。
- 未核实条目允许存在，编辑时以 `verified: false` 提示。

---

### 编辑

根据 namespace 和探测得到的索引表将对象所有所属信息显示为可编辑参数的组件表，组件结构根据数据库读取，允许从数据库添加属性，代码区手动编辑，删除属性。

注意此部分层次结构，根据实际情况细分。

### 3.1 编辑器层次结构（补充）

```
对象 (namespace:name)
└── 文件分组（按 role + format_version）
    ├── 主文件（behavior/items/...）
    │   ├── description（注册信息）
    │   └── components（组件表）
    │       └── 组件 → 属性（值/枚举/嵌套对象）
    ├── 引用文件（resource/items/...）
    │   └── components
    ├── 语言文件
    │   └── 键 → 值
    └── 贴图索引 → 贴图
```

- 每层显示其 `format_version` 与来源路径。
- 组件表支持：从数据库添加属性（按当前文件版本过滤可用组件）、编辑、删除。
- 代码区与组件表**双向同步**：代码区提交时重新解析并按当前版本校验；组件表变更实时反映到代码区预览。
- 结构差异（如 items 行为侧 vs 资源侧）按各自版本模板渲染。

### 3.2 语言键编辑（补充）

- **语言键的名称在对象属性中编辑**，即：编辑某对象时，只处理属于该对象的那些键（`keys` 列表中列出的键），不整文件铺开。
- **单个对象只单独处理它自己的语言键**，不同时编辑其他对象的键，即使它们在同一 `.lang` 文件里。
- 键的具体写法**视情况保留**：原有键不重写格式（带不带 `.name` 都保持原样）；新建键时按该对象既有写法对齐，无既有写法则默认 `item.<id>.name` 形式。
- 保存时只回写该对象涉及的行，其余行与顺序保持不变。

### 3.3 编解码策略（补充）

- 采用「解析 → 模型 → 渲染」而非纯文本替换，保留原始键序与缩进风格（尽量）。
- 保存时校验 JSON 合法性，非法内容阻断保存并提示。

### 3.4 文件浏览视图（补充）

- 提供独立的文件浏览视图，以树形结构展示工作区全部文件（含行为包、资源包、特殊文件、未归属文件）。
- 在浏览视图中可查看原文、查看二进制信息（如 `.mcstructure` 大小与 `format_version`）、下载。
- **特殊文件只能在浏览视图中查看，不提供组件式编辑**，避免误改 `tick.json`、`lines/` 等非对象内容。
- 普通对象文件同样可从浏览视图跳转到其组件编辑页。

---

### 资产编辑

贴图部分：物品贴图内置像素画绘制器，可将绘制结果直接储存至标准位置或从指定位置编辑，颜色要求不允许绘制半透明像素但允许读取时存在且可被继续写入，需要颜色临时储存，色板和去色，颜色格式 rgb。

模型：本地不处理，使用 blockbench，引导放在本地，并将其于已有对象关联，自动更改模型 namespace。

模型贴图：同理。

对象属性信息：见上文。

### 4.1 像素画绘制器补充

- 画布尺寸：默认 16×16，可选 32×32 / 64×64（新建时指定）。
- 读取：支持 PNG，保留 alpha 通道信息但不允许新增半透明像素；已存在的半透明像素可被读取并「原样写回」，编辑时其 alpha 保持不变。
- 调色板：RGB 色板，支持去色（灰度）。
- 临时颜色存储于内存/会话，不落盘。

### 4.2 Blockbench 关联（补充）

- 不本地渲染/编辑模型，仅做外链引导。
- 关联流程：选择对象 → 指定 `.geo.json`/`.bbmodel` → 自动重写其中的 `geometry.<ns>.<name>` 命名空间与对象一致。
- 模型贴图同理。

### 4.3 结构降版本工具（补充）

- **不解析结构内容**，但提供 `.mcstructure` 的 format_version 降级工具（参考既有实现 `Taoism_B/structures/downgrade_mcstructure.py`）。
- 转换规则（fv2 → fv1）：
  - `format_version` 由 `2` 改为 `1`。
  - `structure.block_indices` 由 `List<IntArray>`（`TAG_List` 元素类型 `TAG_Int_Array`）转为两层 `List<List<Int>>`（外层 `TAG_List`，内层 `TAG_Int`）。
  - **`-1` 必须原样保留**：`-1` 是「结构空位」，放置时跳过该格、保留目标位置原方块；空气索引则会清除方块。二者不可混同，绝不能把 `-1` 换成 air 索引。
  - 缺失液体层时补一层全 `-1`；已有液体层则保留原值，不丢弃已有水。
  - 只改容器编码，不动 `palette` 方块内容、方块实体、`entities`、坐标。
- 工程约束：
  - **幂等**：只处理 `format_version == 2`，已是 `1` 直接跳过，重复运行不会叠加层。
  - **备份**：转换前复制到 `_fv2_backup/`（可关闭，不建议）。
  - **转后自检**：重新解析并校验层数、长度、索引范围（`-1` 或落在 palette 范围内）。
  - 支持 `--dry-run`（预演）与 `--verify-only`（仅校验）。
- 在 UI 中以「结构版本检查/降级」入口提供，操作前明确提示备份位置与影响范围。

---

### 导出

任何改动均在本地工作区，并记录修改文件。

导出可选 zip、mcaddon 或记录。

zip 模式时将工作区的资源包、行为包压缩，mcaddon 在此基础上更改压缩包后缀。

记录仅导出改动过的文件，保持位置。

### 5.1 改动记录格式（补充）

```
edits/
  changes.json
```

```json
{
  "project_id": "taoism",
  "changes": [
    {"path": "Taoism_B/items/items_sword_b.json", "op": "modify", "time": "..."},
    {"path": "Taoism_R/textures/items/sword_b.png", "op": "modify", "time": "..."},
    {"path": "Taoism_R/texts/zh_CN.lang", "op": "modify", "time": "..."}
  ]
}
```

- `op`：`add` / `modify` / `delete`。
- 记录模式导出时按 `changes.json` 逐条复制到输出目录，保持相对路径。
- 特殊文件与备份目录不参与改动记录。

---

## 工程结构（补充）

- 技术栈：Python + Flask。
- 建议目录：

```
mcbe_probe_editor/
  app.py                 # Flask 入口
  routes/
    project.py           # 导入/工作区
    index.py             # 索引/探测结果
    editor.py            # 组件编辑
    asset.py             # 贴图/模型
    browser.py           # 文件浏览视图
    export.py            # 导出
  services/
    probe.py             # 探测与 namespace 提取
    database.py          # 组件数据库读写
    lang.py              # 语言文件解析
    texture.py           # 贴图索引/像素处理
    structure.py         # 结构版本检查/降级
  templates/             # WebUI
  static/
```

- WebUI 结构不限，保持完整功能即可。
- 错误处理：导入失败/版本不匹配/非法文件时，记录到索引 `warnings` 并在 UI 提示，不中断整体探测。

---

## 其他要求

- 前端使用 flask 构建 webui，ui 结构不限制，保持完整功能即可。
- 允许参考已有模组项目 `D:\git\MCBE-add-on-Taoism-Craft\` 来了解。
- 开始工作前先补充要求文档中的不足（本版已完成主要补充）。

---

## 决策记录（已确认）

1. **版本关系**：分版本独立，各版本之间没有继承/覆盖关系。选定某版本即按该版本组件使用。
2. **语言键**：语言键名称在对象属性中编辑；单对象只单独处理它自己的键；键的具体写法视情况保留，不强制规范化。
3. **结构文件**：不解析内容，仅做引用/路径管理，但提供降版本工具（见 4.3）。
4. **特殊文件**：`tick.json`、资源包 `lines/` 等不属于一般模组内容，原样保留且不加载进编辑器，仅在文件浏览视图中可见。