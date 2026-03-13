from collections import defaultdict

from ..normalizer import normalize_name, detect_name_variants
from .base import Finding, Rule


class NameVariantRule(Rule):
    name = "Name Variant"
    config_key = "name_variant"

    def evaluate(self, records: list[dict]) -> list[Finding]:
        threshold = self.rule_config.get("similarity_threshold", 0.75)

        referrer_names = []
        referrer_rows = defaultdict(list)
        for rec in records:
            ref = normalize_name(rec.get("referrer"))
            if ref:
                referrer_names.append(ref)
                referrer_rows[ref].append(rec["_source_row"])

        clusters = detect_name_variants(referrer_names, threshold)

        findings = []
        for cluster in clusters:
            all_rows = []
            total_refs = 0
            for variant in cluster:
                rows = referrer_rows.get(variant, [])
                all_rows.extend(rows)
                total_refs += len(rows)

            findings.append(Finding(
                rule_name=self.name,
                severity="high",
                row_numbers=all_rows[:20],
                referrer=cluster[0],
                manager="",
                branch="",
                description=f"Name variants detected: {', '.join(cluster)} ({total_refs} total referrals)",
                evidence={
                    "variants": cluster,
                    "total_referrals": total_refs,
                    "per_variant": {v: len(referrer_rows.get(v, [])) for v in cluster},
                },
            ))

        return findings
