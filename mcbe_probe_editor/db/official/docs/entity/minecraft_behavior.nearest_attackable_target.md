# `minecraft:behavior.nearest_attackable_target`

- 出现版本：`1.12.0`、`1.16.0`、`1.21.0`、`1.26.0`
- 核实状态：**已核实**

## 说明

Allows the mob to check for and pursue the nearest valid target.

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

## `1.16.0`

- 来源：bedrock.dev 官方文档（1.16.0）
- 核实状态：已核实

取值：

```json
{
  "attack_interval": 0,
  "attack_interval_min": 0,
  "attack_owner": false,
  "max_dist": 16,
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
  "attack_interval": [
    0,
    0
  ],
  "attack_owner": false,
  "must_reach": false,
  "must_see": false,
  "must_see_forget_duration": 3.0,
  "persist_time": 0.0,
  "reselect_targets": false,
  "scan_interval": 10,
  "set_persistent": false,
  "target_acquisition_probability": 1.0,
  "target_invisible_multiplier": 0.7,
  "target_search_height": -1.0,
  "target_sneak_visibility_multiplier": 0.8,
  "within_radius": 0.0
}
```

## `1.26.0`

- 来源：bedrock.dev 官方文档（1.26.0）
- 核实状态：已核实

取值：

```json
{
  "attack_interval": [
    0,
    0
  ],
  "attack_owner": false,
  "must_reach": false,
  "must_see": false,
  "must_see_forget_duration": 3.0,
  "persist_time": 0.0,
  "reselect_targets": false,
  "scan_interval": 10,
  "set_persistent": false,
  "target_acquisition_probability": 1.0,
  "target_invisible_multiplier": 0.7,
  "target_search_height": -1.0,
  "target_sneak_visibility_multiplier": 0.8,
  "within_radius": 0.0
}
```
