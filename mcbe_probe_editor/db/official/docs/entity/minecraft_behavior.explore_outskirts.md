# `minecraft:behavior.explore_outskirts`

- 出现版本：`1.12.0`、`1.16.0`、`1.21.0`、`1.26.0`
- 核实状态：**已核实**

## 说明

allows a mob to explore the outskirts of a village

## `1.12.0`

- 来源：bedrock.dev 官方文档（1.12.0）
- 核实状态：已核实

取值：

```json
{
  "wait_time": 0,
  "explore_dist": 5.0,
  "speed_multiplier": 1.0
}
```

## `1.16.0`

- 来源：bedrock.dev 官方文档（1.16.0）
- 核实状态：已核实

取值：

```json
{
  "explore_dist": 5.0,
  "speed_multiplier": 1.0,
  "wait_time": 0
}
```

## `1.21.0`

- 来源：bedrock.dev 官方文档（1.21.0）
- 核实状态：已核实

取值：

```json
{
  "dist_from_boundary": [
    5,
    0,
    5
  ],
  "explore_dist": 5.0,
  "max_travel_time": 60.0,
  "max_wait_time": 0.0,
  "min_dist_from_target": 2.2,
  "min_perimeter": 1.0,
  "min_wait_time": 3.0,
  "next_xz": 5,
  "next_y": 3,
  "speed_multiplier": 1.0,
  "timer_ratio": 2.0
}
```

## `1.26.0`

- 来源：bedrock.dev 官方文档（1.26.0）
- 核实状态：已核实

取值：

```json
{
  "dist_from_boundary": [
    5,
    0,
    5
  ],
  "explore_dist": 5.0,
  "max_travel_time": 60.0,
  "max_wait_time": 0.0,
  "min_dist_from_target": 2.2,
  "min_perimeter": 1.0,
  "min_wait_time": 3.0,
  "next_xz": 5,
  "next_y": 3,
  "speed_multiplier": 1.0,
  "timer_ratio": 2.0
}
```
