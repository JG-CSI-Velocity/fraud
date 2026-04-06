#!/usr/bin/env python3
"""Interactive client YAML config generator.

Reads column headers from a client's Excel or CSV file and walks you
through mapping them to the screener's expected fields.
"""

import argparse
import csv
import sys
from pathlib import Path

import openpyxl
import yaml


REQUIRED_FIELDS = {
    "manager": "Employee or manager who owns the account",
    "account_holder": "Person who was referred (new member)",
    "referrer": "Person who made the referral",
}

OPTIONAL_FIELDS = {
    "row_number": "Row number or ID column",
    "branch_number": "Branch ID or number",
    "branch_name": "Branch name",
    "issue_date": "Date the referral was issued",
    "certificate_id": "Certificate or tracking ID",
    "referral_code": "Referral code",
    "program_name": "Program name",
    "product_count": "Number of products opened",
}


def read_headers(file_path: str, sheet_name: str = None) -> list[str]:
    path = Path(file_path)
    if path.suffix.lower() in (".xlsx", ".xls"):
        wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
        if sheet_name:
            ws = wb[sheet_name]
        else:
            ws = wb.active
            sheet_name = ws.title
        headers = [cell.value for cell in next(ws.iter_rows(max_row=1))]
        wb.close()
        return headers, sheet_name
    elif path.suffix.lower() == ".csv":
        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            headers = next(reader)
        return headers, None
    else:
        print(f"Error: Unsupported file type: {path.suffix}")
        sys.exit(1)


def display_headers(headers: list[str]):
    print("\nColumns found in your file:")
    print("-" * 50)
    for i, h in enumerate(headers, 1):
        display = h if h else "(empty)"
        print(f"  {i:3d}. {display}")
    print()


def prompt_mapping(headers: list[str], field_name: str, description: str, required: bool) -> str | None:
    label = "REQUIRED" if required else "optional"
    print(f"  [{label}] {field_name}: {description}")
    print(f"    Enter column number (1-{len(headers)}), or press Enter to skip: ", end="")

    while True:
        choice = input().strip()
        if not choice:
            if required:
                print(f"    This field is required. Enter a column number: ", end="")
                continue
            return None
        try:
            idx = int(choice)
            if 1 <= idx <= len(headers):
                header = headers[idx - 1]
                print(f"    -> Mapped to: \"{header}\"")
                return header
            else:
                print(f"    Invalid. Enter 1-{len(headers)}: ", end="")
        except ValueError:
            print(f"    Enter a number or press Enter to skip: ", end="")


def main():
    parser = argparse.ArgumentParser(
        description="Generate a client YAML config for the fraud screener"
    )
    parser.add_argument("input_file", help="Path to the client's Excel or CSV file")
    parser.add_argument("--sheet", help="Excel sheet name (defaults to active sheet)")
    args = parser.parse_args()

    if not Path(args.input_file).exists():
        print(f"Error: File not found: {args.input_file}")
        sys.exit(1)

    headers, detected_sheet = read_headers(args.input_file, args.sheet)
    display_headers(headers)

    print("Enter client details:")
    print("  Client name: ", end="")
    client_name = input().strip()
    print("  Program name: ", end="")
    program_name = input().strip()
    print(f"  Dollar value per referral [25.00]: ", end="")
    dollar_input = input().strip()
    dollar_value = float(dollar_input) if dollar_input else 25.00

    print("\nMap your columns to screener fields:")
    print("=" * 50)

    columns = {}

    for field, desc in REQUIRED_FIELDS.items():
        result = prompt_mapping(headers, field, desc, required=True)
        if result:
            columns[field] = result

    print()

    for field, desc in OPTIONAL_FIELDS.items():
        result = prompt_mapping(headers, field, desc, required=False)
        if result:
            columns[field] = result

    print(f"\n  Employee tracking column (separate column number, or Enter to skip): ", end="")
    emp_input = input().strip()
    emp_col = int(emp_input) if emp_input else None

    config = {
        "client": client_name,
        "program": program_name,
        "columns": columns,
        "dollar_value_per_referral": dollar_value,
    }

    if detected_sheet:
        config["sheet"] = detected_sheet
    if emp_col:
        config["employee_tracking_column"] = emp_col

    slug = client_name.lower().replace(" ", "-").replace("'", "")
    slug = "".join(c for c in slug if c.isalnum() or c == "-")
    output_path = Path("config") / f"{slug}.yaml"

    print(f"\n{'=' * 50}")
    print("Generated config:")
    print("-" * 50)
    yaml_output = yaml.dump(config, default_flow_style=False, sort_keys=False)
    print(yaml_output)

    print(f"Save to {output_path}? [Y/n]: ", end="")
    confirm = input().strip().lower()
    if confirm in ("", "y", "yes"):
        output_path.parent.mkdir(exist_ok=True)
        with open(output_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        print(f"Saved to {output_path}")
        print(f"\nRun the screener with:")
        print(f"  python screen.py {args.input_file} --config {output_path}")
    else:
        print("Not saved.")


if __name__ == "__main__":
    main()
