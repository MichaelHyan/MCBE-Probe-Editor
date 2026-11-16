# `minecraft:behavior.lay_egg`

- 出现版本：`1.12.0`、`1.16.0`、`1.21.0`、`1.26.0`
- 核实状态：**已核实**

## 说明

Allows the mob to lay an egg block on a sand block if the mob is pregnant.

## `1.12.0`

- 来源：bedrock.dev 官方文档（1.12.0）
- 核实状态：已核实

取值：

```json
{
  "speed_multiplier": 1.0,
  "search_range": 0,
  "search_height": 1,
  "search_count": 10,
  "goal_radius": 0.5
}
```

## `1.16.0`

- 来源：bedrock.dev 官方文档（1.16.0）
- 核实状态：已核实

取值：

```json
{
  "goal_radius": 0.5,
  "search_height": 1,
  "search_range": 0,
  "speed_multiplier": 1.0
}
```

## `1.21.0`

- 来源：bedrock.dev 官方文档（1.21.0）
- 核实状态：已核实

取值：

```json
{
  "allow_laying_from_below": false,
  "egg_type": "minecraft:turtle_egg",
  "goal_radius": 0.5,
  "lay_egg_sound": "lay_egg",
  "lay_seconds": 10.0,
  "search_height": 1,
  "search_range": 0,
  "speed_multiplier": 1.0,
  "use_default_animation": true
}
```

## `1.26.0`

- 来源：bedrock.dev 官方文档（1.26.0）
- 核实状态：已核实

取值：

```json
{
  "allow_laying_from_below": false,
  "egg_type": "minecraft:turtle_egg",
  "goal_radius": 0.5,
  "lay_egg_sound": "lay_egg",
  "lay_seconds": 10.0,
  "search_height": 1,
  "search_range": 0,
  "speed_multiplier": 1.0,
  "use_default_animation": true
}
```
