#!/usr/bin/env python3
"""Referral Fraud Screening Tool - CLI Entry Point."""

import argparse
import sys
import time
from pathlib import Path

from screener.loader import load_config, load_records
from screener.reporter import generate_report
from screener.rules import ALL_RULES
from screener.scorer import compute_scores


def main():
    parser = argparse.ArgumentParser(
        description="Screen referral program data for fraud patterns"
    )
    parser.add_argument("input_file", help="Path to Excel (.xlsx) or CSV file")
    parser.add_argument(
        "--config", "-c",
        required=True,
        help="Path to client YAML config file",
    )
    parser.add_argument(
        "--output", "-o",
        help="Output report path (default: <input>_fraud_report.xlsx)",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress progress output",
    )
    args = parser.parse_args()

    if not args.output:
        stem = Path(args.input_file).stem
        args.output = f"{stem}_fraud_report.xlsx"

    start = time.time()

    if not args.quiet:
        print(f"Loading config: {args.config}")
    config = load_config(args.config)

    if not args.quiet:
        print(f"Loading data: {args.input_file}")
    records = load_records(args.input_file, config)
    if not args.quiet:
        print(f"  {len(records)} records loaded")

    all_findings = []
    for rule_cls in ALL_RULES:
        rule = rule_cls(config)
        if not rule.enabled:
            continue
        if not args.quiet:
            print(f"  Running: {rule.name}...", end=" ")
        findings = rule.evaluate(records)
        all_findings.extend(findings)
        if not args.quiet:
            print(f"{len(findings)} findings")

    if not args.quiet:
        print(f"\nScoring {len(all_findings)} total findings...")
    scores = compute_scores(all_findings, config)

    if not args.quiet:
        print(f"Generating report: {args.output}")
    generate_report(all_findings, scores, config, records, args.output)

    elapsed = time.time() - start

    flagged_rows = set()
    for f in all_findings:
        flagged_rows.update(f.row_numbers)

    dollar = config.get("dollar_value_per_referral", 25)

    print(f"\n{'='*50}")
    print(f"SCREENING COMPLETE")
    print(f"{'='*50}")
    print(f"  Records screened:  {len(records)}")
    print(f"  Total findings:    {len(all_findings)}")
    print(f"  Unique rows flagged: {len(flagged_rows)}")
    print(f"  Estimated exposure:  ${len(flagged_rows) * dollar:,.0f}")
    print(f"  Time elapsed:      {elapsed:.1f}s")
    print(f"  Report saved to:   {args.output}")

    ref_scores = scores.get("referrer", {})
    critical = [(r, d) for r, d in ref_scores.items() if d["tier"] == "CRITICAL"]
    high = [(r, d) for r, d in ref_scores.items() if d["tier"] == "HIGH"]

    if critical:
        print(f"\n  CRITICAL risk referrers: {len(critical)}")
        for ref, data in sorted(critical, key=lambda x: -x[1]["score"])[:10]:
            print(f"    {ref}: score={data['score']}, rules={', '.join(sorted(data['rules_hit']))}")

    if high:
        print(f"\n  HIGH risk referrers: {len(high)}")
        for ref, data in sorted(high, key=lambda x: -x[1]["score"])[:10]:
            print(f"    {ref}: score={data['score']}")


if __name__ == "__main__":
    main()
