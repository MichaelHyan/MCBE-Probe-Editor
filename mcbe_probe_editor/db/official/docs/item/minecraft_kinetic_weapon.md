# `minecraft:kinetic_weapon`

- 出现版本：`1.26.0`
- 核实状态：**已核实**

## 说明

Allows an item to deal kinetic damage and its effects. This happens every tick while in use, in a straight line along the user's view vector, with damage computed based on both the user's and the target's velocity projected onto the view vector (via a dot product). The more the user and target move toward each other, and the more this movement is aligned with the user's view vector, the higher the damage. After "damage_multiplier" and "damage_modifier" are applied, the resulting damage is floored to the nearest lower integer.

## `1.26.0`

- 来源：bedrock-samples json_schemas/server/item/1.26.30
- 核实状态：已核实

取值：

```json
{
  "damage_modifier": 0,
  "damage_multiplier": 1,
  "delay": 0,
  "hitbox_margin": 0,
  "reach": {
    "max": 3,
    "min": 0
  }
}
```
