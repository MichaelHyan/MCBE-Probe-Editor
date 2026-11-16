# `minecraft:rideable`

- 出现版本：`1.12.0`、`1.16.0`、`1.21.0`、`1.26.0`
- 核实状态：**已核实**

## 说明

Determines whether this entity can be ridden. Allows specifying the different seat positions and quantity.

## `1.12.0`

- 来源：bedrock.dev 官方文档（1.12.0）
- 核实状态：已核实

取值：

```json
{
  "seat_count": 1,
  "crouching_skip_interact": true,
  "controlling_seat": 0,
  "pull_in_entities": false,
  "rider_can_interact": false,
  "position": [
    0.0,
    0.0,
    0.0
  ],
  "min_rider_count": 0,
  "max_rider_count": 0,
  "rotate_rider_by": 0.0,
  "lock_rider_rotation": 181.0
}
```

## `1.16.0`

- 来源：bedrock.dev 官方文档（1.16.0）
- 核实状态：已核实

取值：

```json
{
  "controlling_seat": 0,
  "crouching_skip_interact": true,
  "priority": 0,
  "pull_in_entities": false,
  "rider_can_interact": false,
  "seat_count": 1,
  "lock_rider_rotation": 181,
  "max_rider_count": "seat_count",
  "min_rider_count": 0,
  "position": [
    0,
    0,
    0
  ],
  "rotate_rider_by": 0
}
```

## `1.21.0`

- 来源：bedrock.dev 官方文档（1.21.0）
- 核实状态：已核实

取值：

```json
{
  "controlling_seat": 0,
  "crouching_skip_interact": true,
  "dismount_mode": "default",
  "passenger_max_width": 0.0,
  "pull_in_entities": false,
  "rider_can_interact": false,
  "seat_count": 1,
  "lock_rider_rotation": 181,
  "max_rider_count": 0,
  "min_rider_count": 0,
  "position": [
    0,
    0,
    0
  ],
  "rotate_rider_by": 0
}
```

## `1.26.0`

- 来源：bedrock.dev 官方文档（1.26.0）
- 核实状态：已核实

取值：

```json
{
  "controlling_seat": 0,
  "crouching_skip_interact": true,
  "dismount_mode": "default",
  "passenger_max_width": 0.0,
  "pull_in_entities": false,
  "rider_can_interact": false,
  "seat_count": 1,
  "lock_rider_rotation": 181,
  "max_rider_count": 0,
  "min_rider_count": 0,
  "position": [
    0,
    0,
    0
  ],
  "rotate_rider_by": 0
}
```
