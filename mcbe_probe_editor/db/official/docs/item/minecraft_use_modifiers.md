# `minecraft:use_modifiers`

- 出现版本：`1.21.0`、`1.26.0`
- 核实状态：**已核实**

## 说明

Modifies use behavior, including how long the item takes to use and the player's movement speed.

## `1.21.0`

- 来源：bedrock-samples json_schemas/server/item/1.20.50（最近可得）
- 核实状态：已核实

取值：

```json
{
  "emit_vibrations": true,
  "use_duration": 0
}
```

## `1.26.0`

- 来源：bedrock-samples json_schemas/server/item/1.26.30
- 核实状态：已核实

取值：

```json
{
  "emit_vibrations": true,
  "start_using": "if_first",
  "use_duration": 0
}
```
