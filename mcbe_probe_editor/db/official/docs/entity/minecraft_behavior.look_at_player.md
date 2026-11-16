# `minecraft:behavior.look_at_player`

- 出现版本：`1.12.0`、`1.16.0`、`1.21.0`、`1.26.0`
- 核实状态：**已核实**

## 说明

Allows the mob to look at the player when the player is nearby.

## `1.12.0`

- 来源：bedrock.dev 官方文档（1.12.0）
- 核实状态：已核实

取值：

```json
{
  "look_distance": 8.0,
  "probability": 0.02,
  "look_time": [
    2,
    4
  ],
  "angle_of_view_vertical": 360,
  "angle_of_view_horizontal": 360
}
```

## `1.16.0`

- 来源：bedrock.dev 官方文档（1.16.0）
- 核实状态：已核实

取值：

```json
{
  "angle_of_view_horizontal": 360,
  "angle_of_view_vertical": 360,
  "look_distance": 8.0,
  "look_time": [
    2,
    4
  ],
  "probability": 0.02
}
```

## `1.21.0`

- 来源：bedrock.dev 官方文档（1.21.0）
- 核实状态：已核实

取值：

```json
{
  "angle_of_view_horizontal": 360,
  "angle_of_view_vertical": 360,
  "look_distance": 8.0,
  "look_time": [
    2,
    4
  ],
  "probability": 0.02
}
```

## `1.26.0`

- 来源：人工确认；取自项目实际值（1.26.0）
- 核实状态：已核实

取值：

```json
{
  "look_time": {
    "min": 1,
    "max": 2
  },
  "look_distance": 6,
  "priority": 9
}
```
