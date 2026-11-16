# `minecraft:behavior.random_look_around_and_sit`

- 出现版本：`1.16.0`、`1.21.0`、`1.26.0`
- 核实状态：**已核实**

## 说明

Allows the mob to randomly sit and look around for a duration. Note: Must have a sitting animation set up to use this.

## `1.16.0`

- 来源：bedrock.dev 官方文档（1.16.0）
- 核实状态：已核实

取值：

```json
{
  "max_look_count": 2,
  "max_look_time": 40,
  "min_look_count": 1,
  "min_look_time": 20,
  "probability": 0.02
}
```

## `1.21.0`

- 来源：bedrock.dev 官方文档（1.21.0）
- 核实状态：已核实

取值：

```json
{
  "continue_if_leashed": false,
  "continue_sitting_on_reload": false,
  "max_angle_of_view_horizontal": 30.0,
  "max_look_count": 2,
  "max_look_time": 40,
  "min_angle_of_view_horizontal": -30.0,
  "min_look_count": 1,
  "min_look_time": 20,
  "probability": 0.02,
  "random_look_around_cooldown": 0
}
```

## `1.26.0`

- 来源：bedrock.dev 官方文档（1.26.0）
- 核实状态：已核实

取值：

```json
{
  "continue_if_leashed": false,
  "continue_sitting_on_reload": false,
  "max_angle_of_view_horizontal": 30.0,
  "max_look_count": 2,
  "max_look_time": 40,
  "min_angle_of_view_horizontal": -30.0,
  "min_look_count": 1,
  "min_look_time": 20,
  "probability": 0.02,
  "random_look_around_cooldown": 0
}
```
