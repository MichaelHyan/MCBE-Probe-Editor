# `minecraft:behavior.fertilize_farm_block`

- 出现版本：`1.21.0`、`1.26.0`
- 核实状态：**已核实**

## 说明

Allows the mob to search within an area for a growable crop block. If found, the mob will use any available fertilizer in their inventory on the crop. This goal will not execute if the mob does not have a fertilizer item in its inventory.

## `1.21.0`

- 来源：bedrock.dev 官方文档（1.21.0）
- 核实状态：已核实

取值：

```json
{
  "goal_radius": 1.5,
  "max_fertilizer_usage": 1,
  "search_cooldown_max_seconds": 8.0,
  "search_count": 9,
  "search_height": 1,
  "search_range": 1,
  "speed_multiplier": 0.5
}
```

## `1.26.0`

- 来源：bedrock.dev 官方文档（1.26.0）
- 核实状态：已核实

取值：

```json
{
  "goal_radius": 1.5,
  "max_fertilizer_usage": 1,
  "search_cooldown_max_seconds": 8.0,
  "search_count": 9,
  "search_height": 1,
  "search_range": 1,
  "speed_multiplier": 0.5
}
```
