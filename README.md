# MCBE Probe Editor
# MCBE 探针编辑器

Minecraft Bedrock 附加包（Add-on）可视化编辑器。自动探测组件、建立组件数据库、提供组件/资产编辑与导出。

基于 Flask 构建 WebUI。

## 功能

| 模块 | 说明 |
|---|---|
| 探测 | 导入目录或 mcaddon，按 `namespace:name` 识别对象，自动关联语言/贴图/模型/动画/配方/掉落表/方块材质/feature 等引用文件 |
| 关联槽位 | 每个对象按 kind 呈现固定的「关联引用」槽位表（可选、可关联、可新建），主体文件与共享登记文件分离 |
| 索引 | 按类型/namespace 过滤浏览，显示引用树与告警 |
| 组件编辑 | 按文件 `format_version` 精确查询组件库，支持增/改/删、组件清单点选、代码区直接编辑；正式库已填充 11 桶 / 1423 条 |
| 语言键 | 在对象属性中编辑该对象自己的语言键，保留其余行 |
| 资产 | 像素画绘制器（RGB、禁绘半透明、alpha 只读保留）、Blockbench 模型命名空间改写 |
| 结构 | `.mcstructure` 版本检查与 fv2→fv1 降版本（不解析方块语义，`-1` 空位原样保留） |
| 导出 | zip / mcaddon / 仅改动文件（changes） |
| 文件浏览 | 查看全部文件，特殊文件（`tick.json`、`lines/` 等）仅在此可见 |
| 示例库 | 组件示例下拉选择 / 填入 / 复制 / 存为示例；本地库跨项目共享；同版本同类型组件的取值全部可见并标注来源对象 |
| 包信息 | manifest 独立编辑页（双包分栏、校验、模板），不进对象索引 |
| 新建对象 | item / entity / block，identifier 与所有路径自动推导，主文件由空模板生成，附加产物全部可选 |
| 多语言 | 中文 / English，顶栏切换 |

## 关联槽位

每个对象在编辑页顶部有一张「关联引用」表，按 kind 固定呈现可选槽位。所有槽位一律**可选**，只标注 `linked` / `optional` / `pending`（待指定）状态。

**item**

| 槽位 | 主体 | 说明 |
|---|---|---|
| 资源包注册 | `items/<ns>_<name>.json` | 1.10 格式注册文件 |
| attachable（含贴图） | `attachables/<name>.entity.json` + 贴图 | 一手物品模型注册 |
| attachable 动画 / 动画控制器 | `animations/` `animation_controllers/` | 可多个 |
| attachable 模型 | `models/entity/<name>.geo.json` | geometry 未解析时标「待指定」 |
| 贴图 | `textures/items/<ns>/<name>.png` | **主体是 png**，`item_texture.json` 仅作登记媒介 |
| 配方 | `recipes/<name>.json` | 可多个 |

> 物品的**语言键不是槽位**——它写在共享的 `texts/<locale>.lang` 固定位置，在编辑页「语言键」区块按对象自己的键读写。

**entity**

| 槽位 | 说明 |
|---|---|
| 实体资源注册 | `entity/<name>.entity.json` |
| 模型 | `models/**/*.geo.json`，按 geometry 标识定位 |
| 动画 / 动画控制器（行为包）/ 动画控制器（资源包） | 控制器在两侧是两个独立物，分两个槽 |
| 贴图 | `textures/entity/<ns>/<name>.png` |
| 生成规则 / 掉落表 / 交易表 / 声音 / 渲染控制器 | 行为包或资源包对应目录 |

**block**

| 槽位 | 主体 | 说明 |
|---|---|---|
| 贴图 | `textures/blocks/<name>.png` | **主体是 png，可多张**；六面地址是键名而非六张图 |
| blocks.json 登记 | 共享文件 | 六面 → 贴图键名 |
| terrain_texture.json 登记 | 共享文件 | 贴图键名 → png 路径 |
| feature / feature_rule | `features/` `feature_rules/` | 由 `replace_rules.places_block` 与 `places_feature` 两级反查 |
| 掉落表 / 配方 | 行为包对应目录 | 可多个 |

槽位行提供三类操作：

- **关联**：从候选列表或手填路径挂接已有文件——注册类自动对齐 identifier，模型自动改写 geometry 标识，动画自动写入宿主 `description.animations`，方块贴图关联时六面统一切换
- **新建**：按模组规则自动生成文件，文件名全部自动推导（唯一例外：动画控制器可指定多个不同名文件）
- **打开**：`.png`/`.tga` 进像素画编辑器；其余 JSON 切到文件分组并滚动到代码区

## 组件库

两层结构，字段标准见 [DATABASE.md](DATABASE.md)：

| 层 | 位置 | 内容 |
|---|---|---|
| 临时库 | `workspaces/<pid>/db/temp/` | 本次探测到的实际取值，随探测重建 |
| 正式库（本地库） | `mcbe_probe_editor/db/official/` | 官方文档 / schema 沉淀，跨项目共享 |

正式库当前为 **11 个桶 / 1423 条组件**，全部已核实，配套 **476 份**组件文档：

| kind | 1.12.0 | 1.16.0 | 1.21.0 | 1.26.0 |
|---|---|---|---|---|
| entity | 244 | 263 | 359 | 350 |
| item | — | 20 | 30 | 44 |
| block | 8 | 30 | 36 | 39 |

各版本互相独立，查询按文件 `format_version` 精确命中，不回落、不合并。

另有 **空模板库** `db/official/templates/<kind>/<fv>.json`，对本地库每个现存版本各一份「仅 description、无组件」的骨架，供新建对象时自选版本、查看/复制模板代码。

## 环境

- Python 3.10+
- 依赖：`pip install -r requirements.txt`（Flask、Pillow）

## 启动

```bash
pip install -r requirements.txt
python run.py
# 打开 http://127.0.0.1:5000/
```

也可直接运行应用目录内的入口：

```bash
python mcbe_probe_editor/app.py --port 5000
```

## 目录结构

```
MCBE-Probe-Editor/
├── run.py                    启动入口
├── requirements.txt
├── plan.md                   设计文档
├── PROGRESS.md               实现进度与实现说明
├── DATABASE.md               组件库数据标准（临时库 / 正式库 / 空模板库）
├── mcbe_probe_editor/        应用
│   ├── app.py                Flask 入口与蓝图注册
│   ├── routes/               project / index / editor / browser / asset / export / structure / objects ...
│   ├── services/             probe / slots / templates / objects / workspace / store / pipeline / database / texture / structure
│   ├── templates/            页面模板
│   ├── static/               CSS 与页面脚本
│   ├── workspaces/           工作区（导入的包副本、index.json、临时库、改动记录）
│   └── db/official/          正式组件数据库 + 空模板库（跨项目共享）
└── tools/                    探测/自检/正式库构建脚本
```

## 输出目录

导出产物统一落在**工程根** `output/<project_id>/`：

```
output/<project_id>/
├── <name>_<ts>.mcaddon
├── <name>_<ts>.zip
└── <name>_changes_<ts>/       仅改动文件 + _changes.json
```

## 工作区结构

```
workspaces/<project_id>/
├── meta.json                 项目元信息
├── source/
│   ├── behavior_pack/        行为包文件
│   └── resource_pack/        资源包文件
├── index.json                对象索引表
├── db/temp/                  临时组件库（本次载入生成）
└── edits/changes.json        改动记录
```

## 关键规则

**探测**

- **namespace 从文件内容探测**，不依赖目录名（同一目录可含多个 namespace）。
- **一个对象的一个文件只使用一种 `format_version`**；不同引用文件版本可不同。
- **各版本互相独立**，查询按 `format_version` 精确命中，不回落低版本、不跨版本合并。
- **特殊文件不加载进编辑器**，只在文件浏览视图可见。
- 已被对象引用的文件自动从「未绑定项」剔除。

**组件库**

- **同一 `kind + format_version` 桶内，同一组件的多个实际取值全部保留为示例**（按值去重，上限 60），编辑任一对象都能看到同版本其他对象的取值，并标注来源对象。
- **`component_groups.<组名>` 的组体直接是组件集合**（无 `components` 包装层），组内独有组件同样并入组件库。

**语言键**（对齐现有模组实测写法）

| kind | 键格式 |
|---|---|
| item | `item.<namespace:name>`（**无** `.name` 后缀） |
| entity | `entity.<namespace:name>.name` |
| block | `tile.<namespace:name>.name` |

一个 `.lang` 文件被所有对象共享；编辑时只处理该对象自己的键，其余行与顺序保持不变。

**新建对象的路径规则**（已有文件不强制改名，仅新建时采用）

| 内容 | 路径 |
|---|---|
| 行为包主文件 | `items/` `entities/` `blocks/` + `<name>.json` |
| 物品资源注册 | `items/<ns>_<name>.json` |
| attachable | `attachables/<name>.entity.json` |
| 实体资源注册 | `entity/<name>.entity.json` |
| 模型 | `models/entity/<name>.geo.json`（geometry 标识 `geometry.<name>`） |
| 物品贴图 | `textures/items/<ns>/<name>.png` |
| 实体贴图 | `textures/entity/<ns>/<name>.png` |
| attachable 贴图 | `textures/attachable/<ns>/<name>.png` |
| 方块贴图 | `textures/blocks/<name>.png` |
| 语言 | `texts/<locale>.lang` |

贴图目录不存在会自动创建。新建对象的「同时创建」选项默认**全部不勾选**，只生成行为包主文件。

## 自检脚本

```bash
python tools/e2e_test.py         # 探测 + 临时库链路
python tools/page_test.py        # 页面/API + 写回 + 导出 + 贴图 alpha
python tools/structure_test.py   # 结构检查与降版本
python tools/db_test.py          # 未绑定 + 组件数据库
```

> 写回类测试使用 `copy=True` 的独立工作区，跑完自动清理，不污染源工程。

构建正式库（按顺序执行，产物写入 `db/official/`，会覆盖同名桶）：

```bash
python tools/fetch_official_docs.py   # 抓 bedrock.dev 文档到 tools/_cache/
python tools/build_all.py             # entity / block 桶 + docs，并从临时库补齐缺失项
python tools/build_item.py            # Mojang schema -> item 1.21.0 / 1.26.0
python tools/fix_desc.py              # 修正 block / item 的 description 污染
python tools/finalize.py              # 统一 verified / note、人工剔除、聚合重写 docs
```

版本路径映射与人工确认清单见 [DATABASE.md](DATABASE.md) 第 10 节。

## 探测统计（以 Taoism Craft 为例）

| 指标 | 数值 |
|---|---|
| 对象 | 385（item 223 / entity 159 / block 3） |
| 引用 | 2850 |
| 告警 | 11 |
| 结构 | 25 |