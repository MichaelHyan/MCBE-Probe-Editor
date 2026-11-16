# `minecraft:entity_sensor`

- 出现版本：`1.16.0`、`1.21.0`、`1.26.0`
- 核实状态：**已核实**

## 说明

A component that fires an event when a set of conditions are met by other entities within the defined range.

## `1.16.0`

- 来源：bedrock.dev 官方文档（1.16.0）
- 核实状态：已核实

取值：

```json
{
  "maximum_count": -1,
  "minimum_count": 1,
  "relative_range": true,
  "require_all": false,
  "sensor_range": 10
}
```

## `1.21.0`

- 来源：bedrock.dev 官方文档（1.21.0）
- 核实状态：已核实

取值：

```json
{
  "find_players_only": false,
  "relative_range": true,
  "cooldown": -1,
  "maximum_count": -1,
  "minimum_count": 1,
  "range": [
    10,
    10
  ],
  "require_all": false,
  "y_offset": 0
}
```

## `1.26.0`

- 来源：bedrock.dev 官方文档（1.26.0）
- 核实状态：已核实

取值：

```json
{
  "find_players_only": false,
  "relative_range": true,
  "cooldown": -1,
  "maximum_count": -1,
  "minimum_count": 1,
  "range": [
    10,
    10
  ],
  "require_all": false,
  "y_offset": 0
}
```
