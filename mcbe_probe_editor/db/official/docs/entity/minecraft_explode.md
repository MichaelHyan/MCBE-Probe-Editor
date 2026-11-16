# `minecraft:explode`

- 出现版本：`1.12.0`、`1.16.0`、`1.21.0`、`1.26.0`
- 核实状态：**已核实**

## 说明

Defines how the entity explodes.

## `1.12.0`

- 来源：bedrock.dev 官方文档（1.12.0）
- 核实状态：已核实

取值：

```json
{
  "fuseLength": [
    0.0,
    0.0
  ],
  "power": 3.0,
  "maxResistance": "Infinite",
  "fuseLit": false,
  "causesFire": false,
  "breaks_blocks": true,
  "fireAffectedByGriefing": false,
  "destroyAffectedByGriefing": false
}
```

## `1.16.0`

- 来源：bedrock.dev 官方文档（1.16.0）
- 核实状态：已核实

取值：

```json
{
  "breaks_blocks": true,
  "causes_fire": false,
  "destroy_affected_by_griefing": false,
  "fire_affected_by_griefing": false,
  "fuse_length": [
    0.0,
    0.0
  ],
  "fuse_lit": false,
  "max_resistance": 3.40282e+38,
  "power": 3
}
```

## `1.21.0`

- 来源：bedrock.dev 官方文档（1.21.0）
- 核实状态：已核实

取值：

```json
{
  "allow_underwater": false,
  "breaks_blocks": true,
  "causes_fire": false,
  "damage_scaling": 1.0,
  "destroy_affected_by_griefing": false,
  "fire_affected_by_griefing": false,
  "fuse_length": [
    0.0,
    0.0
  ],
  "fuse_lit": false,
  "knockback_scaling": 1.0,
  "max_resistance": 3.40282e+38,
  "negates_fall_damage": false,
  "particle_effect": "explosion",
  "power": 3,
  "sound_effect": "explode",
  "toggles_blocks": false
}
```

## `1.26.0`

- 来源：bedrock.dev 官方文档（1.26.0）
- 核实状态：已核实

取值：

```json
{
  "allow_underwater": false,
  "breaks_blocks": true,
  "causes_fire": false,
  "damage_scaling": 1.0,
  "destroy_affected_by_griefing": false,
  "fire_affected_by_griefing": false,
  "fuse_length": [
    0.0,
    0.0
  ],
  "fuse_lit": false,
  "knockback_scaling": 1.0,
  "max_resistance": 3.40282e+38,
  "negates_fall_damage": false,
  "particle_effect": "explosion",
  "power": 3,
  "sound_effect": "explode",
  "toggles_blocks": false
}
```
