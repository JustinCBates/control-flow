#!/usr/bin/env python3
"""
Scan for Obsolete Mock Files

This tool scans the project for mock files that were used during design time
but are no longer needed because the real implementation is complete.

Mocks are for design time only. Once real code is implemented, mocks should be removed.

Usage:
    python scan_obsolete_mocks.py [--auto-remove] [--phase PHASE_ID]
"""

import json
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Tuple
import argparse
from datetime import datetime

# Note: Avoid runtime sys.path hacks; rely on installed package or workspace import


class MockScanner:
    """Scans for obsolete mock files that can be safely removed."""

    # Patterns for mock files (only files explicitly named with "mock")
    MOCK_PATTERNS = [
        "**/mock_*.json",
        "**/mock_*.yml",
        "**/mock_*.yaml",
        "**/*_mock.json",
        "**/*_mock.yml",
        "**/*_mock.yaml",
        "**/mocks/**/*",  # Anything in a mocks/ directory
    ]

    # Patterns for implementation files (real code)
    IMPL_PATTERNS = [
        "**/*.py",
        "**/*.sh",
        "**/*.js",
    ]

    # Exclude patterns (don't scan these)
    EXCLUDE_PATTERNS = [
        "__pycache__",
        ".git",
        "node_modules",
        "venv",
        ".pytest_cache",
        "/docs/",  # Documentation files
        "/tests/",  # Test files
        "/testing/",  # Test fixtures
        "/output/",  # Output directories
        "/outputs/",  # Output directories
        "test_",  # Test files
        ".md",  # Markdown documentation
    ]

    def __init__(self, project_root: Path, control_flows_file: Path):
        """
        Initialize the mock scanner.

        Args:
            project_root: Root directory of the project
            control_flows_file: Path to control_flows.yml
        """
        self.project_root = Path(project_root)
        self.control_flows_file = Path(control_flows_file)

        # Load control flows configuration directly
        with open(control_flows_file) as f:
            self.control_flows = yaml.safe_load(f)

    def find_mock_files(self, phase_id: str = None) -> List[Path]:
        """
        Find all mock files in the project.

        Args:
            phase_id: Optional phase ID to limit search

        Returns:
            List of paths to mock files
        """
        mock_files = []

        if phase_id:
            # Scan specific phase only - use control_flows to find the phase directory
            phases = self.control_flows.get("phases", [])
            phase_dir = None
            for phase in phases:
                if phase.get("id") == phase_id:
                    # Construct phase directory path
                    phase_sequence = phase.get("sequence", 0)
                    phase_dir = (
                        self.project_root
                        / "phases"
                        / f"phase_{phase_sequence}_{phase_id}"
                    )
                    break

            if phase_dir and phase_dir.exists():
                search_dirs = [phase_dir]
            else:
                print(f"⚠️  Could not find phase directory for '{phase_id}'")
                return []
        else:
            # Scan all phases ONLY (not project root)
            search_dirs = []
            phases = self.control_flows.get("phases", [])
            for phase in phases:
                phase_id = phase.get("id")
                phase_sequence = phase.get("sequence", 0)
                if phase_id and phase_sequence:
                    phase_dir = (
                        self.project_root
                        / "phases"
                        / f"phase_{phase_sequence}_{phase_id}"
                    )
                    if phase_dir.exists():
                        search_dirs.append(phase_dir)

        # Search for mock files
        for search_dir in search_dirs:
            for pattern in self.MOCK_PATTERNS:
                for mock_file in search_dir.rglob(
                    pattern.split("/")[-1] if "**/" in pattern else pattern
                ):
                    # Check exclusions
                    if any(excl in str(mock_file) for excl in self.EXCLUDE_PATTERNS):
                        continue
                    mock_files.append(mock_file)

        return sorted(set(mock_files))

    def check_implementation_exists(self, mock_file: Path) -> Tuple[bool, List[Path]]:
        """
        Check if real implementation exists for this mock file.

        Args:
            mock_file: Path to the mock file

        Returns:
            Tuple of (implementation_exists, list_of_implementation_files)
        """
        # Get the directory containing the mock
        mock_dir = mock_file.parent

        # Look for implementation files in the same directory and subdirectories
        impl_files = []

        for pattern in self.IMPL_PATTERNS:
            ext = pattern.split(".")[-1]
            for impl_file in mock_dir.rglob(f"*.{ext}"):
                # Skip test files
                if "test_" in impl_file.name or "_test" in impl_file.name:
                    continue
                # Skip mock-related files
                if "mock" in impl_file.name.lower():
                    continue
                # Check exclusions
                if any(excl in str(impl_file) for excl in self.EXCLUDE_PATTERNS):
                    continue

                impl_files.append(impl_file)

        # Consider implementation to exist if there are real code files
        has_implementation = len(impl_files) > 0

        return has_implementation, impl_files

    def check_mock_referenced(
        self, mock_file: Path
    ) -> Tuple[bool, List[Tuple[Path, int]]]:
        """
        Check if the mock file is still referenced in code.

        Args:
            mock_file: Path to the mock file

        Returns:
            Tuple of (is_referenced, list_of_(file, line_number))
        """
        mock_name = mock_file.name
        references = []

        # Search for references in implementation files
        search_dir = mock_file.parent

        for impl_file in search_dir.rglob("*.py"):
            if impl_file == mock_file:
                continue

            try:
                with open(impl_file, encoding="utf-8", errors="ignore") as f:
                    for line_num, line in enumerate(f, 1):
                        if mock_name in line and "--mock" not in line.lower():
                            # Found a reference (but not a CLI arg)
                            if "mock_file" in line or "mock-file" in line:
                                references.append((impl_file, line_num))
            except Exception:
                pass

        return len(references) > 0, references

    def analyze_mock(self, mock_file: Path) -> Dict:
        """
        Analyze a single mock file to determine if it's obsolete.

        Args:
            mock_file: Path to the mock file

        Returns:
            Dict with analysis results
        """
        has_impl, impl_files = self.check_implementation_exists(mock_file)
        is_referenced, references = self.check_mock_referenced(mock_file)

        # Determine if mock is obsolete
        # Mock is obsolete if implementation exists AND it's not referenced
        is_obsolete = has_impl and not is_referenced

        return {
            "path": mock_file,
            "size": mock_file.stat().st_size if mock_file.exists() else 0,
            "has_implementation": has_impl,
            "implementation_files": impl_files,
            "is_referenced": is_referenced,
            "references": references,
            "is_obsolete": is_obsolete,
            "reason": self._get_obsolete_reason(has_impl, is_referenced),
        }

    def _get_obsolete_reason(self, has_impl: bool, is_referenced: bool) -> str:
        """Get human-readable reason for obsolescence status."""
        if has_impl and not is_referenced:
            return "Real implementation exists, no code references mock"
        elif has_impl and is_referenced:
            return "Real implementation exists, but still referenced in code"
        elif not has_impl:
            return "No implementation found (mock still needed)"
        else:
            return "Unknown"

    def scan(self, phase_id: str = None) -> Dict:
        """
        Perform a full scan for obsolete mocks.

        Args:
            phase_id: Optional phase ID to limit scan

        Returns:
            Dict with scan results
        """
        print(f"\n{'='*70}")
        print("🔍 SCANNING FOR OBSOLETE MOCK FILES")
        print(f"{'='*70}\n")

        if phase_id:
            print(f"📁 Scanning phase: {phase_id}")
        else:
            print(f"📁 Scanning all phases in: {self.project_root}")
        print()

        # Find all mock files
        mock_files = self.find_mock_files(phase_id)

        if not mock_files:
            print("✅ No mock files found")
            return {
                "total_mocks": 0,
                "obsolete_count": 0,
                "active_count": 0,
                "obsolete_mocks": [],
                "active_mocks": [],
                "timestamp": datetime.now().isoformat(),
            }

        print(f"Found {len(mock_files)} mock file(s)\n")

        # Analyze each mock
        obsolete_mocks = []
        active_mocks = []

        for mock_file in mock_files:
            print(f"Analyzing: {mock_file.relative_to(self.project_root)}")
            analysis = self.analyze_mock(mock_file)

            if analysis["is_obsolete"]:
                obsolete_mocks.append(analysis)
                print(f"  ❌ OBSOLETE: {analysis['reason']}")
            else:
                active_mocks.append(analysis)
                print(f"  ✅ ACTIVE: {analysis['reason']}")

            print()

        return {
            "total_mocks": len(mock_files),
            "obsolete_count": len(obsolete_mocks),
            "active_count": len(active_mocks),
            "obsolete_mocks": obsolete_mocks,
            "active_mocks": active_mocks,
            "timestamp": datetime.now().isoformat(),
        }

    def remove_obsolete_mocks(self, scan_results: Dict, dry_run: bool = True) -> int:
        """
        Remove obsolete mock files.

        Args:
            scan_results: Results from scan()
            dry_run: If True, only show what would be removed

        Returns:
            Number of files removed
        """
        obsolete_mocks = scan_results.get("obsolete_mocks", [])

        if not obsolete_mocks:
            print("\n✅ No obsolete mocks to remove")
            return 0

        print(f"\n{'='*70}")
        print(f"{'🗑️  DRY RUN - ' if dry_run else ''}REMOVING OBSOLETE MOCKS")
        print(f"{'='*70}\n")

        removed_count = 0
        total_size = 0

        for mock_info in obsolete_mocks:
            mock_file = mock_info["path"]
            size = mock_info["size"]

            print(
                f"{'[DRY RUN] ' if dry_run else ''}Removing: {mock_file.relative_to(self.project_root)}"
            )
            print(f"  Size: {size:,} bytes")
            print(f"  Reason: {mock_info['reason']}")

            if not dry_run:
                try:
                    mock_file.unlink()
                    print(f"  ✅ Removed")
                    removed_count += 1
                    total_size += size
                except Exception as e:
                    print(f"  ❌ Failed: {e}")
            else:
                removed_count += 1
                total_size += size

            print()

        print(f"{'='*70}")
        print(
            f"{'[DRY RUN] Would remove' if dry_run else 'Removed'}: {removed_count} file(s)"
        )
        print(f"{'[DRY RUN] Would free' if dry_run else 'Freed'}: {total_size:,} bytes")
        print(f"{'='*70}\n")

        return removed_count


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Scan for obsolete mock files that can be safely removed"
    )
    parser.add_argument(
        "--project-root",
        default="/opt/openproject/external/config-manager",
        help="Project root directory (default: /opt/openproject/external/config-manager)",
    )
    parser.add_argument(
        "--control-flows",
        help="Path to control_flows.yml (auto-detected if not specified)",
    )
    parser.add_argument("--phase", help="Limit scan to specific phase ID")
    parser.add_argument(
        "--auto-remove",
        action="store_true",
        help="Automatically remove obsolete mocks (default: dry run)",
    )
    parser.add_argument("--report", help="Save scan report to JSON file")

    args = parser.parse_args()

    # Resolve project root
    project_root = Path(args.project_root).resolve()

    if not project_root.exists():
        print(f"❌ Project root not found: {project_root}")
        return 1

    # Find control_flows.yml
    if args.control_flows:
        control_flows_file = Path(args.control_flows)
    else:
        # Auto-detect
        control_flows_file = project_root / "control_flows.yml"
        if not control_flows_file.exists():
            control_flows_file = (
                project_root.parent / "control-flow" / "control_flows.yml"
            )

    if not control_flows_file.exists():
        print(f"❌ control_flows.yml not found: {control_flows_file}")
        print("💡 Specify with --control-flows argument")
        return 1

    # Create scanner
    scanner = MockScanner(project_root, control_flows_file)

    # Perform scan
    results = scanner.scan(phase_id=args.phase)

    # Save report if requested
    if args.report:
        report_path = Path(args.report)
        with open(report_path, "w") as f:
            # Convert Path objects to strings for JSON serialization
            json_results = {
                "total_mocks": results["total_mocks"],
                "obsolete_count": results["obsolete_count"],
                "active_count": results["active_count"],
                "timestamp": results["timestamp"],
                "obsolete_mocks": [
                    {
                        "path": str(m["path"]),
                        "size": m["size"],
                        "reason": m["reason"],
                        "implementation_files": [
                            str(f) for f in m["implementation_files"]
                        ],
                    }
                    for m in results["obsolete_mocks"]
                ],
                "active_mocks": [
                    {"path": str(m["path"]), "size": m["size"], "reason": m["reason"]}
                    for m in results["active_mocks"]
                ],
            }
            json.dump(json_results, f, indent=2)
        print(f"📄 Report saved to: {report_path}")

    # Remove obsolete mocks if requested
    if results["obsolete_count"] > 0:
        dry_run = not args.auto_remove

        if dry_run:
            print(
                "\n💡 This was a DRY RUN. Use --auto-remove to actually delete files."
            )

        scanner.remove_obsolete_mocks(results, dry_run=dry_run)

    # Summary
    print(f"\n{'='*70}")
    print("📊 SUMMARY")
    print(f"{'='*70}")
    print(f"Total mock files found: {results['total_mocks']}")
    print(f"Obsolete (can be removed): {results['obsolete_count']}")
    print(f"Active (still needed): {results['active_count']}")
    print(f"{'='*70}\n")

    return 0 if results["obsolete_count"] == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
