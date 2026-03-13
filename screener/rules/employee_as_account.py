from ..normalizer import normalize_name
from .base import Finding, Rule


class EmployeeAsAccountRule(Rule):
    name = "Employee as Account"
    config_key = "employee_as_account"

    def evaluate(self, records: list[dict]) -> list[Finding]:
        employees = set()
        for rec in records:
            mgr = normalize_name(rec.get("manager"))
            if mgr:
                employees.add(mgr)

        findings = []
        for rec in records:
            acct = normalize_name(rec.get("account_holder"))
            if acct and acct in employees:
                ref = normalize_name(rec.get("referrer"))
                mgr = normalize_name(rec.get("manager"))
                findings.append(Finding(
                    rule_name=self.name,
                    severity="critical",
                    row_numbers=[rec["_source_row"]],
                    referrer=ref,
                    manager=mgr,
                    branch=str(rec.get("branch_name", "")),
                    description=f"Employee '{acct}' referred as account holder by '{ref}'",
                    evidence={
                        "employee_account_holder": acct,
                        "referred_by": ref,
                        "managed_by": mgr,
                    },
                ))

        return findings
