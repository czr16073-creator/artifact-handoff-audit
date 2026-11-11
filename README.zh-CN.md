# Artifact Handoff Audit · 交付物交接审计

[English](README.md)

把 CSV 交给其他团队或导入系统前，用它核对实际文件是否符合接收要求。它会指出缺失的列、格式错误的记录、无效值和重复主键，并给出具体行号和列名。

## 在智能体中使用

把整个目录复制到智能体的 Skill 目录，再提供 CSV 和下游要求、导入模板或字段定义。例如：

> 用 `artifact-handoff-audit` 按附件里的导入要求检查这份导出表。请列出会阻塞导入的问题、具体行号和列名，并指出哪些字段需要回到源数据重新导出。

## 从命令行运行

需要 Python 3.9 或更高版本，无须安装第三方库。在仓库根目录运行两个合成案例：

```sh
python scripts/audit.py examples/monthly-finance-export.csv examples/finance-contract.json
python scripts/audit.py examples/inventory-import.csv examples/import-contract.json
```

- **财务对账。** 下游要逐订单数据，月度汇总表缺少订单号、币种和退款状态。
- **库存导入。** 第 2 和第 3 行的站点与日期重复。第 4 行日期不存在，库存数量也填成了小数。

两个示例都预期审计失败。检查自己的文件时，按[接收要求格式](references/contract.md)准备 JSON。退出码 `0` 表示通过，`1` 表示检查未通过，`2` 表示审计无法运行。

脚本只读 CSV。通过代表文件满足已声明的检查项。要确认源数据是否导出完整、字段的业务含义是否一致，还需核对来源。
