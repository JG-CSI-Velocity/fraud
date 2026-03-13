from collections import defaultdict

from .rules.base import Finding


def compute_scores(findings: list[Finding], config: dict) -> dict:
    rules_config = config.get("rules", {})
    scoring = config.get("scoring", {})

    referrer_scores = defaultdict(lambda: {"score": 0, "findings": [], "rules_hit": set()})
    manager_scores = defaultdict(lambda: {"score": 0, "findings": [], "rules_hit": set()})
    branch_scores = defaultdict(lambda: {"score": 0, "findings": [], "rules_hit": set()})

    for f in findings:
        weight = rules_config.get(
            _rule_to_config_key(f.rule_name), {}
        ).get("weight", 1)

        if f.referrer and " <-> " not in f.referrer and ", " not in f.referrer:
            referrer_scores[f.referrer]["score"] += weight
            referrer_scores[f.referrer]["findings"].append(f)
            referrer_scores[f.referrer]["rules_hit"].add(f.rule_name)

        if f.manager:
            for mgr in f.manager.split(", "):
                mgr = mgr.strip()
                if mgr:
                    manager_scores[mgr]["score"] += weight
                    manager_scores[mgr]["findings"].append(f)
                    manager_scores[mgr]["rules_hit"].add(f.rule_name)

        if f.branch:
            for br in f.branch.split(", "):
                br = br.strip()
                if br:
                    branch_scores[br]["score"] += weight
                    branch_scores[br]["findings"].append(f)
                    branch_scores[br]["rules_hit"].add(f.rule_name)

    return {
        "referrer": _apply_tiers(dict(referrer_scores), scoring),
        "manager": _apply_tiers(dict(manager_scores), scoring),
        "branch": _apply_tiers(dict(branch_scores), scoring),
    }


def _apply_tiers(scores: dict, scoring: dict) -> dict:
    critical = scoring.get("critical_risk", 50)
    high = scoring.get("high_risk", 25)
    medium = scoring.get("medium_risk", 10)

    for entity in scores:
        s = scores[entity]["score"]
        if s >= critical:
            scores[entity]["tier"] = "CRITICAL"
        elif s >= high:
            scores[entity]["tier"] = "HIGH"
        elif s >= medium:
            scores[entity]["tier"] = "MEDIUM"
        else:
            scores[entity]["tier"] = "LOW"

    return scores


def _rule_to_config_key(rule_name: str) -> str:
    return rule_name.lower().replace(" ", "_").replace("-", "_")
