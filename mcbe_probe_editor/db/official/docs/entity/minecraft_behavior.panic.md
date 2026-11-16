# `minecraft:behavior.panic`

- 出现版本：`1.12.0`、`1.16.0`、`1.21.0`、`1.26.0`
- 核实状态：**已核实**

## 说明

Allows the mob to enter the panic state, which makes it run around and away from the damage source that made it enter this state.

## `1.12.0`

- 来源：bedrock.dev 官方文档（1.12.0）
- 核实状态：已核实

取值：

```json
{
  "speed_multiplier": 1.0,
  "ignore_mob_damage": false,
  "prefer_water": false,
  "force": false
}
```

## `1.16.0`

- 来源：bedrock.dev 官方文档（1.16.0）
- 核实状态：已核实

取值：

```json
{
  "damage_sources": "all",
  "force": false,
  "ignore_mob_damage": false,
  "prefer_water": false,
  "speed_multiplier": 1.0
}
```

## `1.21.0`

- 来源：bedrock.dev 官方文档（1.21.0）
- 核实状态：已核实

取值：

```json
{
  "force": false,
  "ignore_mob_damage": false,
  "prefer_water": false,
  "speed_multiplier": 1.0
}
```

## `1.26.0`

- 来源：bedrock.dev 官方文档（1.26.0）
- 核实状态：已核实

取值：

```json
{
  "force": false,
  "ignore_mob_damage": false,
  "prefer_water": false,
  "speed_multiplier": 1.0
}
```
