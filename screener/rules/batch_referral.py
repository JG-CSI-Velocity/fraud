from collections import defaultdict

from ..normalizer import normalize_name
from .base import Finding, Rule


class BatchReferralRule(Rule):
    name = "Batch Referral"
    config_key = "batch_referral"

    def evaluate(self, records: list[dict]) -> list[Finding]:
        threshold = self.rule_config.get("threshold", 4)

        groups = defaultdict(list)
        for rec in records:
            ref = normalize_name(rec.get("referrer"))
            dt = rec.get("issue_date")
            if ref and dt:
                date_str = dt.strftime("%Y-%m-%d") if hasattr(dt, "strftime") else str(dt)[:10]
                groups[(ref, date_str)].append(rec)

        findings = []
        for (ref, date_str), recs in groups.items():
            if len(recs) >= threshold:
                rows = [r["_source_row"] for r in recs]
                accounts = [str(r.get("account_holder", "")) for r in recs]
                managers = list(set(normalize_name(r.get("manager")) for r in recs))
                findings.append(Finding(
                    rule_name=self.name,
                    severity="high" if len(recs) >= 10 else "medium",
                    row_numbers=rows,
                    referrer=ref,
                    manager=", ".join(managers),
                    branch=str(recs[0].get("branch_name", "")),
                    description=f"'{ref}' made {len(recs)} referrals on {date_str}",
                    evidence={
                        "date": date_str,
                        "count": len(recs),
                        "accounts": accounts[:10],
                        "managers": managers,
                    },
                ))
        return findings
