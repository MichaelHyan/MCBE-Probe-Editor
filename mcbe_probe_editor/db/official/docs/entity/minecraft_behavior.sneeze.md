# `minecraft:behavior.sneeze`

- 出现版本：`1.12.0`、`1.16.0`、`1.21.0`、`1.26.0`
- 核实状态：**已核实**

## 说明

Allows the mob to stop and sneeze possibly startling nearby mobs and dropping an item.

## `1.12.0`

- 来源：bedrock.dev 官方文档（1.12.0）
- 核实状态：已核实

取值：

```json
{
  "cooldown_time": 0.0,
  "probability": 0.02,
  "drop_item_chance": 1.0,
  "prepare_time": 1.0,
  "max_dist": 16,
  "walk_speed_multiplier": 1.0,
  "sprint_speed_multiplier": 1.0,
  "must_see": false,
  "must_see_forget_duration": 3.0
}
```

## `1.16.0`

- 来源：bedrock.dev 官方文档（1.16.0）
- 核实状态：已核实

取值：

```json
{
  "cooldown_time": 0.0,
  "drop_item_chance": 1.0,
  "max_dist": 16,
  "must_see": false,
  "must_see_forget_duration": 3.0,
  "sprint_speed_multiplier": 1.0,
  "walk_speed_multiplier": 1.0
}
```

## `1.21.0`

- 来源：bedrock.dev 官方文档（1.21.0）
- 核实状态：已核实

取值：

```json
{
  "cooldown_time": 0.0,
  "drop_item_chance": 1.0,
  "cooldown": 0.0,
  "max_dist": 16,
  "must_see": false,
  "must_see_forget_duration": 3.0,
  "reevaluate_description": false,
  "sprint_speed_multiplier": 1.0,
  "walk_speed_multiplier": 1.0
}
```

## `1.26.0`

- 来源：bedrock.dev 官方文档（1.26.0）
- 核实状态：已核实

取值：

```json
{
  "cooldown_time": 0.0,
  "drop_item_chance": 1.0,
  "cooldown": 0.0,
  "max_dist": 16,
  "must_see": false,
  "must_see_forget_duration": 3.0,
  "reevaluate_description": false,
  "sprint_speed_multiplier": 1.0,
  "walk_speed_multiplier": 1.0
}
```
