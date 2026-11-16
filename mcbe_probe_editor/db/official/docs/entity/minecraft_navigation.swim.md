# `minecraft:navigation.swim`

- 出现版本：`1.12.0`、`1.16.0`、`1.21.0`、`1.26.0`
- 核实状态：**已核实**

## 说明

Allows this entity to generate paths that include water.

## `1.12.0`

- 来源：bedrock.dev 官方文档（1.12.0）
- 核实状态：已核实

取值：

```json
{
  "can_path_over_water": false,
  "can_sink": true,
  "avoid_sun": false,
  "can_pass_doors": true,
  "can_open_doors": false,
  "can_break_doors": false,
  "avoid_water": false,
  "avoid_portals": false
}
```

## `1.16.0`

- 来源：bedrock.dev 官方文档（1.16.0）
- 核实状态：已核实

取值：

```json
{
  "avoid_portals": false,
  "avoid_sun": false,
  "avoid_water": false,
  "can_break_doors": false,
  "can_open_doors": false,
  "can_open_iron_doors": false,
  "can_pass_doors": true,
  "can_path_from_air": false,
  "can_path_over_lava": false,
  "can_path_over_water": false,
  "can_sink": true,
  "can_walk_in_lava": false
}
```

## `1.21.0`

- 来源：bedrock.dev 官方文档（1.21.0）
- 核实状态：已核实

取值：

```json
{
  "avoid_damage_blocks": false,
  "avoid_portals": false,
  "avoid_sun": false,
  "avoid_water": false,
  "can_breach": false,
  "can_break_doors": false,
  "can_jump": true,
  "can_open_doors": false,
  "can_open_iron_doors": false,
  "can_pass_doors": true,
  "can_path_from_air": false,
  "can_path_over_lava": false,
  "can_path_over_water": false,
  "can_sink": true,
  "can_swim": false,
  "can_walk": true,
  "can_walk_in_lava": false,
  "is_amphibious": false
}
```

## `1.26.0`

- 来源：bedrock.dev 官方文档（1.26.0）
- 核实状态：已核实

取值：

```json
{
  "avoid_damage_blocks": false,
  "avoid_portals": false,
  "avoid_sun": false,
  "avoid_water": false,
  "can_breach": false,
  "can_break_doors": false,
  "can_jump": true,
  "can_open_doors": false,
  "can_open_iron_doors": false,
  "can_pass_doors": true,
  "can_path_from_air": false,
  "can_path_over_lava": false,
  "can_path_over_water": false,
  "can_sink": true,
  "can_swim": false,
  "can_walk": true,
  "can_walk_in_lava": false,
  "is_amphibious": false
}
```
