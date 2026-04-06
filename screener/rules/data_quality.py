from ..normalizer import (
    is_business_name,
    is_concatenated_name,
    is_email,
    is_number_only,
    is_single_name,
    normalize_name,
)
from .base import Finding, Rule


class DataQualityRule(Rule):
    name = "Data Quality"
    config_key = "data_quality"

    def evaluate(self, records: list[dict]) -> list[Finding]:
        checks = self.rule_config.get("checks", {})
        biz_keywords = checks.get("business_name_keywords", [])

        findings = []
        for rec in records:
            acct = rec.get("account_holder")
            acct_str = str(acct or "").strip()
            if not acct_str:
                continue

            issues = []

            if checks.get("single_name") and is_single_name(acct_str):
                issues.append("single_name")

            if checks.get("email_as_name") and is_email(acct_str):
                issues.append("email_as_name")

            if checks.get("number_as_name") and is_number_only(acct_str):
                issues.append("number_as_name")

            if checks.get("concatenated_name") and is_concatenated_name(acct_str):
                issues.append("concatenated_name")

            if biz_keywords and is_business_name(acct_str, biz_keywords):
                issues.append("business_name")

            if issues:
                findings.append(Finding(
                    rule_name=self.name,
                    severity="medium" if len(issues) > 1 else "low",
                    row_numbers=[rec["_source_row"]],
                    referrer=normalize_name(rec.get("referrer")),
                    manager=normalize_name(rec.get("manager")),
                    branch=str(rec.get("branch_name", "")),
                    description=f"Data quality issue in '{acct_str}': {', '.join(issues)}",
                    evidence={
                        "account_holder": acct_str,
                        "issues": issues,
                    },
                ))

        return findings
