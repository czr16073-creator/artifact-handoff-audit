# Artifact Handoff Audit

[简体中文](README.zh-CN.md)

Check a CSV before handing it to another team or importing it into a system. Give the tool the actual file and the receiving requirements. It reports missing columns, malformed records, invalid values, and duplicate record keys with line and column locations.

## Use with an agent

Copy the entire folder into your agent's skill directory. Give the agent your CSV and the receiving team's requirements, import template, or schema. For example:

> Use `artifact-handoff-audit` to check this export against the attached import requirements. Identify the blocking issues by line and column, and tell me which fields need to be regenerated from source.

## Run locally

Use Python 3.9 or later. No third-party packages are required. From the repository root, run the synthetic examples:

```sh
python scripts/audit.py examples/monthly-finance-export.csv examples/finance-contract.json
python scripts/audit.py examples/inventory-import.csv examples/import-contract.json
```

- **Finance handoff.** The receiver needs order-level records. The monthly export lacks order ID, currency, and refund status.
- **Inventory import.** Lines 2 and 3 share the same site and date. Line 4 contains an invalid date and a fractional value where an integer is required.

Both examples deliberately fail. To use your own files, see the [contract format](references/contract.md). Exit codes are 0 for pass, 1 for failed checks, and 2 when the audit cannot run.

The audit reads CSV files without changing them. A pass covers the declared checks. Verifying source completeness and business meaning requires source evidence.
