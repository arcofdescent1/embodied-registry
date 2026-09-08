from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any, Iterable

import yaml

from .model import CheckResult, Finding
from .schema import validate_manifest

MANIFEST_NAMES = ("robot-skill.yaml", "robot-skill.yml", "robot-skill.json")
CONFIG_NAMES = (
    "config.json", "policy_config.json", "train_config.json", "dataset_info.json",
    "meta/info.json", "configs/policy.json",
)
DEPENDENCY_NAMES = ("pyproject.toml", "requirements.txt", "environment.yml", "environment.yaml", "poetry.lock", "uv.lock")
FRAMEWORK_MARKERS = {
    "lerobot": ("lerobot", "policy.type", "robot.type"),
    "robomimic": ("robomimic",),
    "diffusion-policy": ("diffusion_policy", "diffusion policy"),
    "ros2": ("rclpy", "ament_python", "ros2"),
}
ARCHITECTURES = ("smolvla", "act", "diffusion", "pi0", "tdmpc", "vqbet", "sac", "td3", "ppo")


def _read_text(path: Path, limit: int = 1_000_000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:limit]
    except OSError:
        return ""


def _nested(data: Any, paths: Iterable[str]) -> Any:
    for dotted in paths:
        value = data
        for part in dotted.split("."):
            if not isinstance(value, dict) or part not in value:
                value = None
                break
            value = value[part]
        if value is not None:
            return value
    return None


def _load_existing(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(_read_text(path)) if path.suffix == ".json" else yaml.safe_load(_read_text(path))
    except (json.JSONDecodeError, yaml.YAMLError) as exc:
        raise ValueError(f"could not parse {path.name}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path.name} must contain a mapping at its root")
    return data


def _git_value(root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args], capture_output=True, text=True, timeout=3, check=False
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    value = result.stdout.strip()
    return value if result.returncode == 0 and value else None


def _repository_type(url: str | None) -> str:
    if url and "huggingface.co" in url:
        return "huggingface"
    if url and "github.com" in url:
        return "github"
    return "local"


def _scan_documents(root: Path) -> tuple[str, list[str]]:
    candidates = [root / "README.md", root / "MODEL_CARD.md", root / "config.json"]
    detected = [str(path.relative_to(root)).replace("\\", "/") for path in candidates if path.is_file()]
    return "\n".join(_read_text(path) for path in candidates if path.is_file()), detected


def _find_number(text: str, patterns: Iterable[str]) -> float | int | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            value = float(match.group(1))
            return int(value) if value.is_integer() else value
    return None


def _first_string(data: dict[str, Any], paths: Iterable[str]) -> str | None:
    value = _nested(data, paths)
    return str(value) if isinstance(value, (str, int, float)) else None


def _infer(root: Path) -> tuple[dict[str, Any], list[str]]:
    text, detected = _scan_documents(root)
    configs: list[dict[str, Any]] = []
    for name in CONFIG_NAMES:
        path = root / name
        if not path.is_file():
            continue
        detected.append(name)
        try:
            value = json.loads(_read_text(path))
            if isinstance(value, dict):
                configs.append(value)
        except json.JSONDecodeError:
            pass
    combined = "\n".join([text, *(json.dumps(item) for item in configs)]).lower()
    config: dict[str, Any] = {}
    for item in configs:
        config.update(item)

    framework = next((name for name, markers in FRAMEWORK_MARKERS.items() if any(marker in combined for marker in markers)), None)
    architecture = _first_string(config, ("policy.type", "policy_type", "architecture", "model_type"))
    if not architecture:
        architecture = next((name for name in ARCHITECTURES if re.search(rf"\b{re.escape(name)}\b", combined)), None)
    robot = _first_string(config, ("robot.type", "robot_type", "robot", "hardware.robot_family"))
    dataset = _first_string(config, ("dataset.repo_id", "dataset_repo_id", "dataset.name", "dataset"))
    fps = _nested(config, ("fps", "dataset.fps", "control_frequency_hz", "control.frequency"))
    if not isinstance(fps, (int, float)):
        fps = _find_number(combined, (r"(?:control frequency|frequency|fps)\D{0,12}(\d+(?:\.\d+)?)\s*(?:hz|fps)",))

    dependencies = [name for name in DEPENDENCY_NAMES if (root / name).is_file()]
    detected.extend(dependencies)
    remote = _git_value(root, "config", "--get", "remote.origin.url")
    revision = _git_value(root, "rev-parse", "HEAD")
    sensors: list[dict[str, Any]] = []
    sensor_text = combined
    for sensor_type in ("rgb", "depth", "joint-position", "force-torque", "imu"):
        if sensor_type.replace("-", " ") in sensor_text or sensor_type in sensor_text:
            sensors.append({"type": sensor_type})

    manifest: dict[str, Any] = {
        "schema_version": "1.0",
        "skill": {
            "name": root.name.replace("_", " ").replace("-", " ").strip().title(),
            "version": None,
            "source": {"type": _repository_type(remote), "repository": remote, "revision": revision},
        },
        "policy": {"framework": framework, "framework_version": None, "architecture": architecture},
        "hardware": {"robot_family": robot, "gripper": None, "sensors": sensors},
        "runtime": {
            "control_frequency_hz": fps,
            "observation_shape": _nested(config, ("observation_shape", "input_shapes", "policy.input_features")),
            "action_shape": _nested(config, ("action_shape", "output_shape", "policy.output_features")),
            "dependencies": dependencies,
        },
        "dataset": {"repository": dataset, "schema": _nested(config, ("dataset.features", "features", "dataset_schema"))},
        "compatibility": [],
        "evaluations": [],
    }
    return manifest, sorted(set(detected))


REQUIRED_EVIDENCE = {
    "skill.version": "Declare the policy or artifact version.",
    "skill.source.repository": "Record the GitHub, Hugging Face, OCI, or local source identifier.",
    "skill.source.revision": "Pin an immutable commit or artifact revision.",
    "policy.framework": "Declare the policy framework.",
    "policy.framework_version": "Pin the framework version.",
    "policy.architecture": "Declare the policy architecture.",
    "hardware.robot_family": "Declare the robot family used or targeted.",
    "hardware.gripper": "Declare the end effector or gripper.",
    "hardware.sensors": "Describe every required sensor and its role.",
    "runtime.control_frequency_hz": "Declare the required control frequency in hertz.",
    "runtime.observation_shape": "Declare observation names, types, and shapes.",
    "runtime.action_shape": "Declare action names, types, and shapes.",
    "runtime.dependencies": "Provide a dependency lockfile or dependency declaration.",
    "dataset.repository": "Identify the training or evaluation dataset.",
    "dataset.schema": "Describe the dataset feature schema.",
}


def _missing(manifest: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    for path, message in REQUIRED_EVIDENCE.items():
        value = _nested(manifest, (path,))
        if value is None or value == "" or value == [] or value == {}:
            findings.append(Finding("metadata.missing", message, path))
    if not manifest.get("evaluations"):
        findings.append(Finding("evidence.absent", "No evaluation result is recorded; compatibility remains unverified.", "evaluations", "warning"))
    if not manifest.get("compatibility"):
        findings.append(Finding("compatibility.absent", "No known compatible or incompatible configuration is recorded.", "compatibility", "warning"))
    return findings


def inspect_policy(root: Path) -> CheckResult:
    root = root.expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"policy path is not a directory: {root}")
    existing = next((root / name for name in MANIFEST_NAMES if (root / name).is_file()), None)
    if existing:
        manifest = _load_existing(existing)
        detected = [existing.name]
    else:
        manifest, detected = _infer(root)
    findings = validate_manifest(manifest)
    if not findings:
        findings.extend(_missing(manifest))
    return CheckResult(root=root, manifest=manifest, findings=findings, detected_files=detected)

