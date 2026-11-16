# `minecraft:projectile`

- 出现版本：`1.12.0`、`1.16.0`、`1.21.0`、`1.26.0`
- 核实状态：**已核实**

## 说明

Allows the entity to be a thrown entity.

## `1.12.0`

- 来源：bedrock.dev 官方文档（1.12.0）
- 核实状态：已核实

取值：

```json
{
  "gravity": 0.05,
  "particle": "iconcrack",
  "reflectOnHurt": false,
  "destroyOnHurt": false,
  "offset": [
    0.0,
    0.5,
    0.0
  ],
  "power": 1.3,
  "angleoffset": 0.0,
  "uncertaintyBase": 0.0,
  "uncertaintyMultiplier": 0.0,
  "critParticleOnHurt": false,
  "knockback": true,
  "semirandomdiffdamage": false,
  "onFireTime": 5.0,
  "catchFire": false,
  "lightning": false,
  "fireAffectedByGriefing": false,
  "potionEffect": -1,
  "splashRange": 4.0,
  "splashPotion": false,
  "isdangerous": false,
  "shoottarget": true,
  "inertia": 0.99,
  "liquid_inertia": 0.6,
  "homing": false,
  "shouldbounce": false,
  "multipletargets": true
}
```

## `1.16.0`

- 来源：bedrock.dev 官方文档（1.16.0）
- 核实状态：已核实

取值：

```json
{
  "angle_offset": 0,
  "catch_fire": false,
  "crit_particle_on_hurt": false,
  "destroy_on_hurt": false,
  "fire_affected_by_griefing": false,
  "gravity": 0.05,
  "homing": false,
  "inertia": 0.99,
  "is_dangerous": false,
  "knockback": true,
  "lightning": false,
  "liquid_inertia": 0.6,
  "multiple_targets": true,
  "offset": [
    0,
    0.5,
    0
  ],
  "on_fire_time": 5,
  "particle": "iconcrack",
  "potion_effect": -1,
  "power": 1.3,
  "reflect_on_hurt": false,
  "semi_random_diff_damage": false,
  "shoot_target": true,
  "should_bounce": false,
  "splash_potion": false,
  "splash_range": 4,
  "uncertainty_base": 0,
  "uncertainty_multiplier": 0
}
```

## `1.21.0`

- 来源：bedrock.dev 官方文档（1.21.0）
- 核实状态：已核实

取值：

```json
{
  "angle_offset": 0,
  "catch_fire": false,
  "crit_particle_on_hurt": false,
  "destroy_on_hurt": false,
  "fire_affected_by_griefing": false,
  "gravity": 0.05,
  "hit_nearest_passenger": false,
  "homing": false,
  "inertia": 0.99,
  "is_dangerous": false,
  "knockback": true,
  "lightning": false,
  "liquid_inertia": 0.6,
  "multiple_targets": true,
  "offset": [
    0,
    0,
    0
  ],
  "on_fire_time": 5,
  "particle": "iconcrack",
  "potion_effect": -1,
  "power": 1.3,
  "reflect_immunity": 0,
  "reflect_on_hurt": false,
  "semi_random_diff_damage": false,
  "shoot_target": true,
  "should_bounce": false,
  "splash_potion": false,
  "splash_range": 4,
  "uncertainty_base": 0,
  "uncertainty_multiplier": 0
}
```

## `1.26.0`

- 来源：人工确认；取自项目实际值（1.26.0）
- 核实状态：已核实

取值：

```json
{
  "hit_ground_sound": "item.trident.hit_ground",
  "anchor": 1,
  "gravity": 0,
  "hit_sound": "item.trident.hit",
  "multiple_targets": false,
  "liquid_inertia": 0.5,
  "on_hit": {
    "impact_damage": {
      "apply_knockback_to_blocking_targets": true,
      "damage": 8,
      "knockback": true,
      "destroy_on_hit": false,
      "semi_random_diff_damage": false
    },
    "stick_in_ground": {
      "shake_time": 0
    }
  },
  "offset": [
    0,
    -0.1,
    0
  ],
  "power": 5,
  "should_bounce": true,
  "stop_on_hurt": true,
  "uncertainty_base": 1,
  "uncertainty_multiplier": 0
}
```
