from dataclasses import dataclass, field


@dataclass
class Finding:
    rule_name: str
    severity: str
    row_numbers: list[int]
    referrer: str = ""
    manager: str = ""
    branch: str = ""
    description: str = ""
    evidence: dict = field(default_factory=dict)


class Rule:
    name: str = ""
    config_key: str = ""

    def __init__(self, config: dict):
        rule_config = config.get("rules", {}).get(self.config_key, {})
        self.enabled = rule_config.get("enabled", True)
        self.weight = rule_config.get("weight", 1)
        self.rule_config = rule_config
        self.full_config = config

    def evaluate(self, records: list[dict]) -> list[Finding]:
        raise NotImplementedError
