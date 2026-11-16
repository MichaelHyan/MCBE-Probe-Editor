# `minecraft:behavior.random_search_and_dig`

- 出现版本：`1.21.0`、`1.26.0`
- 核实状态：**已核实**

## 说明

Allows this entity to locate a random target block that it can path find to. Once found, the entity will move towards it and dig up an item. [Default target block types: Dirt, Grass, Podzol, DirtWithRoots, MossBlock, Mud, MuddyMangroveRoots].

## `1.21.0`

- 来源：bedrock.dev 官方文档（1.21.0）
- 核实状态：已核实

取值：

```json
{
  "cooldown_range": [
    0.0,
    0.0
  ],
  "digging_duration_range": [
    8.0,
    10.0
  ],
  "find_valid_position_retries": 5,
  "goal_radius": 1.5,
  "search_range_xz": 10,
  "search_range_y": 7,
  "spawn_item_after_seconds": 0.0,
  "spawn_item_pos_offset": 0.0,
  "speed_multiplier": 1.0,
  "target_dig_position_offset": 2.25
}
```

## `1.26.0`

- 来源：bedrock.dev 官方文档（1.26.0）
- 核实状态：已核实

取值：

```json
{
  "cooldown_range": [
    0.0,
    0.0
  ],
  "digging_duration_range": [
    8.0,
    10.0
  ],
  "find_valid_position_retries": 5,
  "goal_radius": 1.5,
  "search_range_xz": 10,
  "search_range_y": 7,
  "spawn_item_after_seconds": 0.0,
  "spawn_item_pos_offset": 0.0,
  "speed_multiplier": 1.0,
  "target_dig_position_offset": 2.25
}
```
