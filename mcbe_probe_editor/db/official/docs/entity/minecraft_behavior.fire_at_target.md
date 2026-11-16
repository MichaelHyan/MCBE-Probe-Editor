# `minecraft:behavior.fire_at_target`

- 出现版本：`1.21.0`、`1.26.0`
- 核实状态：**已核实**

## 说明

Allows an entity to attack by firing a shot with a delay. Anchor and offset parameters of this component overrides the anchor and offset from projectile component.

## `1.21.0`

- 来源：bedrock.dev 官方文档（1.21.0）
- 核实状态：已核实

取值：

```json
{
  "attack_cooldown": 0.5,
  "attack_range": [
    2.0,
    16.0
  ],
  "max_head_rotation_x": 30.0,
  "max_head_rotation_y": 30.0,
  "owner_anchor": 2,
  "owner_offset": [
    0.0,
    0.0,
    0.0
  ],
  "post_shoot_delay": 0.2,
  "pre_shoot_delay": 0.75,
  "ranged_fov": 90.0,
  "target_anchor": 2,
  "target_offset": [
    0.0,
    0.0,
    0.0
  ]
}
```

## `1.26.0`

- 来源：bedrock.dev 官方文档（1.26.0）
- 核实状态：已核实

取值：

```json
{
  "attack_cooldown": 0.5,
  "attack_range": [
    2.0,
    16.0
  ],
  "max_head_rotation_x": 30.0,
  "max_head_rotation_y": 30.0,
  "owner_anchor": 2,
  "owner_offset": [
    0.0,
    0.0,
    0.0
  ],
  "post_shoot_delay": 0.2,
  "pre_shoot_delay": 0.75,
  "ranged_fov": 90.0,
  "target_anchor": 2,
  "target_offset": [
    0.0,
    0.0,
    0.0
  ]
}
```
