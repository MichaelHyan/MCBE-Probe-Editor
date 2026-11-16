# `minecraft:behavior.move_around_target`

- 出现版本：`1.21.0`、`1.26.0`
- 核实状态：**已核实**

## 说明

Allows an entity to move around a target. If the entity is too close (i.e. closer than destination range min and height difference limit) it will try to move away from its target. If the entity is too far away from its target it will try to move closer to a random position within the destination range. A randomized amount of those positions will be behind the target, and the spread can be tweaked with 'destination_pos_spread_degrees'.

## `1.21.0`

- 来源：bedrock.dev 官方文档（1.21.0）
- 核实状态：已核实

取值：

```json
{
  "destination_pos_spread_degrees": 90.0,
  "destination_position_range": [
    4.0,
    8.0
  ],
  "height_difference_limit": 10.0,
  "horizontal_search_distance": 5,
  "movement_speed": 0.6,
  "vertical_search_distance": 5
}
```

## `1.26.0`

- 来源：bedrock.dev 官方文档（1.26.0）
- 核实状态：已核实

取值：

```json
{
  "destination_pos_spread_degrees": 90.0,
  "destination_position_range": [
    4.0,
    8.0
  ],
  "height_difference_limit": 10.0,
  "horizontal_search_distance": 5,
  "movement_speed": 0.6,
  "vertical_search_distance": 5
}
```
