# -*- coding: utf-8 -*-
"""把第四轮改动与待办事项写入 PROGRESS.md / README.md。"""
import io

PROGRESS = r"D:/git/MCBE-Probe-Editor/PROGRESS.md"
README = r"D:/git/MCBE-Probe-Editor/README.md"

# ------------------------------------------------------------ PROGRESS.md
with io.open(PROGRESS, "r", encoding="utf-8") as f:
    p = f.read()

ok, fail = [], []


def rep(old, new, label):
    global p
    if old in p:
        p = p.replace(old, new, 1)
        ok.append(label)
    else:
        fail.append(label)


# 1. 头部时间戳
rep("最后更新：本轮开发完成，等待正式测试。",
    "最后更新：第四轮改动完成（示例库 / scope 编辑 / 新建对象 / 包信息 / 多语言 / output 目录）。"
    "功能已实现并通过脚本自检，**尚未完成人工界面测试**。",
    "头部时间戳")

# 2. 总体状态表：补齐缺失行 + 修正路由数
rep("| 工程配套 | \u2705 完成 | requirements / README / run.py / .gitignore |",
    "| 工程配套 | \u2705 完成 | requirements / README / run.py / .gitignore |\n"
    "| 多语言 UI | \u2705 完成 | zh / en 各 242 键、双向对齐，顶栏切换 |\n"
    "| 示例库 | \u2705 完成 | project / local / official 三类示例，下拉选择 + 填入 + 复制 + 存为示例 |\n"
    "| scope 编辑 | \u2705 完成 | components / component_groups.\u7ec4 / events 三区独立增删改 |\n"
    "| 新建对象 | \u2705 完成 | item / entity / block，按标准写法生成主文件与配套文件 |\n"
    "| 包信息编辑 | \u2705 完成 | manifest 独立页面（双包分栏 / 校验 / 模板），不进对象索引 |\n"
    "| 导出目录 | \u2705 完成 | 产物统一落到工程根 output/\u9879\u76ee\u540d/ |",
    "总体状态表")

rep("**路由总数：49**。所有页面与 API 已通过回归测试（详见第八节）。",
    "**路由总数：58**。页面与 API 已通过脚本级自检（fails: 0），"
    "**界面交互仍待人工验证**（见第十二节待办）。",
    "路由总数")

# 3. 目录结构：补新增模块
rep("│   │   └── unbound.py         未绑定项分页视图",
    "│   │   ├── unbound.py         未绑定项分页视图\n"
    "│   │   ├── manifest.py        包信息（manifest）编辑\n"
    "│   │   ├── objects.py         新建对象\n"
    "│   │   └── i18n.py            界面语言字典接口",
    "routes 结构")

rep("│   │   ├── texture.py         贴图 alpha 规则 / 像素画\n"
    "│   │   └── structure.py       结构 NBT 解析与降版本",
    "│   │   ├── texture.py         贴图 alpha 规则 / 像素画\n"
    "│   │   ├── structure.py       结构 NBT 解析与降版本\n"
    "│   │   ├── manifest.py        manifest 校验 / 模板 / 读写\n"
    "│   │   ├── objects.py         新建对象（标准写法生成）\n"
    "│   │   └── i18n.py            语言字典（zh / en）",
    "services 结构")

with io.open(PROGRESS, "w", encoding="utf-8") as f:
    f.write(p)

# 4. 追加第四轮章节 + 待办章节
TAIL = """

---

## 十二、第四轮改动（近期）

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
| `component_groups.<组名>` | `…component_groups.<组>.components` |
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

---

## 十三、待办事项

### 13.1 必做（阻塞交付）

1. **界面人工测试未完成**：本轮改动均为脚本级自检，需逐页实际点击验证。
   重点：包信息页、新建对象、scope 切换、示例下拉与复制、导出落点提示。
2. **后端需重启**：新增 `services/{manifest,objects,i18n}.py`，
   旧进程不会自动加载。
3. **浏览器强刷**：`Ctrl+F5` 清 `app.js` 缓存（此前出现过旧脚本导致上传失败）。

### 13.2 功能待完善

4. **正式库为空**：`db/official/` 无种子数据，示例只有 `project` 一种来源；
   `official` 类示例需人工补充文档后才有。
5. **组件 `description` 为空**：探测只推断 `value_type` / `default` / `example`，
   说明文字需经「文档核实」流程补全。
6. **`value_type` 为推断值**：`enum` 无法自动识别，复杂对象仅给 key 摘要。
7. **像素画不支持多帧 / 动画贴图**：仅单帧 PNG。
8. **模型仍依赖 Blockbench 外链**：本地只改写 geometry 命名空间，不渲染。
9. **结构降版本缺 fv2 样本**：当前 25 个结构均为 fv1，真实降级路径未实测。
10. **未绑定项无跳转**：列表项不能跳到对应对象或文件。
11. **语言键无批量操作**：不能一次为多个 locale 新增键。
12. **i18n 需同步维护**：新增 UI 文案时必须同时补 zh / en 两个字典。

### 13.3 工程清理

13. `tools/` 下一次性补丁脚本已删除，保留：
    `probe.py`、`e2e_test.py`、`page_test.py`、`structure_test.py`、
    `db_test.py`、`test_upload.py`、`verify_r4a.py`、`verify_r4b.py`、
    `verify_r4c.py`、`update_progress.py`。
14. `mcbe_probe_editor/workspaces/` 下可能有 `verify_*` 测试残留，可删。
15. `output/` 下可能有测试导出产物，可删。
16. 根目录若残留 `_*.txt` 报告文件，可删。

### 13.4 风险提示

- `copy=False` 的工作区直接写**源模组目录**，正式使用请保持默认 `copy=True`。
- 组件「提升到正式库」与「文档核实」会**永久写入**本地库，
  测试时注意先确认项目是否正确。
- 特殊文件（`tick.json`、`lines/` 等）只能在文件浏览页查看，
  刻意不提供编辑入口，避免误改。
"""

p2 = p.rstrip() + TAIL
with io.open(PROGRESS, "w", encoding="utf-8") as f:
    f.write(p2)

# ------------------------------------------------------------ README.md
with io.open(README, "r", encoding="utf-8") as f:
    r = f.read()

rok, rfail = [], []


def rrep(old, new, label):
    global r
    if old in r:
        r = r.replace(old, new, 1)
        rok.append(label)
    else:
        rfail.append(label)


rrep("| 文件浏览 | 查看全部文件，特殊文件（`tick.json`、`lines/` 等）仅在此可见 |",
     "| 文件浏览 | 查看全部文件，特殊文件（`tick.json`、`lines/` 等）仅在此可见 |\n"
     "| 示例库 | 组件示例下拉选择 / 填入 / 复制 / 存为示例；本地库跨项目共享 |\n"
     "| 包信息 | manifest 独立编辑页（双包分栏、校验、模板），不进对象索引 |\n"
     "| 新建对象 | item / entity / block，按标准写法生成主文件与配套文件 |\n"
     "| 多语言 | 中文 / English，顶栏切换 |",
     "README 功能表")

rrep("## 工作区结构",
     "## 输出目录\n\n"
     "导出产物统一落在**工程根** `output/<project_id>/`：\n\n"
     "```\n"
     "output/<project_id>/\n"
     "├── <name>_<ts>.mcaddon\n"
     "├── <name>_<ts>.zip\n"
     "└── <name>_changes_<ts>/       仅改动文件 + _changes.json\n"
     "```\n\n"
     "## 工作区结构",
     "README 输出目录")

with io.open(README, "w", encoding="utf-8") as f:
    f.write(r)

print("PROGRESS 修改成功:", ok)
print("PROGRESS 未匹配:", fail)
print("README  修改成功:", rok)
print("README  未匹配:", rfail)
print("PROGRESS 新长度:", len(p2))
print("README   新长度:", len(r))