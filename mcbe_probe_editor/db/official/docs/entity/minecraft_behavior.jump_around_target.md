# `minecraft:behavior.jump_around_target`

- 出现版本：`1.21.0`、`1.26.0`
- 核实状态：**已核实**

## 说明

Allows an entity to jump around a target.

## `1.21.0`

- 来源：bedrock.dev 官方文档（1.21.0）
- 核实状态：已核实

取值：

```json
{
  "check_collision": false,
  "entity_bounding_box_scale": 0.7,
  "jump_angles": [
    40.0,
    55.0,
    60.0,
    75.0,
    80.0
  ],
  "jump_cooldown_duration": 0.5,
  "jump_cooldown_when_hurt_duration": 0.1,
  "landing_distance_from_target": [
    4.0,
    8.0
  ],
  "landing_position_spread_degrees": 90,
  "last_hurt_duration": 2.0,
  "line_of_sight_obstruction_height_ignore": 4,
  "max_jump_velocity": 1.4,
  "prepare_jump_duration": 0.5,
  "required_vertical_space": 4,
  "snap_to_surface_block_range": 10,
  "valid_distance_to_target": [
    4.0,
    20.0
  ]
}
```

## `1.26.0`

- 来源：bedrock.dev 官方文档（1.26.0）
- 核实状态：已核实

取值：

```json
{
  "check_collision": false,
  "entity_bounding_box_scale": 0.7,
  "jump_angles": [
    40.0,
    55.0,
    60.0,
    75.0,
    80.0
  ],
  "jump_cooldown_duration": 0.5,
  "jump_cooldown_when_hurt_duration": 0.1,
  "landing_distance_from_target": [
    4.0,
    8.0
  ],
  "landing_position_spread_degrees": 90,
  "last_hurt_duration": 2.0,
  "line_of_sight_obstruction_height_ignore": 4,
  "max_jump_velocity": 1.4,
  "prepare_jump_duration": 0.5,
  "required_vertical_space": 4,
  "snap_to_surface_block_range": 10,
  "valid_distance_to_target": [
    4.0,
    20.0
  ]
}
```
