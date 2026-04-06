from collections import defaultdict

from ..normalizer import normalize_name, names_match
from .base import Finding, Rule


class DuplicateAccountRule(Rule):
    name = "Duplicate Account"
    config_key = "duplicate_account"

    def evaluate(self, records: list[dict]) -> list[Finding]:
        threshold = self.rule_config.get("similarity_threshold", 0.85)

        by_name = defaultdict(list)
        for rec in records:
            acct = normalize_name(rec.get("account_holder"))
            if acct:
                by_name[acct].append(rec)

        findings = []
        seen_exact = set()

        for acct_name, recs in by_name.items():
            if len(recs) > 1 and acct_name not in seen_exact:
                seen_exact.add(acct_name)
                rows = [r["_source_row"] for r in recs]
                referrers = [normalize_name(r.get("referrer")) for r in recs]
                findings.append(Finding(
                    rule_name=self.name,
                    severity="high" if len(recs) >= 3 else "medium",
                    row_numbers=rows,
                    referrer=", ".join(set(referrers)),
                    manager=normalize_name(recs[0].get("manager")),
                    branch=str(recs[0].get("branch_name", "")),
                    description=f"'{acct_name}' referred {len(recs)} times",
                    evidence={
                        "count": len(recs),
                        "referrers": list(set(referrers)),
                    },
                ))

        return findings
