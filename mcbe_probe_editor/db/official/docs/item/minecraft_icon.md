# `minecraft:icon`

- 出现版本：`1.16.0`、`1.21.0`、`1.26.0`
- 核实状态：**已核实**

## 说明

The icon item componenent determines the icon to represent the item in the UI and elsewhere.

## `1.16.0`

- 来源：bedrock.dev 官方文档（1.16.0）
- 核实状态：已核实

字段结构（官方文档未提供默认值）：
- `frame`
- `legacy_id`
- `texture`

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
  "texture": ""
}
```

## `1.26.0`

- 来源：bedrock-samples json_schemas/server/item/1.26.30
- 核实状态：已核实

取值：

```json
{
  "textures": {}
}
```
