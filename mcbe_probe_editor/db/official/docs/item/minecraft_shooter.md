# `minecraft:shooter`

- 出现版本：`1.16.0`、`1.21.0`、`1.26.0`
- 核实状态：**已核实**

## 说明

Shooter Item Component.

## `1.16.0`

- 来源：bedrock.dev 官方文档（1.16.0）
- 核实状态：已核实

字段结构（官方文档未提供默认值）：
- `ammunition`
- `charge_on_draw`
- `launch_power_scale`
- `max_draw_duration`
- `max_launch_power`
- `scale_power_by_draw_duration`

取值：

```json
{}
```

## `1.21.0`

- 来源：bedrock-samples json_schemas/server/item/1.20.50（最近可得）
- 核实状态：已核实

取值：

```json
{
  "ammunition": [],
  "charge_on_draw": false,
  "max_draw_duration": 0,
  "scale_power_by_draw_duration": false
}
```

## `1.26.0`

- 来源：bedrock-samples json_schemas/server/item/1.26.30
- 核实状态：已核实

取值：

```json
{
  "ammunition": [],
  "charge_on_draw": false,
  "max_draw_duration": 0,
  "scale_power_by_draw_duration": false
}
```
