# `minecraft:behavior.timer_flag_2`

- 出现版本：`1.21.0`、`1.26.0`
- 核实状态：**已核实**

## 说明

Fires an event when this behavior starts, then waits for a duration before stopping. When stopping due to that timeout or due to being interrupted by another behavior, fires another event. query.timer_flag_2 will return 1.0 on both the client and server when this behavior is running, and 0.0 otherwise.

## `1.21.0`

- 来源：bedrock.dev 官方文档（1.21.0）
- 核实状态：已核实

取值：

```json
{
  "cooldown_range": [
    10.0,
    10.0
  ],
  "duration_range": [
    2.0,
    2.0
  ]
}
```

## `1.26.0`

- 来源：bedrock.dev 官方文档（1.26.0）
- 核实状态：已核实

取值：

```json
{
  "cooldown_range": [
    0,
    0
  ],
  "duration_range": [
    0,
    0
  ]
}
```
