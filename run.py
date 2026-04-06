#!/usr/bin/env python3
"""Full fraud screening pipeline.

Usage:
    python run.py clients/acme/          # new client, interactive setup
    python run.py clients/acme/ --rerun  # re-run with existing config

Workflow:
    1. Finds the Excel/CSV data file in the client folder
    2. If no YAML config exists, runs interactive column mapping
    3. Runs the fraud screener
    4. Saves the report to the client folder
"""

import argparse
import subprocess
import sys
from pathlib import Path

import yaml

SUPPORTED_EXTENSIONS = {".xlsx", ".xls", ".csv"}


def find_data_file(folder: Path) -> Path | None:
    candidates = [
        f for f in folder.iterdir()
        if f.is_file()
        and f.suffix.lower() in SUPPORTED_EXTENSIONS
        and "_fraud_report" not in f.stem.lower()
    ]
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]

    print("\nMultiple data files found:")
    for i, f in enumerate(candidates, 1):
        print(f"  {i}. {f.name}")
    print(f"  Select file (1-{len(candidates)}): ", end="")
    while True:
        choice = input().strip()
        try:
            idx = int(choice)
            if 1 <= idx <= len(candidates):
                return candidates[idx - 1]
        except ValueError:
            pass
        print(f"  Enter 1-{len(candidates)}: ", end="")


def find_config(folder: Path) -> Path | None:
    configs = [f for f in folder.iterdir() if f.suffix.lower() in (".yaml", ".yml")]
    if configs:
        return configs[0]
    return None


def create_config(data_file: Path, folder: Path) -> Path:
    """Interactive config creation, adapted from setup_client.py logic."""
    import csv
    import openpyxl

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

    # Read headers
    path = data_file
    sheet_name = None
    if path.suffix.lower() in (".xlsx", ".xls"):
        wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
        ws = wb.active
        sheet_name = ws.title
        headers = [cell.value for cell in next(ws.iter_rows(max_row=1))]
        sheets = wb.sheetnames
        wb.close()

        if len(sheets) > 1:
            print(f"\nSheets found: {', '.join(sheets)}")
            print(f"  Using: {sheet_name}")
            print(f"  Change sheet? Enter name or press Enter to keep: ", end="")
            choice = input().strip()
            if choice and choice in sheets:
                sheet_name = choice
                wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
                ws = wb[sheet_name]
                headers = [cell.value for cell in next(ws.iter_rows(max_row=1))]
                wb.close()
    else:
        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            headers = next(reader)

    # Display headers
    print(f"\nColumns in {data_file.name}:")
    print("-" * 50)
    for i, h in enumerate(headers, 1):
        print(f"  {i:3d}. {h if h else '(empty)'}")
    print()

    # Collect client info
    print("Client name: ", end="")
    client_name = input().strip()
    print("Program name: ", end="")
    program_name = input().strip()
    print("Dollar value per referral [25.00]: ", end="")
    dollar_input = input().strip()
    dollar_value = float(dollar_input) if dollar_input else 25.00

    # Map columns
    print("\nMap columns (enter column number, or Enter to skip):")
    print("=" * 50)
    columns = {}

    for field, desc in REQUIRED_FIELDS.items():
        print(f"  [REQUIRED] {field} ({desc}): ", end="")
        while True:
            choice = input().strip()
            if not choice:
                print(f"    Required. Enter a number: ", end="")
                continue
            try:
                idx = int(choice)
                if 1 <= idx <= len(headers):
                    columns[field] = headers[idx - 1]
                    print(f"    -> \"{headers[idx - 1]}\"")
                    break
                else:
                    print(f"    Enter 1-{len(headers)}: ", end="")
            except ValueError:
                print(f"    Enter a number: ", end="")

    for field, desc in OPTIONAL_FIELDS.items():
        print(f"  [optional] {field} ({desc}): ", end="")
        choice = input().strip()
        if choice:
            try:
                idx = int(choice)
                if 1 <= idx <= len(headers):
                    columns[field] = headers[idx - 1]
                    print(f"    -> \"{headers[idx - 1]}\"")
            except ValueError:
                pass

    print("  Employee tracking column (number, or Enter to skip): ", end="")
    emp_input = input().strip()
    emp_col = int(emp_input) if emp_input else None

    # Build config
    config = {
        "client": client_name,
        "program": program_name,
        "columns": columns,
        "dollar_value_per_referral": dollar_value,
    }
    if sheet_name:
        config["sheet"] = sheet_name
    if emp_col:
        config["employee_tracking_column"] = emp_col

    # Save
    config_path = folder / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    print(f"\nConfig saved to {config_path}")

    return config_path


def main():
    parser = argparse.ArgumentParser(description="Full fraud screening pipeline")
    parser.add_argument("folder", help="Path to client folder containing data file")
    parser.add_argument("--rerun", action="store_true", help="Re-run with existing config")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress screener progress")
    args = parser.parse_args()

    folder = Path(args.folder)
    if not folder.is_dir():
        print(f"Error: {folder} is not a directory")
        sys.exit(1)

    # Step 1: Find data file
    data_file = find_data_file(folder)
    if not data_file:
        print(f"Error: No Excel/CSV file found in {folder}")
        sys.exit(1)
    print(f"Data file: {data_file.name}")

    # Step 2: Find or create config
    config_path = find_config(folder)
    if config_path and not args.rerun:
        print(f"Config found: {config_path.name}")
        print(f"  Use existing config? [Y/n]: ", end="")
        choice = input().strip().lower()
        if choice in ("n", "no"):
            config_path = None

    if not config_path:
        config_path = create_config(data_file, folder)

    # Step 3: Run screener
    output_name = f"{data_file.stem}_fraud_report.xlsx"
    output_path = folder / output_name

    print(f"\nRunning fraud screener...")
    cmd = [
        sys.executable, "screen.py",
        str(data_file),
        "--config", str(config_path),
        "--output", str(output_path),
    ]
    if args.quiet:
        cmd.append("--quiet")

    result = subprocess.run(cmd, cwd=Path(__file__).parent)

    if result.returncode != 0:
        print(f"\nScreener failed with exit code {result.returncode}")
        sys.exit(result.returncode)

    print(f"\nReport saved to: {output_path}")


if __name__ == "__main__":
    main()
