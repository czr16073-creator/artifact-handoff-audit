# CSV handoff contract

The CLI accepts a comma-separated, UTF-8 CSV with a header row and a UTF-8 JSON contract. A UTF-8 BOM is supported. Quoted fields may span multiple lines.

```json
{
  "columns": {
    "order_id": {"required": true, "type": "text"},
    "refund_status": {"required": true, "allowed": ["none", "partial", "full"]},
    "amount": {"required": true, "type": "decimal"}
  },
  "key": ["order_id"],
  "allow_extra_columns": true,
  "min_rows": 1
}
```

- `columns` is required and must contain at least one named rule. Names match the header exactly. Every declared column must exist in the header. Use an empty rule object to require a column without constraining its cells.
- `required` defaults to false. When true, empty or whitespace-only cells fail.
- `type` defaults to `text`. Other types are `integer` (signed ASCII digits), `decimal` (finite decimal number, with optional exponent), and `date` (valid calendar date in YYYY-MM-DD form).
- `allowed` is an optional list of exact, case-sensitive, nonblank string values. Optional blank cells skip type and allowed-value checks.
- `key` is an optional list of column names. All key components must be nonblank. Key values use the exact CSV text and must be unique in combination. Use the smallest set of fields that identifies one row at the required grain.
- `allow_extra_columns` defaults to true. Set false for a strict import format.
- `min_rows` defaults to 0. It counts structurally readable data records, including records with cell-level violations.

Exit codes are 0 for pass, 1 for a failed CSV check, and 2 for invalid contract, CLI arguments, or an unreadable file. Findings identify the file, column where applicable, and the physical start line of the CSV record. A duplicate includes the first occurrence's line. The default cap is 50 detailed issues. Counts always include all issues found, and findings exclude cell values to avoid copying sensitive values into reports.

A pass means the CSV satisfies the declared checks. A unique key cannot establish that every source record was exported or that a field has the correct business meaning.
