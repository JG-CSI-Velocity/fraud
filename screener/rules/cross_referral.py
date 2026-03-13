from ..normalizer import normalize_name
from .base import Finding, Rule


class CrossReferralRule(Rule):
    name = "Cross-Referral"
    config_key = "cross_referral"

    def evaluate(self, records: list[dict]) -> list[Finding]:
        employees = set()
        for rec in records:
            mgr = normalize_name(rec.get("manager"))
            if mgr:
                employees.add(mgr)

        findings = []
        for rec in records:
            ref = normalize_name(rec.get("referrer"))
            mgr = normalize_name(rec.get("manager"))
            if ref and mgr and ref in employees and ref != mgr:
                findings.append(Finding(
                    rule_name=self.name,
                    severity="high",
                    row_numbers=[rec["_source_row"]],
                    referrer=ref,
                    manager=mgr,
                    branch=str(rec.get("branch_name", "")),
                    description=f"Employee '{ref}' referring under manager '{mgr}'",
                    evidence={
                        "account_holder": rec.get("account_holder"),
                        "referrer_is_manager_elsewhere": True,
                    },
                ))
        return findings
