# `minecraft:food`

- 出现版本：`1.16.0`、`1.21.0`、`1.26.0`
- 核实状态：**已核实**

## 说明

When an item has a food component, it becomes edible to the player.

## `1.16.0`

- 来源：bedrock.dev 官方文档（1.16.0）
- 核实状态：已核实

字段结构（官方文档未提供默认值）：
- `can_always_eat`
- `nutrition`
- `on_consume`
- `saturation_modifier`
- `using_converts_to`

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
  "can_always_eat": false,
  "nutrition": 0,
  "saturation_modifier": 0.6000000238418579,
  "using_converts_to": {}
}
```

## `1.26.0`

- 来源：bedrock-samples json_schemas/server/item/1.26.30
- 核实状态：已核实

取值：

```json
{
  "can_always_eat": false,
  "nutrition": 0,
  "saturation_modifier": 0.6000000238418579,
  "using_converts_to": {}
}
```
