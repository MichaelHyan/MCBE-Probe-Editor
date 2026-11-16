# `minecraft:breedable`

- 出现版本：`1.12.0`、`1.16.0`、`1.21.0`、`1.26.0`
- 核实状态：**已核实**

## 说明

Defines the way an entity can get into the 'love' state.

## `1.12.0`

- 来源：bedrock.dev 官方文档（1.12.0）
- 核实状态：已核实

取值：

```json
{
  "requireTame": true,
  "blend_attributes": true,
  "extraBabyChance": 0.0,
  "breedCooldown": 60.0,
  "inheritTamed": true,
  "allowSitting": false,
  "variant": 0.0,
  "extra_variant": 0.0,
  "color": 0.0
}
```

## `1.16.0`

- 来源：bedrock.dev 官方文档（1.16.0）
- 核实状态：已核实

取值：

```json
{
  "allow_sitting": false,
  "blend_attributes": true,
  "breed_cooldown": 60
}
```

## `1.21.0`

- 来源：bedrock.dev 官方文档（1.21.0）
- 核实状态：已核实

取值：

```json
{
  "allow_sitting": false,
  "blend_attributes": true,
  "breed_cooldown": 60
}
```

## `1.26.0`

- 来源：bedrock.dev 官方文档（1.26.0）
- 核实状态：已核实

取值：

```json
{
  "allow_sitting": false,
  "breed_cooldown": 60,
  "causes_pregnancy": false,
  "extra_baby_chance": 0,
  "require_full_health": false,
  "require_tame": true
}
```
