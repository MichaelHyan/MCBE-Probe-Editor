# `minecraft:throwable`

- 出现版本：`1.16.0`、`1.21.0`、`1.26.0`
- 核实状态：**已核实**

## 说明

Throwable item component. Throwable items, such as a snowball.

## `1.16.0`

- 来源：bedrock.dev 官方文档（1.16.0）
- 核实状态：已核实

字段结构（官方文档未提供默认值）：
- `do_swing_animation`
- `launch_power_scale`
- `max_draw_duration`
- `max_launch_power`
- `min_draw_duration`
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
  "do_swing_animation": false,
  "launch_power_scale": 1,
  "max_draw_duration": 0,
  "max_launch_power": 1,
  "min_draw_duration": 0,
  "scale_power_by_draw_duration": false
}
```

## `1.26.0`

- 来源：bedrock-samples json_schemas/server/item/1.26.30
- 核实状态：已核实

取值：

```json
{
  "do_swing_animation": false,
  "launch_power_scale": 1,
  "max_draw_duration": 0,
  "max_launch_power": 1,
  "min_draw_duration": 0,
  "scale_power_by_draw_duration": false
}
```
