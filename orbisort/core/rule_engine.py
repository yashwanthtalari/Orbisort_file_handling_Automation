import os
import yaml
from typing import Any, Dict, List, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RULE_FILE = os.path.join(BASE_DIR, "config", "rules.yaml")


def _normalize_extension(extension: Any) -> str:
    if extension is None:
        return ""

    if not isinstance(extension, str):
        extension = str(extension)

    ext = extension.strip().lower()

    if not ext:
        return ""

    if not ext.startswith("."):
        ext = f".{ext}"

    return ext


def load_rules() -> List[Dict[str, Any]]:
    if not os.path.exists(RULE_FILE):
        return []

    with open(RULE_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    rules = data.get("rules", [])
    if not isinstance(rules, list):
        return []

    return sorted(rules, key=lambda r: r.get("priority", 100))


def match_rule(extension: str, rules: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    extension = _normalize_extension(extension)

    for rule in rules:
        cond = rule.get("condition") or {}
        rule_ext = cond.get("extension")

        if isinstance(rule_ext, list):
            normalized = [_normalize_extension(item) for item in rule_ext]
            if extension in normalized:
                return rule

        elif isinstance(rule_ext, str):
            if extension == _normalize_extension(rule_ext):
                return rule

    return None
