# `minecraft:behavior.summon_entity`

- 出现版本：`1.12.0`、`1.16.0`、`1.21.0`、`1.26.0`
- 核实状态：**已核实**

## 说明

Allows the mob to attack the player by summoning other entities.

## `1.12.0`

- 来源：bedrock.dev 官方文档（1.12.0）
- 核实状态：已核实

取值：

```json
{
  "min_activation_range": 1.0,
  "max_activation_range": -1.0,
  "cooldown_time": 0.0,
  "weight": 0.0,
  "do_casting": true,
  "particle_color": 0,
  "shape": "line",
  "base_delay": 0.0,
  "delay_per_summon": 0.0,
  "num_entities_spawned": 1,
  "entity_lifespan": -1.0,
  "size": 1.0,
  "target": "self",
  "summon_cap": 0,
  "summon_cap_radius": 0.0
}
```

## `1.16.0`

- 来源：bedrock.dev 官方文档（1.16.0）
- 核实状态：已核实

取值：

```json
{
  "cast_duration": "Total delay of the steps",
  "cooldown_time": 0.0,
  "do_casting": true,
  "max_activation_range": 32.0,
  "min_activation_range": 1.0,
  "particle_color": 0,
  "base_delay": 0.0,
  "delay_per_summon": 0.0,
  "entity_lifespan": -1.0,
  "num_entities_spawned": 1,
  "shape": "line",
  "size": 1.0,
  "summon_cap": 0,
  "summon_cap_radius": 0.0,
  "target": "self"
}
```

## `1.21.0`

- 来源：bedrock.dev 官方文档（1.21.0）
- 核实状态：已核实

取值：

```json
{
  "cast_duration": "Total delay of the steps",
  "cooldown_time": 0.0,
  "do_casting": true,
  "max_activation_range": 32.0,
  "min_activation_range": 1.0,
  "particle_color": 0,
  "base_delay": 0.0,
  "delay_per_summon": 0.0,
  "entity_lifespan": -1.0,
  "num_entities_spawned": 1,
  "shape": "line",
  "size": 1.0,
  "summon_cap": 0,
  "summon_cap_radius": 0.0,
  "target": "self"
}
```

## `1.26.0`

- 来源：bedrock.dev 官方文档（1.26.0）
- 核实状态：已核实

取值：

```json
{
  "cast_duration": "Total delay of the steps",
  "cooldown_time": 0.0,
  "do_casting": true,
  "max_activation_range": 32.0,
  "min_activation_range": 1.0,
  "particle_color": 0,
  "base_delay": 0.0,
  "delay_per_summon": 0.0,
  "entity_lifespan": -1.0,
  "num_entities_spawned": 1,
  "shape": "line",
  "size": 1.0,
  "summon_cap": 0,
  "summon_cap_radius": 0.0,
  "target": "self"
}
```
