# `minecraft:teleport`

- 出现版本：`1.12.0`、`1.16.0`、`1.21.0`、`1.26.0`
- 核实状态：**已核实**

## 说明

Defines an entity's teleporting behavior.

## `1.12.0`

- 来源：bedrock.dev 官方文档（1.12.0）
- 核实状态：已核实

取值：

```json
{
  "randomTeleports": true,
  "minRandomTeleportTime": 0.0,
  "maxRandomTeleportTime": 20.0,
  "randomTeleportCube": [
    32.0,
    16.0,
    32.0
  ],
  "targetDistance": 16.0,
  "target_teleport_chance": 1.0,
  "lightTeleportChance": 0.01,
  "darkTeleportChance": 0.01
}
```

## `1.16.0`

- 来源：bedrock.dev 官方文档（1.16.0）
- 核实状态：已核实

取值：

```json
{
  "dark_teleport_chance": 0.01,
  "light_teleport_chance": 0.01,
  "max_random_teleport_time": 20,
  "min_random_teleport_time": 0,
  "random_teleport_cube": [
    32,
    16,
    32
  ],
  "random_teleports": true,
  "target_distance": 16,
  "target_teleport_chance": 1
}
```

## `1.21.0`

- 来源：bedrock.dev 官方文档（1.21.0）
- 核实状态：已核实

取值：

```json
{
  "dark_teleport_chance": 0.01,
  "light_teleport_chance": 0.01,
  "max_random_teleport_time": 20,
  "min_random_teleport_time": 0,
  "random_teleport_cube": [
    32,
    16,
    32
  ],
  "random_teleports": true,
  "target_distance": 16,
  "target_teleport_chance": 1
}
```

## `1.26.0`

- 来源：bedrock.dev 官方文档（1.26.0）
- 核实状态：已核实

取值：

```json
{
  "dark_teleport_chance": 0.01,
  "light_teleport_chance": 0.01,
  "max_random_teleport_time": 20,
  "min_random_teleport_time": 0,
  "random_teleport_cube": [
    32,
    16,
    32
  ],
  "random_teleports": true,
  "target_distance": 16,
  "target_teleport_chance": 1,
  "teleports_on_projectile_hit": false
}
```
