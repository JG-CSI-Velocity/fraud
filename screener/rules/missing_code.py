from collections import defaultdict

from ..normalizer import normalize_name
from .base import Finding, Rule


class MissingCodeRule(Rule):
    name = "Missing Code"
    config_key = "missing_code"

    def evaluate(self, records: list[dict]) -> list[Finding]:
        none_values = self.rule_config.get("none_values", ["NONE", "none", ""])
        mgr_threshold = self.rule_config.get("manager_threshold", 0.80)

        mgr_totals = defaultdict(int)
        mgr_missing = defaultdict(int)
        mgr_rows = defaultdict(list)

        for rec in records:
            mgr = normalize_name(rec.get("manager"))
            code = str(rec.get("referral_code") or "").strip()
            if mgr:
                mgr_totals[mgr] += 1
                if code in none_values or not code:
                    mgr_missing[mgr] += 1
                    mgr_rows[mgr].append(rec["_source_row"])

        findings = []
        for mgr in mgr_totals:
            total = mgr_totals[mgr]
            missing = mgr_missing.get(mgr, 0)
            if total > 0 and missing / total >= mgr_threshold:
                rate = missing / total
                findings.append(Finding(
                    rule_name=self.name,
                    severity="medium" if rate < 0.95 else "high",
                    row_numbers=mgr_rows.get(mgr, [])[:20],
                    referrer="",
                    manager=mgr,
                    branch="",
                    description=f"Manager '{mgr}' has {missing}/{total} ({rate:.0%}) missing referral codes",
                    evidence={
                        "total_referrals": total,
                        "missing_codes": missing,
                        "rate": round(rate, 3),
                    },
                ))

        return findings
