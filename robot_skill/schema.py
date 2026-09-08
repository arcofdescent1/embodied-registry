from __future__ import annotations

import json
from importlib.resources import files
from typing import Any

from jsonschema import Draft202012Validator

from .model import Finding


def load_schema() -> dict[str, Any]:
    resource = files("robot_skill").joinpath("robot-skill.schema.json")
    return json.loads(resource.read_text(encoding="utf-8"))


def validate_manifest(manifest: dict[str, Any]) -> list[Finding]:
    validator = Draft202012Validator(load_schema())
    findings: list[Finding] = []
    for error in sorted(validator.iter_errors(manifest), key=lambda item: list(item.absolute_path)):
        location = ".".join(str(part) for part in error.absolute_path) or "$"
        findings.append(Finding("schema.invalid", error.message, location))
    return findings

