# `minecraft:behavior.float_wander`

- 出现版本：`1.12.0`、`1.16.0`、`1.21.0`、`1.26.0`
- 核实状态：**已核实**

## 说明

Allows the mob to float around like the Ghast.

## `1.12.0`

- 来源：bedrock.dev 官方文档（1.12.0）
- 核实状态：已核实

取值：

```json
{
  "xz_dist": 10,
  "y_dist": 7,
  "y_offset": 0.0,
  "must_reach": false,
  "random_reselect": false,
  "float_duration": [
    0.0,
    0.0
  ]
}
```

## `1.16.0`

- 来源：bedrock.dev 官方文档（1.16.0）
- 核实状态：已核实

取值：

```json
{
  "float_duration": [
    0.0,
    0.0
  ],
  "must_reach": false,
  "random_reselect": false,
  "xz_dist": 10,
  "y_dist": 7,
  "y_offset": 0.0
}
```

## `1.21.0`

- 来源：bedrock.dev 官方文档（1.21.0）
- 核实状态：已核实

取值：

```json
{
  "additional_collision_buffer": false,
  "allow_navigating_through_liquids": false,
  "float_duration": [
    0.0,
    0.0
  ],
  "float_wander_has_move_control": true,
  "must_reach": false,
  "navigate_around_surface": false,
  "random_reselect": false,
  "surface_xz_dist": 0,
  "surface_y_dist": 0,
  "use_home_position_restriction": true,
  "xz_dist": 10,
  "y_dist": 7,
  "y_offset": 0.0
}
```

## `1.26.0`

- 来源：bedrock.dev 官方文档（1.26.0）
- 核实状态：已核实

取值：

```json
{
  "additional_collision_buffer": false,
  "allow_navigating_through_liquids": false,
  "float_duration": [
    0.0,
    0.0
  ],
  "float_wander_has_move_control": true,
  "must_reach": false,
  "navigate_around_surface": false,
  "random_reselect": false,
  "surface_xz_dist": 0,
  "surface_y_dist": 0,
  "use_home_position_restriction": true,
  "xz_dist": 10,
  "y_dist": 7,
  "y_offset": 0.0
}
```
