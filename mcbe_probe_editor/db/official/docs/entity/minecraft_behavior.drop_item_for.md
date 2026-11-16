# `minecraft:behavior.drop_item_for`

- 出现版本：`1.12.0`、`1.21.0`、`1.26.0`
- 核实状态：**已核实**

## 说明

Allows the mob to move near a target and drop an item.

## `1.12.0`

- 来源：bedrock.dev 官方文档（1.12.0）
- 核实状态：已核实

取值：

```json
{
  "speed_multiplier": 1.0,
  "search_range": 0,
  "search_height": 1,
  "goal_radius": 0.5,
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
  "cooldown": 0.2,
  "drop_item_chance": 1.0,
  "goal_radius": 0.5,
  "max_head_look_at_height": 10.0,
  "minimum_teleport_distance": 2.0,
  "offering_distance": 1.0,
  "search_count": 0,
  "search_height": 1,
  "search_range": 0,
  "seconds_before_pickup": 0.0,
  "speed_multiplier": 1.0,
  "target_range": [
    1,
    1,
    1
  ],
  "teleport_offset": [
    0,
    1,
    0
  ],
  "time_of_day_range": [
    0,
    1
  ]
}
```

## `1.26.0`

- 来源：bedrock.dev 官方文档（1.26.0）
- 核实状态：已核实

取值：

```json
{
  "cooldown": 0.2,
  "drop_item_chance": 1.0,
  "goal_radius": 0.5,
  "max_head_look_at_height": 10.0,
  "minimum_teleport_distance": 2.0,
  "offering_distance": 1.0,
  "search_count": 0,
  "search_height": 1,
  "search_range": 0,
  "seconds_before_pickup": 0.0,
  "speed_multiplier": 1.0,
  "target_range": [
    1,
    1,
    1
  ],
  "teleport_offset": [
    0,
    1,
    0
  ],
  "time_of_day_range": [
    0,
    1
  ]
}
```
