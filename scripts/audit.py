"""Validate a CSV handoff against a receiving-side JSON contract."""

import argparse
from collections import Counter
import csv
from datetime import date
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import re
import sys


INTEGER = re.compile(r"[+-]?[0-9]+")
DECIMAL = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?")
DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


def valid_type(value, kind):
    if kind == "text":
        return True
    if kind == "integer":
        return INTEGER.fullmatch(value) is not None
    if kind == "decimal":
        if not DECIMAL.fullmatch(value):
            return False
        try:
            return Decimal(value).is_finite()
        except InvalidOperation:
            return False
    if not DATE.fullmatch(value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def unique_object(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise ValueError(f"duplicate contract field: {name}")
        result[name] = value
    return result


def validate_fields(obj, permitted, label):
    if not isinstance(obj, dict):
        raise ValueError(f"{label} must be an object")
    unknown = obj.keys() - permitted
    if unknown:
        raise ValueError(f"{label} has unknown fields: {', '.join(sorted(unknown))}")


def nonblank_string(value):
    return isinstance(value, str) and bool(value.strip())


def load_contract(path):
    contract = json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=unique_object)
    validate_fields(contract, {"columns", "key", "allow_extra_columns", "min_rows"}, "contract")
    columns = contract.get("columns")
    if not isinstance(columns, dict) or not columns:
        raise ValueError("columns must be a nonempty object")
    for name, rule in columns.items():
        if not nonblank_string(name):
            raise ValueError("column names must be nonblank")
        validate_fields(rule, {"required", "type", "allowed"}, f"column {name}")
        if type(rule.get("required", False)) is not bool:
            raise ValueError(f"{name}.required must be a boolean")
        if rule.get("type", "text") not in ("text", "integer", "decimal", "date"):
            raise ValueError(f"{name}.type is unsupported")
        if "allowed" in rule:
            values = rule["allowed"]
            if not isinstance(values, list) or not values or not all(
                nonblank_string(value) for value in values
            ):
                raise ValueError(f"{name}.allowed must list nonblank strings")

    key = contract.get("key", [])
    if not isinstance(key, list) or not all(isinstance(name, str) and name in columns for name in key):
        raise ValueError("key must list declared column names")
    if len(set(key)) != len(key):
        raise ValueError("key column names must be unique")
    if type(contract.get("allow_extra_columns", True)) is not bool:
        raise ValueError("allow_extra_columns must be a boolean")
    min_rows = contract.get("min_rows", 0)
    if type(min_rows) is not int or min_rows < 0:
        raise ValueError("min_rows must be a nonnegative integer")
    return contract


class Report:
    def __init__(self, path, limit):
        self.path = str(path)
        self.limit = limit
        self.rows = 0
        self.counts = Counter()
        self.issues = []

    def add(self, code, line, **details):
        self.counts[code] += 1
        if len(self.issues) < self.limit:
            self.issues.append({"code": code, "line": line, **details})

    def as_dict(self):
        return {
            "file": self.path,
            "status": "fail" if self.counts else "pass",
            "rows_checked": self.rows,
            "issue_counts": dict(self.counts),
            "issues": self.issues,
            "omitted_issues": sum(self.counts.values()) - len(self.issues),
        }


def header_positions(header, contract, report):
    counts = Counter(header)
    for column, count in counts.items():
        if not column.strip():
            report.add("blank_header", 1)
        elif count > 1:
            report.add("duplicate_header", 1, column=column, occurrences=count)
    for column in contract["columns"]:
        if column not in counts:
            report.add("missing_column", 1, column=column)
    if not contract.get("allow_extra_columns", True):
        for column in counts:
            if column.strip() and column not in contract["columns"]:
                report.add("unexpected_column", 1, column=column)
    return {column: index for index, column in enumerate(header) if counts[column] == 1}


def check_cell(column, value, rule, line, report):
    if not value.strip():
        if rule.get("required", False):
            report.add("blank_required_value", line, column=column)
        return
    kind = rule.get("type", "text")
    if not valid_type(value, kind):
        report.add("invalid_type", line, column=column, expected=kind)
    if "allowed" in rule and value not in rule["allowed"]:
        report.add("invalid_allowed_value", line, column=column)


def check_key(key, positions, row, line, seen, report):
    values = tuple(row[positions[column]] for column in key)
    blanks = [column for column, value in zip(key, values) if not value.strip()]
    if blanks:
        report.add("blank_key", line, columns=blanks)
    elif values in seen:
        report.add("duplicate_key", line, columns=key, first_line=seen[values])
    else:
        seen[values] = line


def audit_csv(path, contract, limit):
    report = Report(path, limit)
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream, strict=True)
        line = 1
        try:
            header = next(reader, [])
            if not header:
                report.add("missing_header", 1)
                return report

            positions = header_positions(header, contract, report)
            rules = [
                (column, positions[column], rule)
                for column, rule in contract["columns"].items()
                if column in positions
            ]
            key = contract.get("key", [])
            check_keys = bool(key) and all(column in positions for column in key)
            seen = {}
            while True:
                line = reader.line_num + 1
                row = next(reader, None)
                if row is None:
                    break
                if len(row) != len(header):
                    report.add("row_width", line, expected=len(header), actual=len(row))
                    continue
                report.rows += 1
                for column, index, rule in rules:
                    check_cell(column, row[index], rule, line, report)
                if check_keys:
                    check_key(key, positions, row, line, seen, report)
        except csv.Error as error:
            report.add("malformed_csv", line, detail=str(error))
            return report
    min_rows = contract.get("min_rows", 0)
    if report.rows < min_rows:
        report.add("too_few_rows", None, expected=min_rows, actual=report.rows)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", type=Path)
    parser.add_argument("contract", type=Path)
    parser.add_argument("--max-issues", type=int, default=50)
    args = parser.parse_args()
    if args.max_issues < 0:
        parser.error("--max-issues must be nonnegative")
    try:
        contract = load_contract(args.contract)
        report = audit_csv(args.csv_file, contract, args.max_issues)
    except (OSError, ValueError) as error:
        print(f"Cannot run audit: {error}", file=sys.stderr)
        return 2
    print(json.dumps(report.as_dict(), indent=2))
    return 1 if report.counts else 0


if __name__ == "__main__":
    sys.exit(main())
