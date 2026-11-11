---
name: artifact-handoff-audit
description: Check actual CSV deliverables against a receiving team's or importer's requirements. Use for data handoffs, CSV import preflight, report exports, and migrations where missing columns, bad values, or incorrect record grain can block the next step.
---

# Artifact handoff audit

1. Identify the receiving step and obtain its requirements from the user, import template, interface specification, or downstream code. Establish what one row represents and what identifies it. Record where each requirement came from. When a requirement is unclear, report it as unverified.
2. Translate verifiable requirements into a JSON contract using [the contract format](references/contract.md). Preserve identifier spelling and leading zeros. Set the key to the columns that jointly identify one required record. Keep the contract and audit outputs separate from the delivered CSV.
3. Run `python scripts/audit.py <delivery.csv> <contract.json>` from this skill directory. For a large report, use the issue counts and representative locations first. Increase `--max-issues` when the user needs a longer repair list.
4. Report blocking issues with file, line, and column. For missing columns or incorrect grain, identify the source export that must be changed. For duplicate keys, compare both locations before proposing any merge or deduplication.
5. Check requirements the contract cannot establish, such as completeness against a source system, definitions, units, and whether the file was aggregated before export. State which checks used independent evidence. Preserve source files during the audit.
