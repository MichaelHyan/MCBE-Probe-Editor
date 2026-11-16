# `minecraft:variable_max_auto_step`

- 出现版本：`1.21.0`、`1.26.0`
- 核实状态：**已核实**

## 说明

Entities with this component will have a maximum auto step height that is different depending on whether they are on a block that prevents jumping. Incompatible with "runtime_identifier": "minecraft:horse".

## `1.21.0`

- 来源：bedrock.dev 官方文档（1.21.0）
- 核实状态：已核实

取值：

```json
{
  "base_value": 0.5625,
  "controlled_value": 0.5625,
  "jump_prevented_value": 0.5625
}
```

## `1.26.0`

- 来源：bedrock.dev 官方文档（1.26.0）
- 核实状态：已核实

取值：

```json
{
  "base_value": 0.5625,
  "controlled_value": 0.5625,
  "jump_prevented_value": 0.5625
}
```
