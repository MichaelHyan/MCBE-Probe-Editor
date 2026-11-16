# `minecraft:behavior.circle_around_anchor`

- 出现版本：`1.12.0`、`1.21.0`、`1.26.0`
- 核实状态：**已核实**

## 说明

Allows the mob to move in a circle around a point or a target.

## `1.12.0`

- 来源：bedrock.dev 官方文档（1.12.0）
- 核实状态：已核实

取值：

```json
{
  "speed_multiplier": 1.0,
  "radius_range": [
    5.0,
    15.0
  ],
  "radius_change_chance": 250,
  "height_above_target_range": [
    0.0,
    0.0
  ],
  "height_offset_range": [
    0.0,
    0.0
  ],
  "height_change_chance": 350,
  "goal_radius": 0.5
}
```

## `1.21.0`

- 来源：bedrock.dev 官方文档（1.21.0）
- 核实状态：已核实

取值：

```json
{
  "angle_change": 15.0,
  "goal_radius": 0.5,
  "height_above_target_range": [
    0,
    0
  ],
  "height_adjustment_chance": 0.002857,
  "height_offset_range": [
    0,
    0
  ],
  "radius_adjustment_chance": 0.004,
  "radius_change": 1.0,
  "radius_range": [
    5,
    15
  ],
  "speed_multiplier": 1.0
}
```

## `1.26.0`

- 来源：bedrock.dev 官方文档（1.26.0）
- 核实状态：已核实

取值：

```json
{
  "angle_change": 15.0,
  "goal_radius": 0.5,
  "height_above_target_range": [
    0,
    0
  ],
  "height_adjustment_chance": 0.002857,
  "height_offset_range": [
    0,
    0
  ],
  "radius_adjustment_chance": 0.004,
  "radius_change": 1.0,
  "radius_range": [
    5,
    15
  ],
  "speed_multiplier": 1.0
}
```
