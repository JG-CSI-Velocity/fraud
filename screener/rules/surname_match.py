from ..normalizer import normalize_name, extract_surname
from .base import Finding, Rule


class SurnameMatchRule(Rule):
    name = "Surname Match"
    config_key = "surname_match"

    def evaluate(self, records: list[dict]) -> list[Finding]:
        min_len = self.rule_config.get("min_surname_length", 3)

        findings = []
        for rec in records:
            ref = normalize_name(rec.get("referrer"))
            acct = normalize_name(rec.get("account_holder"))
            if not ref or not acct or " " not in ref or " " not in acct:
                continue

            ref_surname = extract_surname(ref)
            acct_surname = extract_surname(acct)

            if (
                ref_surname == acct_surname
                and len(ref_surname) >= min_len
                and ref != acct
            ):
                findings.append(Finding(
                    rule_name=self.name,
                    severity="low",
                    row_numbers=[rec["_source_row"]],
                    referrer=ref,
                    manager=normalize_name(rec.get("manager")),
                    branch=str(rec.get("branch_name", "")),
                    description=f"Referrer '{ref}' and account holder '{acct}' share surname '{ref_surname}'",
                    evidence={
                        "account_holder": acct,
                        "shared_surname": ref_surname,
                    },
                ))
        return findings
