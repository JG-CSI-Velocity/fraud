from collections import defaultdict

from ..normalizer import normalize_name
from .base import Finding, Rule


class RingDetectionRule(Rule):
    name = "Ring Detection"
    config_key = "ring_detection"

    def evaluate(self, records: list[dict]) -> list[Finding]:
        min_ring_size = self.rule_config.get("min_ring_size", 2)

        employees = set()
        for rec in records:
            mgr = normalize_name(rec.get("manager"))
            if mgr:
                employees.add(mgr)

        edges = defaultdict(set)
        edge_rows = defaultdict(list)

        for rec in records:
            ref = normalize_name(rec.get("referrer"))
            mgr = normalize_name(rec.get("manager"))
            if ref and mgr and ref in employees and ref != mgr:
                edges[ref].add(mgr)
                edge_rows[(ref, mgr)].append(rec["_source_row"])

        rings = []
        visited = set()

        for start in edges:
            if start in visited:
                continue
            component = set()
            stack = [start]
            while stack:
                node = stack.pop()
                if node in component:
                    continue
                component.add(node)
                for neighbor in edges.get(node, set()):
                    if neighbor not in component:
                        stack.append(neighbor)
                for other in edges:
                    if node in edges[other] and other not in component:
                        stack.append(other)

            if len(component) >= min_ring_size:
                mutual_pairs = []
                for a in component:
                    for b in edges.get(a, set()):
                        if b in component and a in edges.get(b, set()):
                            pair = tuple(sorted([a, b]))
                            if pair not in mutual_pairs:
                                mutual_pairs.append(pair)

                if mutual_pairs:
                    rings.append(component)
                    visited.update(component)

        findings = []
        for ring in rings:
            all_rows = []
            for a in ring:
                for b in edges.get(a, set()):
                    if b in ring:
                        all_rows.extend(edge_rows.get((a, b), []))

            members = sorted(ring)
            findings.append(Finding(
                rule_name=self.name,
                severity="critical",
                row_numbers=all_rows[:30],
                referrer=", ".join(members),
                manager="",
                branch="",
                description=f"Employee referral ring detected: {', '.join(members)} ({len(members)} members)",
                evidence={
                    "members": members,
                    "size": len(members),
                },
            ))

        return findings
