# `minecraft:leashable`

- 出现版本：`1.12.0`、`1.16.0`、`1.21.0`、`1.26.0`
- 核实状态：**已核实**

## 说明

Allows this entity to be leashed and Defines the conditions and events for this entity when is leashed.

## `1.12.0`

- 来源：bedrock.dev 官方文档（1.12.0）
- 核实状态：已核实

取值：

```json
{
  "soft_distance": 4.0,
  "hard_distance": 6.0,
  "max_distance": 10.0,
  "can_be_stolen": false
}
```

## `1.16.0`

- 来源：bedrock.dev 官方文档（1.16.0）
- 核实状态：已核实

取值：

```json
{
  "can_be_stolen": false,
  "hard_distance": 6,
  "max_distance": 10,
  "soft_distance": 4
}
```

## `1.21.0`

- 来源：bedrock.dev 官方文档（1.21.0）
- 核实状态：已核实

取值：

```json
{
  "can_be_cut": true,
  "can_be_stolen": true,
  "on_unleash_interact_only": false,
  "hard_distance": 7,
  "max_distance": 12,
  "rotation_adjustment": 0,
  "soft_distance": 4,
  "spring_type": "dampened"
}
```

## `1.26.0`

- 来源：bedrock.dev 官方文档（1.26.0）
- 核实状态：已核实

取值：

```json
{
  "can_be_cut": true,
  "can_be_stolen": true,
  "on_unleash_interact_only": false,
  "hard_distance": 7,
  "max_distance": 12,
  "rotation_adjustment": 0,
  "soft_distance": 4,
  "spring_type": "dampened"
}
```
