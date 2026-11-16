# `minecraft:piercing_weapon`

- 出现版本：`1.26.0`
- 核实状态：**已核实**

## 说明

Allows an item to deal damage to all entities detected in a straight line along the user's view vector. Items with this component cannot destroy blocks, as the attack action always takes priority, regardless of what the user is looking at.

## `1.26.0`

- 来源：bedrock-samples json_schemas/server/item/1.26.30
- 核实状态：已核实

取值：

```json
{
  "hitbox_margin": 0,
  "reach": {
    "max": 3,
    "min": 0
  }
}
```
