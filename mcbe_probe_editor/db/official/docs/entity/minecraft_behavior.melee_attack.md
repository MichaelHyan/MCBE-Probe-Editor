# `minecraft:behavior.melee_attack`

- 出现版本：`1.12.0`、`1.21.0`、`1.26.0`
- 核实状态：**已核实**

## 说明

Allows the mob to use close combat melee attacks.

## `1.12.0`

- 来源：bedrock.dev 官方文档（1.12.0）
- 核实状态：已核实

取值：

```json
{
  "melee_fov": 90.0,
  "speed_multiplier": 1.0,
  "track_target": false,
  "random_stop_interval": 0,
  "reach_multiplier": 2.0,
  "attack_once": false,
  "require_complete_path": false
}
```

## `1.21.0`

- 来源：bedrock.dev 官方文档（1.21.0）
- 核实状态：已核实

取值：

```json
{
  "attack_once": false,
  "can_spread_on_fire": false,
  "cooldown_time": 1,
  "inner_boundary_time_increase": 0.25,
  "max_path_time": 0.55,
  "melee_fov": 90,
  "min_path_time": 0.2,
  "outer_boundary_time_increase": 0.5,
  "path_fail_time_increase": 0.75,
  "path_inner_boundary": 16,
  "path_outer_boundary": 32,
  "random_stop_interval": 0,
  "reach_multiplier": 2,
  "require_complete_path": false,
  "speed_multiplier": 1,
  "track_target": false,
  "x_max_rotation": 30,
  "y_max_head_rotation": 30
}
```

## `1.26.0`

- 来源：bedrock.dev 官方文档（1.26.0）
- 核实状态：已核实

取值：

```json
{
  "attack_once": false,
  "can_spread_on_fire": false,
  "cooldown_time": 1,
  "inner_boundary_time_increase": 0.25,
  "max_path_time": 0.55,
  "melee_fov": 90,
  "min_path_time": 0.2,
  "outer_boundary_time_increase": 0.5,
  "path_fail_time_increase": 0.75,
  "path_inner_boundary": 16,
  "path_outer_boundary": 32,
  "random_stop_interval": 0,
  "reach_multiplier": 2,
  "require_complete_path": false,
  "speed_multiplier": 1,
  "track_target": false,
  "x_max_rotation": 30,
  "y_max_head_rotation": 30
}
```
