# `minecraft:behavior.defend_village_target`

- 出现版本：`1.12.0`、`1.21.0`、`1.26.0`
- 核实状态：**已核实**

## 说明

Allows the mob to stay in the village and fight mobs hostile to the villagers.

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

## `1.21.0`

- 来源：bedrock.dev 官方文档（1.21.0）
- 核实状态：已核实

取值：

```json
{
  "attack_chance": 0.05,
  "attack_owner": false,
  "must_reach": false,
  "must_see": false,
  "must_see_forget_duration": 3.0,
  "persist_time": 0.0,
  "within_radius": 0.0
}
```

## `1.26.0`

- 来源：bedrock.dev 官方文档（1.26.0）
- 核实状态：已核实

取值：

```json
{
  "attack_chance": 0.05,
  "attack_owner": false,
  "must_reach": false,
  "must_see": false,
  "must_see_forget_duration": 3.0,
  "persist_time": 0.0,
  "within_radius": 0.0
}
```
