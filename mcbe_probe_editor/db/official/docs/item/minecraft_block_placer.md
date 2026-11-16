# `minecraft:block_placer`

- 出现版本：`1.16.0`、`1.21.0`、`1.26.0`
- 核实状态：**已核实**

## 说明

Planter item component. planter items are items that can be planted.

## `1.16.0`

- 来源：bedrock.dev 官方文档（1.16.0）
- 核实状态：已核实

字段结构（官方文档未提供默认值）：
- `block`
- `use_on`

取值：

```json
{}
```

## `1.21.0`

- 来源：bedrock-samples json_schemas/server/item/1.20.50（最近可得）
- 核实状态：已核实

取值：

```json
{
  "use_on": []
}
```

## `1.26.0`

- 来源：bedrock-samples json_schemas/server/item/1.26.30
- 核实状态：已核实

取值：

```json
{
  "aligned_placement": false,
  "replace_block_item": false,
  "use_on": []
}
```
