# `minecraft:leashable_to`

- 出现版本：`1.16.0`、`1.21.0`、`1.26.0`
- 核实状态：**已核实**

## 说明

Allows players to leash entities to this entity, retrieve entities already leashed to it, or free them using shears. For the last interaction to work, the leashed entities must have "can_be_cut" set to true in their "minecraft:leashable" component.

## `1.16.0`

- 来源：人工确认；取自项目实际值（1.16.0）
- 核实状态：已核实

取值：

```json
{}
```

## `1.21.0`

- 来源：bedrock.dev 官方文档（1.21.0）
- 核实状态：已核实

取值：

```json
{
  "can_retrieve_from": false
}
```

## `1.26.0`

- 来源：bedrock.dev 官方文档（1.26.0）
- 核实状态：已核实

取值：

```json
{
  "can_retrieve_from": false,
  "unleash_on_removal": true
}
```
