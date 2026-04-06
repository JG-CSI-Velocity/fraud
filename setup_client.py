#!/usr/bin/env python3
"""Standalone client YAML config generator.

Reads column headers from a client's Excel or CSV file, auto-detects
column mappings, and lets you confirm or adjust before saving.

For the full pipeline (config + screening in one step), use run.py instead.
"""

import argparse
import csv
import sys
from pathlib import Path

import openpyxl
import yaml

# Same auto-match keywords as run.py
AUTO_MATCH = {
    "manager": ["purchase manager", "manager", "employee", "staff", "rep name"],
    "account_holder": ["account holder", "account name", "new member", "member name", "customer"],
    "referrer": ["referrer", "referred by", "referral name", "referring"],
    "row_number": ["row", "#"],
    "branch_number": ["branch number", "branch num", "branch id", "branch #"],
    "branch_name": ["branch name", "branch"],
    "issue_date": ["issue date", "date", "created"],
    "certificate_id": ["certificate", "cert id", "tracking id", "cert"],
    "referral_code": ["referral code", "ref code", "code"],
    "program_name": ["program name", "program"],
    "product_count": ["product count", "products", "# products"],
}

REQUIRED_FIELDS = ["manager", "account_holder", "referrer"]

FIELD_DESCRIPTIONS = {
    "manager": "Employee/manager who owns the account",
    "account_holder": "Person who was referred (new member)",
    "referrer": "Person who made the referral",
    "row_number": "Row number or ID",
    "branch_number": "Branch ID or number",
    "branch_name": "Branch name",
    "issue_date": "Date the referral was issued",
    "certificate_id": "Certificate or tracking ID",
    "referral_code": "Referral code",
    "program_name": "Program name",
    "product_count": "Number of products opened",
}


def read_headers(file_path: str, sheet_name: str = None):
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


def auto_match_columns(headers: list[str]) -> dict[str, str]:
    matches = {}
    used_headers = set()
    header_lower = [(h or "").strip().lower() for h in headers]

    for field, patterns in AUTO_MATCH.items():
        for pattern in patterns:
            for i, h in enumerate(header_lower):
                if h and h not in used_headers and pattern in h:
                    matches[field] = headers[i]
                    used_headers.add(h)
                    break
            if field in matches:
                break

    return matches


def main():
    parser = argparse.ArgumentParser(
        description="Generate a client YAML config for the fraud screener"
    )
    parser.add_argument("input_file", help="Path to the client's Excel or CSV file")
    parser.add_argument("--sheet", help="Excel sheet name (defaults to active sheet)")
    parser.add_argument("--output", "-o", help="Output YAML path (default: config/<client>.yaml)")
    args = parser.parse_args()

    if not Path(args.input_file).exists():
        print(f"Error: File not found: {args.input_file}")
        sys.exit(1)

    headers, detected_sheet = read_headers(args.input_file, args.sheet)

    # Show columns
    print(f"\nColumns found in your file:")
    print("-" * 50)
    for i, h in enumerate(headers, 1):
        print(f"  {i:3d}. {h if h else '(empty)'}")

    # Auto-match
    matches = auto_match_columns(headers)

    # Show results
    print(f"\n{'=' * 50}")
    print("AUTO-DETECTED COLUMN MAPPING")
    print("=" * 50)

    all_fields = list(FIELD_DESCRIPTIONS.keys())
    unmatched_required = []

    for field in all_fields:
        req = field in REQUIRED_FIELDS
        tag = "REQUIRED" if req else "optional"
        if field in matches:
            print(f"  [{tag}] {field} -> \"{matches[field]}\"")
        elif req:
            print(f"  [{tag}] {field} -> NOT FOUND")
            unmatched_required.append(field)

    # Handle unmatched required fields
    if unmatched_required:
        print(f"\nManual mapping needed for: {', '.join(unmatched_required)}")
        for field in unmatched_required:
            desc = FIELD_DESCRIPTIONS[field]
            print(f"  {field} ({desc})")
            print(f"    Enter column number (1-{len(headers)}): ", end="")
            while True:
                choice = input().strip()
                try:
                    idx = int(choice)
                    if 1 <= idx <= len(headers):
                        matches[field] = headers[idx - 1]
                        print(f"    -> \"{headers[idx - 1]}\"")
                        break
                    else:
                        print(f"    Enter 1-{len(headers)}: ", end="")
                except ValueError:
                    print(f"    Enter a number: ", end="")

    # Confirm or fix
    print(f"\nAccept this mapping? [Y/n]: ", end="")
    choice = input().strip().lower()

    if choice in ("n", "no"):
        print("\nFix mappings (enter column number, or Enter to keep):")
        for field in all_fields:
            current = matches.get(field)
            req = field in REQUIRED_FIELDS
            tag = "REQUIRED" if req else "optional"
            current_display = f" (current: \"{current}\")" if current else " (not set)"
            print(f"  [{tag}] {field}{current_display}: ", end="")

            while True:
                val = input().strip()
                if not val:
                    break
                try:
                    idx = int(val)
                    if 1 <= idx <= len(headers):
                        matches[field] = headers[idx - 1]
                        print(f"    -> \"{headers[idx - 1]}\"")
                        break
                    else:
                        print(f"    Enter 1-{len(headers)} or Enter to keep: ", end="")
                except ValueError:
                    print(f"    Enter a number or Enter to keep: ", end="")

    # Client info
    print(f"\nClient name: ", end="")
    client_name = input().strip()
    print("Program name: ", end="")
    program_name = input().strip()
    print("Dollar value per referral [25.00]: ", end="")
    dollar_input = input().strip()
    dollar_value = float(dollar_input) if dollar_input else 25.00

    # Build config
    columns = {k: v for k, v in matches.items() if v}
    config = {
        "client": client_name,
        "program": program_name,
        "columns": columns,
        "dollar_value_per_referral": dollar_value,
    }
    if detected_sheet:
        config["sheet"] = detected_sheet

    # Output path
    if args.output:
        output_path = Path(args.output)
    else:
        slug = client_name.lower().replace(" ", "-").replace("'", "")
        slug = "".join(c for c in slug if c.isalnum() or c == "-")
        output_path = Path("config") / f"{slug}.yaml"

    # Final summary
    print(f"\n{'=' * 50}")
    print("FINAL CONFIG")
    print("=" * 50)
    print(f"  Client:     {client_name}")
    print(f"  Program:    {program_name}")
    print(f"  $/Referral: {dollar_value}")
    print(f"\n  Column mappings:")
    for field, header in columns.items():
        req = "*" if field in REQUIRED_FIELDS else " "
        print(f"   {req} {field:20s} -> \"{header}\"")
    print(f"\n  * = required")

    print(f"\nSave to {output_path}? [Y/n]: ", end="")
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
