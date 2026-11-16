# `minecraft:breathable`

- 出现版本：`1.12.0`、`1.16.0`、`1.21.0`、`1.26.0`
- 核实状态：**已核实**

## 说明

Defines what blocks this entity can breathe in and gives them the ability to suffocate

## `1.12.0`

- 来源：bedrock.dev 官方文档（1.12.0）
- 核实状态：已核实

取值：

```json
{
  "totalSupply": 15,
  "suffocateTime": -20,
  "inhaleTime": 0.0,
  "breathesAir": true,
  "breathesWater": false,
  "breathesLava": false,
  "breathesSolids": false,
  "generatesBubbles": true
}
```

## `1.16.0`

- 来源：bedrock.dev 官方文档（1.16.0）
- 核实状态：已核实

取值：

```json
{
  "breathes_air": true,
  "breathes_lava": true,
  "breathes_solids": false,
  "breathes_water": false,
  "generates_bubbles": true,
  "inhale_time": 0,
  "suffocate_time": -20,
  "total_supply": 15
}
```

## `1.21.0`

- 来源：bedrock.dev 官方文档（1.21.0）
- 核实状态：已核实

取值：

```json
{
  "breathes_air": true,
  "breathes_lava": true,
  "breathes_solids": false,
  "breathes_water": false,
  "can_dehydrate": false,
  "generates_bubbles": true,
  "inhale_time": 0,
  "suffocate_time": -20,
  "total_supply": 15
}
```

## `1.26.0`

- 来源：bedrock.dev 官方文档（1.26.0）
- 核实状态：已核实

取值：

```json
{
  "breathes_air": true,
  "breathes_lava": true,
  "breathes_solids": false,
  "breathes_water": false,
  "generates_bubbles": true,
  "inhale_time": 0,
  "suffocate_time": -20,
  "total_supply": 15
}
```
