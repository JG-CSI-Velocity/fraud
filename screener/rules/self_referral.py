from ..normalizer import normalize_name
from .base import Finding, Rule


class SelfReferralRule(Rule):
    name = "Self-Referral"
    config_key = "self_referral"

    def evaluate(self, records: list[dict]) -> list[Finding]:
        findings = []
        for rec in records:
            mgr = normalize_name(rec.get("manager"))
            ref = normalize_name(rec.get("referrer"))
            if mgr and ref and mgr == ref:
                findings.append(Finding(
                    rule_name=self.name,
                    severity="critical",
                    row_numbers=[rec["_source_row"]],
                    referrer=ref,
                    manager=mgr,
                    branch=str(rec.get("branch_name", "")),
                    description=f"Manager '{mgr}' listed as their own referrer",
                    evidence={"account_holder": rec.get("account_holder")},
                ))
        return findings
