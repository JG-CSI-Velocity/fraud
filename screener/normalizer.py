import re

from rapidfuzz import fuzz


def normalize_name(name) -> str:
    if not name:
        return ""
    s = str(name).strip().upper()
    s = re.sub(r"\s+", " ", s)
    return s


def extract_surname(name: str) -> str:
    normalized = normalize_name(name)
    parts = normalized.split()
    return parts[-1] if parts else ""


def names_match(a, b, threshold: float = 0.85) -> bool:
    na = normalize_name(a)
    nb = normalize_name(b)
    if not na or not nb:
        return False
    if na == nb:
        return True
    score = fuzz.token_sort_ratio(na, nb) / 100.0
    return score >= threshold


def detect_name_variants(names: list[str], threshold: float = 0.75) -> list[list[str]]:
    normalized = [normalize_name(n) for n in names if n]
    unique = list(set(normalized))
    unique.sort()

    clusters = []
    assigned = set()

    for i, name_a in enumerate(unique):
        if name_a in assigned:
            continue
        cluster = [name_a]
        assigned.add(name_a)
        surname_a = extract_surname(name_a)

        for j in range(i + 1, len(unique)):
            name_b = unique[j]
            if name_b in assigned:
                continue
            surname_b = extract_surname(name_b)
            if surname_a != surname_b:
                continue
            score = fuzz.token_sort_ratio(name_a, name_b) / 100.0
            if score >= threshold:
                cluster.append(name_b)
                assigned.add(name_b)

        if len(cluster) > 1:
            clusters.append(cluster)

    return clusters


def is_single_name(name: str) -> bool:
    normalized = normalize_name(name)
    return bool(normalized) and " " not in normalized and len(normalized) > 1


def is_email(name: str) -> bool:
    return "@" in str(name or "")


def is_number_only(name: str) -> bool:
    s = str(name or "").strip().replace("-", "")
    return bool(s) and s.isdigit() and len(s) > 3


def is_concatenated_name(name: str) -> bool:
    normalized = normalize_name(name)
    return bool(normalized) and " " not in normalized and len(normalized) > 15


def is_business_name(name: str, keywords: list[str]) -> bool:
    normalized = normalize_name(name)
    return any(kw in normalized for kw in keywords)
