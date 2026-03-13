from collections import defaultdict

from ..normalizer import normalize_name
from .base import Finding, Rule


class ReciprocalPairRule(Rule):
    name = "Reciprocal Pair"
    config_key = "reciprocal_pair"

    def evaluate(self, records: list[dict]) -> list[Finding]:
        ref_to_accts = defaultdict(set)
        ref_rows = defaultdict(list)

        for rec in records:
            ref = normalize_name(rec.get("referrer"))
            acct = normalize_name(rec.get("account_holder"))
            if ref and acct:
                ref_to_accts[ref].add(acct)
                ref_rows[(ref, acct)].append(rec["_source_row"])

        findings = []
        seen = set()

        for a in ref_to_accts:
            for b in ref_to_accts[a]:
                if b in ref_to_accts and a in ref_to_accts[b] and a != b:
                    pair = tuple(sorted([a, b]))
                    if pair not in seen:
                        seen.add(pair)
                        rows_ab = ref_rows.get((a, b), [])
                        rows_ba = ref_rows.get((b, a), [])
                        findings.append(Finding(
                            rule_name=self.name,
                            severity="medium",
                            row_numbers=rows_ab + rows_ba,
                            referrer=f"{a} <-> {b}",
                            manager="",
                            branch="",
                            description=f"Reciprocal referral: '{a}' and '{b}' refer each other",
                            evidence={
                                "person_a": a,
                                "person_b": b,
                                "a_to_b_rows": rows_ab,
                                "b_to_a_rows": rows_ba,
                            },
                        ))

        return findings
