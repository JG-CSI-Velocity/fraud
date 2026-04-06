# Referral Fraud Screening Tool

A command-line tool that screens referral program data for fraud patterns. It reads an Excel or CSV file, runs configurable detection rules, scores entities by risk, and outputs a detailed Excel report.

No APIs, no cloud services, no internet required. Runs entirely offline.

## Requirements

- Python 3.10+
- pip packages: `openpyxl`, `pyyaml`, `rapidfuzz`

## Installation

```cmd
git clone https://github.com/JG-CSI-Velocity/fraud.git
cd fraud
pip install openpyxl pyyaml rapidfuzz
```

## Quick Start (Full Pipeline)

The easiest way to run the tool is the pipeline runner. Create a folder for your client, drop in the data file, and run:

**Windows (Command Prompt):**

```cmd
mkdir clients\acme
copy "C:\path\to\referral-data.xlsx" clients\acme\
python run.py clients\acme\
```

**Mac/Linux:**

```bash
mkdir -p clients/acme
cp /path/to/referral-data.xlsx clients/acme/
python run.py clients/acme/
```

The pipeline will:
1. Find the Excel/CSV file in the folder
2. Show you the column headers and walk you through mapping them
3. Save a `config.yaml` in the client folder
4. Run the screener and save the report in the same folder

To re-run later with the same config:

```cmd
python run.py clients\acme\ --rerun
```

### Standalone Config Generator

To create a config file without running the screener:

```bash
python setup_client.py /path/to/data.xlsx
```

### Direct Screener Usage

```bash
python screen.py <input_file> --config <config_file> [--output <output_file>] [--quiet]
```

| Argument | Required | Description |
|----------|----------|-------------|
| `input_file` | Yes | Path to Excel (.xlsx) or CSV file containing referral data |
| `--config, -c` | Yes | Path to client YAML config file |
| `--output, -o` | No | Output report path (defaults to `<input>_fraud_report.xlsx`) |
| `--quiet, -q` | No | Suppress progress output |

```bash
python screen.py referrals.xlsx --config config/acme.yaml
```

## Configuration

Each client needs a YAML config file that maps your data columns to the tool's expected fields. Use `config/default.yaml` for rule settings and scoring thresholds.

### Client Config Example

Create a file like `config/acme.yaml`:

```yaml
client: "Acme Credit Union"
program: "Referral Rewards"

columns:
  row_number: "#"
  branch_number: "Branch Number"
  branch_name: "Branch Name"
  manager: "Manager Name"
  account_holder: "Account Holder"
  referrer: "Referrer Name"
  issue_date: "Issue Date"
  certificate_id: "Certificate ID"
  referral_code: "Referral Code"
  program_name: "Program Name"
  product_count: "Product Count"

sheet: "Sheet1"
dollar_value_per_referral: 25.00
```

The `columns` section maps canonical field names to the actual column headers in your spreadsheet. Adjust these to match your data.

Optional fields:
- `sheet` -- name of the Excel sheet to read (defaults to the active sheet)
- `employee_tracking_column` -- 1-based column number if employee IDs are tracked separately
- `points_per_referral` -- points value per referral (informational)
- `dollar_value_per_referral` -- dollar value used to estimate exposure

### Default Config

`config/default.yaml` controls which rules are enabled, their weights, and scoring thresholds. You can override any rule setting in your client config.

## Detection Rules

| Rule | What It Detects |
|------|----------------|
| Self Referral | Manager listed as their own referrer |
| Cross Referral | Employee referring under another employee's management |
| Batch Referral | Same referrer, same day, high volume (threshold: 4+) |
| Surname Match | Referrer and account holder share a last name |
| Duplicate Account | Same account holder referred multiple times |
| Missing Code | Missing or placeholder referral codes |
| Name Variant | Same person using name variants as referrer |
| Reciprocal Pair | A refers B and B refers A |
| Employee as Account | Employee appearing as an account holder |
| Data Quality | Fabricated entries (single names, emails as names, business names) |
| Ring Detection | Multi-employee referral rings |

## Risk Scoring

Each finding is weighted by its rule. Scores are aggregated per referrer, manager, and branch, then tiered:

| Tier | Score Threshold |
|------|----------------|
| LOW | 0 - 9 |
| MEDIUM | 10 - 24 |
| HIGH | 25 - 49 |
| CRITICAL | 50+ |

Thresholds are configurable in `config/default.yaml` under `scoring`.

## Output

The tool generates an Excel report with:
- All findings with rule name, severity, evidence, and source row numbers
- Risk scores per referrer, manager, and branch
- Summary statistics and estimated dollar exposure

## Project Structure

```
fraud/
  run.py                 # Full pipeline runner (recommended)
  setup_client.py        # Standalone config generator
  screen.py              # Screener CLI
  config/
    default.yaml         # Default rules and scoring config
  clients/               # Client folders (gitignored)
    acme/
      data.xlsx          # Client data file
      config.yaml        # Generated config
      data_fraud_report.xlsx  # Output report
  screener/
    __init__.py
    loader.py            # Excel/CSV loading and column mapping
    normalizer.py        # Name normalization and fuzzy matching
    scorer.py            # Risk scoring and tier assignment
    reporter.py          # Excel report generation
    rules/
      __init__.py        # Rule registry
      base.py            # Rule and Finding base classes
      self_referral.py
      cross_referral.py
      batch_referral.py
      surname_match.py
      duplicate_account.py
      missing_code.py
      name_variant.py
      reciprocal_pair.py
      employee_as_account.py
      data_quality.py
      ring_detection.py
```
