# `minecraft:lookat`

- 出现版本：`1.12.0`、`1.16.0`
- 核实状态：**已核实**

## 说明

Defines the behavior when another entity looks at this entity.

## `1.12.0`

- 来源：bedrock.dev 官方文档（1.12.0）
- 核实状态：已核实

取值：

```json
{
  "setTarget": true,
  "searchRadius": 10.0,
  "mAllowInvulnerable": false,
  "look_cooldown": [
    0.0,
    0.0
  ],
  "filters": "player"
}
```

## `1.16.0`

- 来源：bedrock.dev 官方文档（1.16.0）
- 核实状态：已核实

取值：

```json
{
  "allow_invulnerable": false,
  "look_cooldown": [
    0,
    0
  ],
  "search_radius": 10,
  "set_target": true
}
```
