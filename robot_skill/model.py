from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Finding:
    code: str
    message: str
    path: str
    severity: str = "error"

    def as_dict(self) -> dict[str, str]:
        return {
            "severity": self.severity,
            "code": self.code,
            "path": self.path,
            "message": self.message,
        }


@dataclass
class CheckResult:
    root: Path
    manifest: dict[str, Any]
    findings: list[Finding] = field(default_factory=list)
    detected_files: list[str] = field(default_factory=list)

    @property
    def errors(self) -> list[Finding]:
        return [finding for finding in self.findings if finding.severity == "error"]

    @property
    def warnings(self) -> list[Finding]:
        return [finding for finding in self.findings if finding.severity == "warning"]

    @property
    def complete(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": "complete" if self.complete else "incomplete",
            "root": str(self.root),
            "summary": {"errors": len(self.errors), "warnings": len(self.warnings)},
            "findings": [finding.as_dict() for finding in self.findings],
            "detected_files": self.detected_files,
            "manifest": self.manifest,
        }

