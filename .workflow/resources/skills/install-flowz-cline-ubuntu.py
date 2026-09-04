#!/usr/bin/env python3
"""Install FlowZ's Cline rule and Skills on Ubuntu/Linux.

The installer uses only Python's standard library so a normal Ubuntu Python 3
installation is enough. It never overwrites a differing same-name rule or
Skill directory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import List, Union


def full_path(value: Union[str, Path]) -> Path:
    return Path(value).expanduser().resolve()


def is_within(root: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(root)
        return True
    except ValueError:
        return False


def assert_within(root: Path, candidate: Path) -> None:
    if not is_within(root, candidate):
        raise RuntimeError(f"Path escapes the allowed root: {candidate}")


def assert_safe_override(path: Path) -> Path:
    resolved = full_path(path)
    root = Path(resolved.anchor)
    home = full_path(Path.home())
    if resolved == root or resolved == home:
        raise RuntimeError(f"Refusing to use a filesystem or home root as an override: {resolved}")
    return resolved


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def names(items: List[str]) -> str:
    return ", ".join(items) if items else "none"


def copy_verified(
    source: Path,
    destination: Path,
    expected_hash: str,
    label: str,
    installed: List[str],
    skipped: List[str],
    conflicts: List[str],
) -> None:
    if destination.exists():
        if destination.is_file() and sha256(destination) == expected_hash:
            skipped.append(label)
            return
        conflicts.append(label)
        return

    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    if sha256(destination) != expected_hash:
        raise RuntimeError(f"File '{label}' failed destination hash verification.")
    installed.append(label)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install FlowZ globally for Cline on Ubuntu/Linux.")
    parser.add_argument("--project-root", default=None)
    parser.add_argument("--skill", action="append", default=[])
    parser.add_argument("--include-optional", action="store_true")
    parser.add_argument("--target-directory", default=None)
    parser.add_argument("--rules-target-directory", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project = full_path(args.project_root) if args.project_root else full_path(Path(__file__).parents[3])
    manifest_path = project / ".workflow" / "resources" / "skills" / "manifest.json"
    if not manifest_path.is_file():
        raise RuntimeError(f"Manifest not found: {manifest_path}")

    manifest_directory = manifest_path.parent
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    resource_base = full_path(manifest_directory / manifest["resourceRoot"])
    cline = manifest["installation"]["cline"]

    requested = [name.strip() for name in args.skill if name and name.strip()]
    all_entries = manifest["skills"]
    unsupported = [
        entry["name"]
        for entry in all_entries
        if entry["name"] in requested and entry.get("hosts", {}).get("cline", {}).get("installable") is False
    ]
    if unsupported:
        raise RuntimeError(
            "The following Skill entries are not installable for Cline: " + ", ".join(unsupported)
        )

    if args.include_optional and not requested:
        entries = [
            entry
            for entry in all_entries
            if entry.get("hosts", {}).get("cline", {}).get("installable") is not False
        ]
    else:
        entries = [
            entry
            for entry in all_entries
            if (not requested and entry.get("hosts", {}).get("cline", {}).get("default") is True)
            or entry["name"] in requested
        ]
    if not entries:
        raise RuntimeError("No matching Cline Skill entries were found in the manifest.")

    target = assert_safe_override(args.target_directory) if args.target_directory else full_path(Path.home() / ".cline" / "skills")
    rules_target = (
        assert_safe_override(args.rules_target_directory)
        if args.rules_target_directory
        else full_path(Path.home() / ".cline" / "rules")
    )
    home = full_path(Path.home())
    if not args.target_directory:
        assert_within(home, target)
    if not args.rules_target_directory:
        assert_within(home, rules_target)
    target.mkdir(parents=True, exist_ok=True)
    rules_target.mkdir(parents=True, exist_ok=True)

    installed_rules: List[str] = []
    skipped_rules: List[str] = []
    rule_conflicts: List[str] = []
    installed_skills: List[str] = []
    skipped_skills: List[str] = []
    skill_conflicts: List[str] = []

    for rule in cline.get("globalRules", []):
        source = full_path(manifest_directory / rule["sourcePath"])
        assert_within(manifest_directory.parent, source)
        if not source.is_file():
            raise RuntimeError(f"Global rule '{rule['name']}' is missing its source file: {source}")
        if sha256(source) != rule["sha256"]:
            raise RuntimeError(f"Global rule '{rule['name']}' failed source hash verification.")
        destination = rules_target / rule["installFile"]
        assert_within(rules_target, destination)
        copy_verified(
            source, destination, rule["sha256"], rule["name"], installed_rules, skipped_rules, rule_conflicts
        )

    for entry in entries:
        relative_source = entry["sourcePath"]
        if relative_source.startswith("sources/"):
            relative_source = relative_source[len("sources/") :]
        source_dir = full_path(resource_base / relative_source)
        assert_within(resource_base, source_dir)
        source_skill = source_dir / entry["skillFile"]
        if not source_skill.is_file():
            raise RuntimeError(f"Skill entry '{entry['name']}' is missing its source file: {source_skill}")
        if sha256(source_skill) != entry["skillSha256"]:
            raise RuntimeError(f"Skill entry '{entry['name']}' failed source hash verification.")

        destination_dir = target / entry["name"]
        assert_within(target, destination_dir)
        if destination_dir.exists():
            if not destination_dir.is_dir():
                skill_conflicts.append(entry["name"])
                continue
            all_match = True
            for relative_file in entry["installFiles"]:
                source_file = source_dir / relative_file
                destination_file = destination_dir / relative_file
                assert_within(source_dir, source_file)
                assert_within(destination_dir, destination_file)
                if not source_file.is_file() or not destination_file.is_file():
                    all_match = False
                    break
                expected = entry["skillSha256"] if relative_file == entry["skillFile"] else sha256(source_file)
                if sha256(destination_file) != expected:
                    all_match = False
                    break
            (skipped_skills if all_match else skill_conflicts).append(entry["name"])
            continue

        destination_dir.mkdir(parents=True, exist_ok=True)
        for relative_file in entry["installFiles"]:
            source_file = source_dir / relative_file
            destination_file = destination_dir / relative_file
            assert_within(source_dir, source_file)
            assert_within(destination_dir, destination_file)
            if not source_file.is_file():
                raise RuntimeError(f"Skill entry '{entry['name']}' is missing install file: {source_file}")
            expected = entry["skillSha256"] if relative_file == entry["skillFile"] else sha256(source_file)
            destination_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source_file, destination_file)
            if sha256(destination_file) != expected:
                raise RuntimeError(f"Skill entry '{entry['name']}' failed destination hash verification.")
        installed_skills.append(entry["name"])

    print(f"Cline rules target: {rules_target}")
    print(f"Rules installed: {names(installed_rules)}")
    print(f"Rules already matching: {names(skipped_rules)}")
    print(f"Cline Skill target: {target}")
    print(f"Skills installed: {names(installed_skills)}")
    print(f"Skills already matching: {names(skipped_skills)}")
    conflicts = [f"rule:{name}" for name in rule_conflicts] + [f"skill:{name}" for name in skill_conflicts]
    if conflicts:
        print("Conflicts not overwritten: " + ", ".join(conflicts), file=sys.stderr)
        return 2
    print("Reload or refresh Cline before using the installed global workflow and Skills.")
    print("Project-layer onboarding occurs when the Agent handles the first task in each workspace.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"FlowZ Cline installer failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
