# `minecraft:economy_trade_table`

- 出现版本：`1.12.0`、`1.16.0`、`1.21.0`、`1.26.0`
- 核实状态：**已核实**

## 说明

Defines this entity's ability to trade with players.

## `1.12.0`

- 来源：bedrock.dev 官方文档（1.12.0）
- 核实状态：已核实

取值：

```json
{
  "new_screen": false,
  "hero_demand_discount": -4,
  "persist_trades": false,
  "convert_trades_economy": false
}
```

## `1.16.0`

- 来源：bedrock.dev 官方文档（1.16.0）
- 核实状态：已核实

取值：

```json
{
  "convert_trades_economy": false,
  "cured_discount": [
    -5,
    -20
  ],
  "hero_demand_discount": -4,
  "max_cured_discount": [
    -25,
    -63
  ],
  "max_nearby_cured_discount": -200,
  "nearby_cured_discount": -25,
  "new_screen": false,
  "persist_trades": false,
  "show_trade_screen": true,
  "use_legacy_price_formula": false
}
```

## `1.21.0`

- 来源：bedrock.dev 官方文档（1.21.0）
- 核实状态：已核实

取值：

```json
{
  "convert_trades_economy": false,
  "cured_discount": [
    -25,
    -20
  ],
  "hero_demand_discount": -4,
  "max_cured_discount": [
    -25,
    -20
  ],
  "max_nearby_cured_discount": -200,
  "nearby_cured_discount": -20,
  "new_screen": false,
  "persist_trades": false,
  "show_trade_screen": true,
  "use_legacy_price_formula": false
}
```

## `1.26.0`

- 来源：bedrock.dev 官方文档（1.26.0）
- 核实状态：已核实

取值：

```json
{
  "convert_trades_economy": false,
  "cured_discount": {
    "min": -25,
    "max": -20
  },
  "hero_demand_discount": -4,
  "max_cured_discount": {
    "min": -25,
    "max": -20
  },
  "max_nearby_cured_discount": -200,
  "nearby_cured_discount": -20,
  "new_screen": false,
  "persist_trades": false,
  "show_trade_screen": true,
  "use_legacy_price_formula": false
}
```
