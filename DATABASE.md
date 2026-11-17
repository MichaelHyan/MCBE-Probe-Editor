# 组件库数据标准（临时库 / 正式库）

> 本文档是组件库的**字段与写入规则权威说明**，对应实现 `services/database.py`。
> 设计意图见 [plan.md](plan.md) 第 2 节，实现状态见 [PROGRESS.md](PROGRESS.md)。
> 修改库结构或字段语义时，**必须同步更新本文档**。

最后核对：第八轮（关联槽位 / 空模板库）后与代码逐项对齐。

---

## 1. 文档定位

组件库分两层，**数据标准不同**，不能混用字段语义：

| 层 | 名称 | 位置 | 生命周期 | 定位 |
|---|---|---|---|---|
| 短期 | **临时库**（temp） | `workspaces/<pid>/db/temp/` | 随项目探测重建，重建前整体释放 | 本次探测到的**实际取值**，只读参考 |
| 长期 | **正式库**（official，又称「本地库」） | `mcbe_probe_editor/db/official/` | 长久保存，跨项目共享 | 人工沉淀 + 文档核实后的**权威条目** |

两者**都按 `kind + format_version` 分桶**，各版本互相独立，查询精确命中，不回落低版本、不跨版本合并（plan.md 0.1）。

UI 里「示例」下拉同时消费两者，来源标注为 `本项目` / `本地库` / `官方`，映射规则见第 7 节。

---

## 2. 两库对照

| 维度 | 临时库 temp | 正式库 official |
|---|---|---|
| 写入者 | 探测流水线自动生成 | 构建脚本批量导入 + `promote` + `record_example` + 文档核实 |
| 桶文件顶层字段 | `kind` / `format_version` / `generated` / `components` | `kind` / `format_version` / `updated` / `components` |
| 条目 `source` | 恒为 `"probe"` | `"probe"`（提升时整体复制）/ `"manual"`（手动存示例） |
| 条目 `verified` | 恒为 `false` | 核实后为 `true` |
| 条目 `note` / `description` | 恒为空 | 由文档核实流程填写 |
| `default` / `example` | 本模组**首个**遇到的取值 | 官方示例或提升时的取值 |
| `examples[].source` | 恒为 `"project"` | `"project"` / `"local"` / `"official"` 三种并存 |
| `examples[].origin` | 来源对象 identifier | 来源对象 identifier 或文档出处 |
| 单组件 `examples` 上限 | 60 | 60 |
| 是否进 Git | 否（`workspaces/` 已忽略） | 是（默认纳入版本管理，见第 10 节） |

---

## 3. 目录布局

```
mcbe_probe_editor/
├── db/
│   └── official/                       正式库（跨项目共享）
│       ├── components/
│       │   ├── item/<fv>.json
│       │   ├── entity/<fv>.json
│       │   ├── block/<fv>.json
│       │   └── structure/<fv>.json
│       ├── docs/
│       │   └── <kind>/<component>.md
│       └── templates/                  空模板库（新建对象用）
│           ├── item/<fv>.json
│           ├── entity/<fv>.json
│           └── block/<fv>.json
└── workspaces/
    └── <pid>/
        └── db/
            └── temp/                 临时库（本项目专用）
                ├── inventory.json
                └── components/
                    ├── item/<fv>.json
                    ├── entity/<fv>.json
                    ├── block/<fv>.json
                    └── structure/<fv>.json
```

文件名规则（`safe_fv()`）：

- `format_version` 转为字符串后，把 `[^0-9A-Za-z._-]` 全部替换为 `_`。
- `None` 或空字符串 → `unknown`。
- 例：`1.21.50` → `1.21.50.json`；`[1,2,0]` → `_1_2_0_.json`。

`kind` 限定为 `KNOWN_KINDS = ("item", "entity", "block", "structure")`，其他值不入库。

---

## 4. 公共值处理规则

### 4.1 value_type 推断（`infer_value_type`）

由实际 Python 值类型推断，**不是官方 schema**：

| Python 类型 | value_type |
|---|---|
| `bool` | `boolean`（先于 int 判断，避免 `True` 被当整数） |
| `int` | `integer` |
| `float` | `float` |
| `str` | `string` |
| `list` | `array` |
| `dict` | `object` |
| 其他 | `any` |

`VALUE_TYPES` 常量列出全部取值，其中 `enum` 保留但**探测不会自动产出**。

### 4.2 取值裁剪（`clip_value` / `summarize_value`）

入库前统一走 `clip_value(value, limit=8000)`：

- JSON 序列化后长度 **≤ 8000** → 原值直接入库（可回填）。
- 超过 8000 → 退化为 `summarize_value()` 摘要：

| 类型 | 摘要形态 |
|---|---|
| 标量 | 原值 |
| `array` | `{"length": n, "sample": 前 3 项}` |
| `object` | `{"keys": 前 20 个键, "key_count": n}` |

> 退化为摘要后**不再是可直接回填的真实值**，UI 填入会得到摘要对象而非原始数据。

### 4.3 去重指纹（`_value_sig`）

```python
json.dumps(value, ensure_ascii=False, sort_keys=True)
```

序列化失败时退化为 `repr(value)`。用于 `examples` 去重。

### 4.4 条目兼容读取（`_norm_examples`）

读取 `examples` 时统一走 `_norm_examples(entry)`，兼容旧格式：

1. `entry["examples"]` 是非空列表 → 直接返回。
2. 否则取 `entry["example"]`，为空再取 `entry["default"]`，包装成单条：
   `{"label": "probe", "source": "project", "value": v, "origin": null, "added": null}`
3. 都为空 → 返回 `[]`。

**这样历史库文件（只有单条 `example`）无需迁移即可读取。**

---

## 5. 临时库（temp）数据标准

### 5.1 inventory.json

探测清单，记录本次入库的文件级明细。

```json
{
  "project_id": "TaoismV5",
  "generated": "2026-11-16 19:06:56",
  "objects": 385,
  "files": [
    {
      "object": "entity:arrow",
      "pack": "behavior",
      "path": "entities/arrow.json",
      "kind": "entity",
      "format_version": "1.21.40",
      "components": 7,
      "group_components": 1,
      "container": "minecraft:entity"
    }
  ],
  "buckets": [
    { "kind": "entity", "format_version": "1.21.40", "count": 14 }
  ]
}
```

| 字段 | 说明 |
|---|---|
| `files[].object` | 对象 identifier |
| `files[].components` | 该文件顶层 `components` 的组件数 |
| `files[].group_components` | 该文件 `component_groups` 内提取到的组件数 |
| `files[].container` | 组件所在顶层键（如 `minecraft:entity`） |
| `files[].error` | 读取失败时存在，替代上述字段 |
| `buckets[]` | 落盘后的桶清单，按 `(kind, format_version)` 排序 |

读取失败的文件不会中断探测，只写入 `error` 并跳过。

### 5.2 桶文件

路径：`workspaces/<pid>/db/temp/components/<kind>/<fv>.json`

```json
{
  "kind": "item",
  "format_version": "1.21.50",
  "generated": "2026-11-16 19:06:56",
  "components": { }
}
```

`format_version` 字段存**原始标签**（`fv_label`），与文件名可能不同（文件名经 `safe_fv` 处理）。

### 5.3 组件条目

```json
{
  "minecraft:durability": {
    "value_type": "object",
    "default": { "max_durability": 256 },
    "example": { "max_durability": 256 },
    "examples": [
      {
        "label": "probe",
        "source": "project",
        "value": { "max_durability": 256 },
        "origin": "fanart:machete_handle",
        "added": "2026-11-16 19:06:56"
      },
      {
        "label": "probe",
        "source": "project",
        "value": { "max_durability": 512 },
        "origin": "fanart:machete_knife",
        "added": "2026-11-16 19:06:56"
      }
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
```

| 字段 | 类型 | 临时库取值 |
|---|---|---|
| `value_type` | string | 由首个值推断（第 4.1 节） |
| `default` | any | **首个**遇到该组件的取值（经 `clip_value`） |
| `example` | any | 同 `default` |
| `examples` | array | 同桶所有对象的取值，按值去重，上限 60 |
| `note` | string | `""` |
| `description` | string | `""` |
| `doc_ref` | string\|null | `null` |
| `verified` | bool | `false` |
| `source` | string | `"probe"` |
| `added_in` | string\|null | `null`（探测无法得知引入版本） |
| `deprecated` | bool | `false` |

**关键点：`default` / `example` 只反映首个取值，多值只体现在 `examples`。** 这是刻意的——`default` 代表「本桶一个具名参考值」，`examples` 才是全集。

### 5.4 examples 条目

| 字段 | 说明 |
|---|---|
| `label` | 固定 `"probe"` |
| `source` | 固定 `"project"` |
| `value` | 实际取值（经 `clip_value`） |
| `origin` | 来源对象 identifier，如 `entity:arrow` |
| `added` | 写入时间 `%Y-%m-%d %H:%M:%S` |

### 5.5 写入规则

构建入口 `build_temp(project_id, index, reader)`，只遍历对象的**主文件**（`index.objects.<ident>.primary`），不处理引用文件。

流程：

1. 按 `(kind, format_version)` 分组为 `buckets`。
2. 顶层组件与 `component_groups` 内组件**统一**走 `add_project_value()`：
   - 桶内无该组件 → `build_entry(name, value, source="probe", origin=ident)`，生成新条目（`default` / `example` = 首值，`examples` = 1 条）。
   - 桶内已有该组件 → `add_project_example(entry, value, ident)`。
3. 全部对象处理完后落盘，并写 `inventory.json`。

`add_project_example` 规则：

- 按 `_value_sig(value)` 与现有 `examples` 比对，**值相同即跳过**（不追加重复值）。
- 达到 `MAX_EXAMPLES = 60` 后不再追加。
- 追加条目 `source="project"`、`label="probe"`、`origin=<对象 identifier>`。

> 去重只看**值**，不看来源对象。若两个对象取同一值，只保留先遇到的那个 `origin`。

### 5.6 提取范围

`extract_components(data, kind)`：

- 按 `kind` 取顶层键（`minecraft:item` / `minecraft:entity` / `minecraft:block`），读其 `components`。
- 失败则兜底扫任意 `minecraft:*` 顶层键。
- 返回 `(components, container)`。

`extract_group_components(data, kind)`：

- 遍历 `component_groups.<组名>`，**组体直接是组件集合**（标准写法无 `components` 包装层）。
- 兼容带 `components` 包装层的非标准写法（组内无 `minecraft:*` 键时才查包装层）。
- 只收集以 `minecraft:` 开头的键；同名取**首个**。
- 结果并入同 `(kind, fv)` 桶，保证组件组的「+ 添加」与顶层一致。

### 5.7 重建与释放

- `pipeline.run_probe()` 在构建前先调 `db.clear_temp(project_id)`，**整体删除** `db/temp/` 后重建。
- 因此临时库内容**只反映最近一次探测**，不会残留历史桶。
- 修改库结构或提取逻辑后，必须重新探测才生效。

---

## 6. 正式库（official）数据标准

### 6.1 桶文件

路径：`mcbe_probe_editor/db/official/components/<kind>/<fv>.json`

```json
{
  "kind": "item",
  "format_version": "1.21.50",
  "updated": "2026-11-16 19:10:00",
  "components": { }
}
```

与临时库的差别：`updated` 替代 `generated`，表示最后一次写入时间（`save_official_bucket` 自动刷新）。

### 6.2 组件条目

字段集合与临时库**完全相同**，语义不同：

| 字段 | 正式库语义 |
|---|---|
| `default` | 权威参考值（官方默认值，或提升时的首个实际值） |
| `example` | 权威示例值；`record_example` 写入时会被更新为最新存下的值 |
| `examples` | 多来源示例集合（`project` / `local` / `official` 并存） |
| `note` | 用法说明，由文档核实流程填写 |
| `description` | 组件说明 |
| `doc_ref` | 指向 `docs/` 的相对路径，如 `docs/item/minecraft_durability.md` |
| `verified` | 是否已核实 |
| `source` | `"probe"`（提升时整体复制）/ `"manual"`（手动存示例时新建） |
| `added_in` | 引入版本，人工填写 |
| `deprecated` | 是否已弃用 |

### 6.3 examples 条目与 source 语义

| `source` | 含义 | 产生方式 |
|---|---|---|
| `project` | 某项目的实际取值 | 探测提升（`promote_to_official`）合并进来 |
| `local` | 本地沉淀 | 编辑器「存为示例」（`record_example`，`source="local"`） |
| `official` | 官方文档核实 | 文档核实流程写入 |

条目结构：`{label, source, value, origin, added}`。

- `origin` 对 `project` 是对象 identifier，对 `official` 是文档出处（如 `wiki`）。
- 上限 60 条（`record_example`、`promote_to_official` 均按 `[:60]` 截断）。

### 6.4 docs/

路径：`db/official/docs/<kind>/<component>.md`，组件名经 `[^0-9A-Za-z._-]` → `_` 处理。

- `write_doc(kind, component, content)` 写入并返回绝对路径。
- `read_doc(kind, component)` 不存在时返回 `None`。
- `mark_verified(kind, fv, component, doc_rel)` 把条目标记为 `verified = true`，并写入 `doc_ref`。

### 6.5 写入入口

#### promote_to_official(project_id, kind, fv, names=None)

把临时库条目提升到正式库。

- 正式库**无**该组件 → 整体复制临时库条目（`source` 保持 `"probe"`）。
- 正式库**有**该组件 → 只补**缺失字段**，不覆盖已有值（保护已核实的 `description` / `note`）；合并 `examples`：
  - 按 `_value_sig(value)` 去重；
  - 追加条目的 `source` 统一改为 `"project"`；
  - `origin` 保留原对象 identifier，为空才回填 `project_id`；
  - 截断 60 条。
- 返回 `{ok, added, updated, total}`。

#### record_example(kind, fv, component, value, label=None, source="local", origin=None)

把一条示例存进正式库（编辑器「存为示例」）。

- 条目不存在 → `build_entry(..., source="manual", origin=origin)` 新建。
- 去重条件是 **`value` 相同且 `source` 相同**（比临时库宽松，允许同值不同来源共存）。
- 追加后同步更新 `entry["example"] = value`，截断 60。
- 返回 `{ok, added, count}`。

#### mark_verified(kind, fv, component, doc_rel=None)

正式库条目置 `verified = true`，可选写入 `doc_ref`。条目不存在返回 `False`。

---

## 7. 示例查询与合并视图

### 7.1 list_examples(project_id, kind, fv, component)

供编辑器「示例」下拉使用，返回 `[{source, label, value, origin, added}]`。

收集顺序与 `source` **重新映射**：

| 来源桶 | 原始 `examples[].source` | 输出 `source` |
|---|---|---|
| 正式库 | `"official"` | `"official"` |
| 正式库 | 其他（`project` / `local` / 缺失） | `"local"` |
| 临时库 | 任意 | `"project"` |

> 注意：正式库里 `source="project"` 的历史示例在这里也会被标成 `local`。前端只保证「本项目 / 本地库 / 官方」三档，不细分历史来源。

去重键为 `(source, _value_sig(value))`，保留顺序（正式库在前，临时库在后）。

`label` / `origin` / `added` 从原文透传，因此临时库示例能显示来源对象。

### 7.2 query_components(project_id, kind, fv)

供组件表、组件清单、数据库页使用的合并视图，返回：

```json
{
  "kind": "item",
  "format_version": "1.21.50",
  "temp": { },
  "official": { },
  "merged": { }
}
```

`merged` 构建规则：

1. 先放入正式库全部条目，标 `origin = "official"`。
2. 再叠临时库条目：
   - **同名**：复制正式库条目，追加
     - `actual` = 临时库 `default`
     - `actual_type` = 临时库 `value_type`
     - `in_use = true`
     - `examples` = 正式库 `examples` + 临时库独有值（`source` 改为 `"project"`，按值去重）
     - 正式库无 `example` 且临时库有 → 回填 `example`
   - **不同名**：整条放入，标 `origin = "temp"`、`in_use = true`。

`origin` 只有 `"official"` / `"temp"` 两种，UI 据此显示「正式库 ✓ / 临时库」。

### 7.3 消费方差异

| 消费方 | 数据来源 | 看到的值 |
|---|---|---|
| 编辑器「示例」下拉 | `list_examples()` | `examples` 全集（多值），标注来源对象 |
| 「+ 添加」组件清单预览 | `query_components().merged` | 条目 `example`（**单个值**） |
| 数据库页「示例」列 | `query_components().merged` | 条目 `example`（**单个值**） |

> 即：**只有编辑器示例下拉能看全同版本多值**，组件清单和数据库页仍展示单个代表性示例。

### 7.4 桶列表

- `list_temp_buckets(project_id)` → `[{kind, format_version, count}]`
- `list_official_buckets()` → `[{kind, format_version, count, verified}]`

`count` 是组件条目数，`verified` 是已核实条目数。

---

## 8. 生命周期

```
导入项目
  └─ pipeline.run_probe()
       ├─ probe.run()               探测对象与引用
       ├─ ws.save_index()           写 index.json
       ├─ db.clear_temp()           整体删除旧临时库
       └─ db.build_temp()           按 kind+fv 重建桶
            └─ 多对象同组件 → examples 累加（上限 60）

编辑组件
  ├─ GET  /db/examples              list_examples()      正式库 + 临时库
  ├─ POST /db/examples/add          record_example()     写正式库
  └─ POST /db/promote               promote_to_official() 临时库 → 正式库

文档核实
  ├─ POST /db/doc                   write_doc()
  └─ POST /db/verify                mark_verified()
```

- 临时库**随探测重建**，不手动维护。
- 正式库**永久保存**，只有 `promote` / `record_example` / `mark_verified` 会写入。
- 提升与核实是**不可撤销的文件写入**，操作前确认项目正确。

---

## 9. 字段速查

### 9.1 桶文件

| 字段 | temp | official |
|---|---|---|
| `kind` | ✓ | ✓ |
| `format_version` | ✓ | ✓ |
| `generated` | ✓ | — |
| `updated` | — | ✓ |
| `components` | ✓ | ✓ |

### 9.2 组件条目

| 字段 | 类型 | temp 默认 | official 默认 |
|---|---|---|---|
| `value_type` | string | 推断值 | 推断值 / 人工 |
| `default` | any | 首值 | 权威值 |
| `example` | any | 首值 | 权威示例 |
| `examples` | array | 多值（≤60） | 多来源（≤60） |
| `note` | string | `""` | 人工填写 |
| `description` | string | `""` | 人工填写 |
| `doc_ref` | string\\|null | `null` | 文档核实后写入 |
| `verified` | bool | `false` | 核实后 `true` |
| `source` | string | `"probe"` | `"probe"` / `"manual"` |
| `added_in` | string\\|null | `null` | 人工填写 |
| `deprecated` | bool | `false` | 人工填写 |

### 9.3 examples 条目

| 字段 | temp | official |
|---|---|---|
| `label` | `"probe"` | `"probe"` / `"manual"` / 自定义 |
| `source` | `"project"` | `"project"` / `"local"` / `"official"` |
| `value` | 实际值 | 实际值 / 官方值 |
| `origin` | 对象 identifier | 对象 identifier 或文档出处 |
| `added` | 时间戳 | 时间戳 |

---

## 10. 正式库填充现状（首版）

`db/official/` 已按第 6 节标准完成首版填充，覆盖 **3 类 x 4 个 format_version，共 11 个桶、1423 条组件**。

### 10.1 桶清单

| kind | format_version | 条目数 | verified |
|---|---|---|---|
| entity | 1.12.0 | 244 | 244 |
| entity | 1.16.0 | 263 | 263 |
| entity | 1.21.0 | 359 | 359 |
| entity | 1.26.0 | 350 | 350 |
| item | 1.16.0 | 20 | 20 |
| item | 1.21.0 | 30 | 30 |
| item | 1.26.0 | 44 | 44 |
| block | 1.12.0 | 8 | 8 |
| block | 1.16.0 | 30 | 30 |
| block | 1.21.0 | 36 | 36 |
| block | 1.26.0 | 39 | 39 |

`docs/` 按 **(kind, component) 聚合**：同一组件在不同版本各占一节，避免跨版本覆盖。
当前 476 份：entity 374 / item 50 / block 52。

### 10.2 数据源与版本映射

| 数据源 | 覆盖 | 说明 |
|---|---|---|
| [bedrock.dev](https://bedrock.dev) 按版本文档 | entity x 4、block x 4、item 1.16.0 | 组件标题 / 表格行 + 参数表 `Default Value` 列合成 `default` |
| [Mojang/bedrock-samples](https://github.com/Mojang/bedrock-samples) JSON Schema | item 1.21.0、item 1.26.0 | `metadata/json_schemas/server/item/`，权威机器可读，`default` 由 schema 递归提取 |
| 项目临时库 | 24 条（见 10.4） | 文档 / schema 未收录，取项目实际值 |

bedrock.dev 版本路径（`<major>/<build>`）：

| format_version | 路径 |
|---|---|
| 1.12.0 | `1.12.0.0/1.12.0.28` |
| 1.16.0 | `1.16.0.0/1.16.100.60` |
| 1.21.0 | `1.21.0.0/1.21.130.28` |
| 1.26.0 | `1.26.0.0/1.26.60.5` |

Mojang schema 版本：

| format_version | schema 版本 | 备注 |
|---|---|---|
| item 1.21.0 | `item/1.20.50` | 最近可得，非精确匹配 |
| item 1.26.0 | `item/1.26.30` | 合并版 `Item Components.json` + `$ref` 逐个解析 |

> 抓取注意：`raw.githubusercontent.com` 在部分环境因 TLS 吊销检查失败，
> 需改用 GitHub Contents API 的 raw 媒体类型（`Accept: application/vnd.github.raw`）。
> bedrock.dev 需带 `User-Agent`，否则返回 403。

### 10.3 构建脚本

`tools/` 下保留 5 个构建脚本，**按顺序执行**即可完整复现：

| 顺序 | 脚本 | 作用 |
|---|---|---|
| 1 | `fetch_official_docs.py` | 抓 bedrock.dev 的 entity / item / block 文档到 `tools/_cache/` |
| 2 | `build_all.py` | 解析文档 -> 写 entity / block 桶与 docs；并从临时库补齐文档缺失项 |
| 3 | `build_item.py` | 用 Mojang schema 建 item 1.21.0 / 1.26.0 桶与 docs |
| 4 | `fix_desc.py` | 用嵌套表感知解析修正 block / item 的 `description` 污染 |
| 5 | `finalize.py` | 统一 `verified` 与 `note`、执行人工剔除、按组件聚合重写 docs |

配套数据：`tools/official_item116_fields.json` 记录 item 1.16.0 的子字段结构
（官方文档该列默认值整列为空，仅提供字段名，`default` 保持 `{}`，不臆造）。

`db_test.py`、`e2e_test.py`、`page_test.py`、`probe.py`、`structure_test.py`、
`test_upload.py`、`update_progress.py`、`verify_r4a/b/c.py` 为原有测试脚本，与构建无关。
`tools/_cache/` 为可重建缓存，已清理。

### 10.4 人工确认记录

以下 24 条在 bedrock.dev 文档中**确实未收录**（全文检索无匹配），取自项目实际值，
经人工逐条确认存在后入库：`source: "probe"`、`verified: true`、
`note: "人工确认；取自项目实际值（<fv>）"`。

| format_version | 组件 |
|---|---|
| entity 1.12.0（3） | `minecraft:physics`、`minecraft:pushable`、`minecraft:conditional_bandwidth_optimization` |
| entity 1.16.0（4） | `minecraft:health`、`minecraft:leashable_to`、`minecraft:is_collidable`、`minecraft:knockback_resistance` |
| entity 1.21.0（4） | `minecraft:health`、`minecraft:knockback_resistance`、`minecraft:movement`、`minecraft:underwater_movement` |
| entity 1.26.0（13） | `minecraft:knockback_resistance`、`minecraft:follow_range`、`minecraft:health`、`minecraft:jump.static`、`minecraft:movement`、`minecraft:movement.basic`、`minecraft:pushable`、`minecraft:persistent`、`minecraft:projectile`、`minecraft:transformation`、`minecraft:balloonable`、`minecraft:behavior.look_at_entity`、`minecraft:behavior.look_at_player` |

**人工剔除**（确认不应入库，已从正式库移除）：

| format_version | 组件 | 原因 |
|---|---|---|
| entity 1.21.0 | `minecraft:player.exhaustion`、`minecraft:player.experience`、`minecraft:player.level`、`minecraft:player.saturation` | 属玩家属性，非实体组件，误探测产生 |

> 剔除逻辑固化在 `finalize.py` 的 `REMOVE` 常量，重跑不会回流。
> 临时库仍保留这些条目（探测产物只读），编辑器未命中正式库时会看到临时库来源。

### 10.5 verified 语义约定

- **官方文档 / 官方 schema 来源**（`source: "manual"`）：视为已核实，`verified: true`，不再人工二次复核。
- **项目实际值补充**（`source: "probe"`）：必须经人工确认存在后才置 `verified: true`，`note` 注明「人工确认」。
- 未确认的条目不写入正式库，宁缺勿滥。

---


### 10.6 数据统计（当前）

| 指标 | 数值 |
|---|---|
| 组件条目 | 1423（11 桶） |
| `verified: true` | 1423（100%） |
| 有 `description` | 1267（89.0%），均为英文原文 |
| 有 `note` | 1423（100%） |
| 有 `doc_ref` | 1399（98.3%） |
| `source: manual` | 1399（官方文档 / schema） |
| `source: probe` | 24（官方未收录，人工确认） |
| `examples` 总数 | 1446 |
| `examples` : `official` | 1399 |
| `examples` : `project` | 47 |
| `docs/` 文档 | 476（entity 374 / item 50 / block 52） |
| `added_in` | 全为 `null`（官方文档未给引入版本） |
| `deprecated` | 全为 `false` |

> `docs/` 中 44 份只覆盖单版本、120 份覆盖两版本、109 份三版本、203 份四版本。
> 24 条 probe 条目中 11 条带多条 `project` 示例（如 entity 1.26.0 的
> `minecraft:health` 有 6 条），是第六轮「同桶多值合并」的产物。
## 10.7 空模板库（templates/）

新建对象时的主文件骨架，与正式库**同源不同物**：目录并列、版本对齐，但内容只有 `description` 与空 `components`。

```
db/official/templates/<kind>/<fv>.json
```

### 10.7.1 生成规则

`services/templates.py::ensure_templates()`：

1. 扫 `list_official_buckets()` 得到正式库现存的全部 `(kind, format_version)`。
2. 每个组合在 `templates/<kind>/<fv>.json` 缺文件时写一份骨架。
3. 已存在的**不覆盖**（避免冲掉人工调整）。

因此模板库版本集合总是正式库版本集合的子集/等集。

### 10.7.2 骨架内容

只有 `description`（identifier 用 `__IDENT__` 占位）与空 `components`：

```json
{
  "format_version": "1.21.50",
  "minecraft:item": {
    "description": {
      "identifier": "__IDENT__",
      "menu_category": { "category": "equipment" }
    },
    "components": {}
  }
}
```

- entity 额外带空 `component_groups` / `events`。
- block 额外带 `register_to_creative_menu`。

### 10.7.3 取用方式

| 场景 | 接口 |
|---|---|
| 列出可用版本 | `GET /api/project/<pid>/objects/kinds` 的 `templates` |
| 查看/复制模板代码 | `GET /api/project/<pid>/objects/template?kind=&fv=` |
| 创建时实际使用 | `templates.materialize(kind, fv, identifier)`，把 `__IDENT__` 替换为真实 identifier |

> 模板库**不参与**组件查询、不参与示例合并；它只是新建对象的起手文件。

---

## 11. 已知限制

1. **`default` / `example` 不随多值更新**：临时库只把多值并入 `examples`，`default` 与 `example` 始终是首个取值。需要代表性取值时读 `examples`。
2. **`value_type` 是推断值**：来自实际数据，非官方 schema；`enum` 不会自动识别；复杂对象只能给出类型名，无结构约束。
3. **超长值退化为摘要**：> 8000 字符的值不是可回填的真实数据（第 4.2 节）。
4. **去重只看值**：临时库同一值来自多个对象时只保留首个 `origin`，无法追溯全部来源。
5. **正式库 `project` 示例被标为 `local`**：`list_examples` 的三档来源映射所致，历史来源无法在 UI 区分。
6. **临时库只覆盖主文件**：`build_temp` 只遍历 `primary`。资源侧注册文件（`resource_item`）、客户端实体（`client_entity`）、attachable 等引用文件里的组件**不入桶**，编辑这些文件时示例下拉可能为空。
7. **正式库种子数据的边界**：`db/official/` 已按第 10 节填充 11 个桶，但 item 1.16.0 缺官方默认值、组件清单也不完整（官方页面该列整列为空，且仅收录 20 个组件，见 10.1 / 10.3）；未收录组件仍需人工补充。
8. **正式库纳入版本管理**：`.gitignore` 当前只忽略 `workspaces/` 与 `output/`，`db/official/` 会进 Git。这是刻意设计（跨项目共享需要持久化），但需注意不要把测试数据提交进去。

---

## 12. 变更记录

| 轮次 | 变更 |
|---|---|
| 第四轮 | 新增 `examples` 数组与 `project` / `local` / `official` 三档来源 |
| 第五轮 | `build_entry` 改用 `clip_value`，`default` / `example` / `examples[].value` 存真实值 |
| 第六轮 | 临时库同桶多值合并（`add_project_value` / `add_project_example`，`MAX_EXAMPLES = 60`）；`origin` 记录来源对象；`list_examples` 透传 `label` / `origin` / `added`；`promote` 不再覆盖原 `origin` |
| 第七轮 | 正式库首版填充：entity / item / block x 4 个 format_version，共 11 桶 1423 条；`docs/` 改为按组件跨版本聚合；新增第 10 节记录数据源、版本映射、构建脚本与人工确认记录 |
| 第八轮 | 新增空模板库 `templates/<kind>/<fv>.json`（第 10.7 节）；关联槽位体系上线，槽位定义见 [PROGRESS.md](PROGRESS.md) 12.11 |
