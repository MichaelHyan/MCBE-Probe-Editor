# `minecraft:behavior.avoid_mob_type`

- 出现版本：`1.12.0`、`1.21.0`、`1.26.0`
- 核实状态：**已核实**

## 说明

Allows this entity to avoid certain mob types.

## `1.12.0`

- 来源：bedrock.dev 官方文档（1.12.0）
- 核实状态：已核实

取值：

```json
{
  "max_dist": 16,
  "walk_speed_multiplier": 1.0,
  "sprint_speed_multiplier": 1.0,
  "must_see": false,
  "must_see_forget_duration": 3.0
}
```

## `1.21.0`

- 来源：bedrock.dev 官方文档（1.21.0）
- 核实状态：已核实

取值：

```json
{
  "avoid_target_xz": 16,
  "avoid_target_y": 7,
  "ignore_visibility": false,
  "max_dist": 3.0,
  "max_flee": 10.0,
  "probability_per_strength": 1.0,
  "remove_target": false,
  "sound_interval": [
    3,
    8
  ],
  "sprint_distance": 7.0,
  "sprint_speed_multiplier": 1.0,
  "walk_speed_multiplier": 1.0
}
```

## `1.26.0`

- 来源：bedrock.dev 官方文档（1.26.0）
- 核实状态：已核实

取值：

```json
{
  "avoid_target_xz": 16,
  "avoid_target_y": 7,
  "ignore_visibility": false,
  "max_dist": 3.0,
  "max_flee": 10.0,
  "probability_per_strength": 1.0,
  "remove_target": false,
  "sound_interval": [
    3,
    8
  ],
  "sprint_distance": 7.0,
  "sprint_speed_multiplier": 1.0,
  "walk_speed_multiplier": 1.0
}
```
