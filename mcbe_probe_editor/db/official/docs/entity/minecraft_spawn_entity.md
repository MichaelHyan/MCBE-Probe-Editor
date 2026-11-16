# `minecraft:spawn_entity`

- 出现版本：`1.12.0`、`1.16.0`、`1.21.0`、`1.26.0`
- 核实状态：**已核实**

## 说明

Adds a timer after which this entity will spawn another entity or item (similar to vanilla's chicken's egg-laying behavior).

## `1.12.0`

- 来源：bedrock.dev 官方文档（1.12.0）
- 核实状态：已核实

取值：

```json
{
  "should_leash": false,
  "num_to_spawn": 1,
  "min_wait_time": 300,
  "max_wait_time": 600,
  "spawn_sound": "plop",
  "spawn_item": "egg",
  "spawn_method": "born",
  "spawn_event": "minecraft:entity_born",
  "single_use": false
}
```

## `1.16.0`

- 来源：bedrock.dev 官方文档（1.16.0）
- 核实状态：已核实

取值：

```json
{
  "max_wait_time": 600,
  "min_wait_time": 300,
  "num_to_spawn": 1,
  "should_leash": false,
  "single_use": false,
  "spawn_event": "minecraft:entity_born",
  "spawn_item": "egg",
  "spawn_method": "born",
  "spawn_sound": "plop"
}
```

## `1.21.0`

- 来源：bedrock.dev 官方文档（1.21.0）
- 核实状态：已核实

取值：

```json
{
  "max_wait_time": 600,
  "min_wait_time": 300,
  "num_to_spawn": 1,
  "should_leash": false,
  "single_use": false,
  "spawn_event": "minecraft:entity_born",
  "spawn_item": "egg",
  "spawn_method": "born",
  "spawn_sound": "plop"
}
```

## `1.26.0`

- 来源：bedrock.dev 官方文档（1.26.0）
- 核实状态：已核实

取值：

```json
{
  "max_wait_time": 600,
  "min_wait_time": 300,
  "num_to_spawn": 1,
  "should_leash": false,
  "single_use": false,
  "spawn_event": "minecraft:entity_born",
  "spawn_item": "egg",
  "spawn_method": "born",
  "spawn_sound": "plop"
}
```
