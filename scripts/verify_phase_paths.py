#!/usr/bin/env python3
"""
Phase Path Verification Tool

Validates consistency between:
1. Physical directory names (phase_N_id/)
2. control_flows.yml metadata (sequence, phase_directory)
3. Code constants (PHASE_SEQUENCE in orchestrator files)

Usage:
    python3 verify_phase_paths.py
    python3 verify_phase_paths.py --project-root /path/to/project
    python3 verify_phase_paths.py --verbose
    python3 verify_phase_paths.py --fix-yaml  # Update YAML to match directories
"""

import argparse
import re
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class PhasePathValidator:
    """Validates phase path consistency."""

    def __init__(self, project_root: Path, verbose: bool = False):
        self.project_root = Path(project_root).resolve()
        self.verbose = verbose
        self.phases_dir = self.project_root / "phases"
        self.control_flows_file = (
            self.project_root / "design_specs" / "control_flows.yml"
        )
        self.errors = []
        self.warnings = []
        self.info = []

        if not self.control_flows_file.exists():
            raise FileNotFoundError(
                f"control_flows.yml not found at {self.control_flows_file}"
            )

        if not self.phases_dir.exists():
            raise FileNotFoundError(f"phases directory not found at {self.phases_dir}")

    def log_error(self, message: str):
        """Log an error."""
        self.errors.append(message)
        print(f"❌ ERROR: {message}")

    def log_warning(self, message: str):
        """Log a warning."""
        self.warnings.append(message)
        print(f"⚠️  WARNING: {message}")

    def log_info(self, message: str):
        """Log informational message."""
        self.info.append(message)
        if self.verbose:
            print(f"ℹ️  INFO: {message}")

    def log_success(self, message: str):
        """Log a success message."""
        print(f"✅ {message}")

    def load_control_flows(self) -> Dict:
        """Load control_flows.yml."""
        with open(self.control_flows_file) as f:
            return yaml.safe_load(f)

    def save_control_flows(self, spec: Dict):
        """Save control_flows.yml."""
        with open(self.control_flows_file, "w") as f:
            yaml.dump(spec, f, default_flow_style=False, sort_keys=False)

    def get_main_flow_phases(self, spec: Dict) -> List[Dict]:
        """Extract phases list from control_flows.yml."""
        flows = spec.get("flows", {})

        for flow_name, flow_data in flows.items():
            if isinstance(flow_data, dict) and "phases" in flow_data:
                return flow_data["phases"]

        raise ValueError("Could not find phases in control_flows.yml")

    def parse_directory_name(self, dir_name: str) -> Optional[Tuple[int, str]]:
        """
        Parse phase directory name.

        Returns: (sequence, phase_id) or None if not a phase directory

        Examples:
            phase_1_discovery → (1, 'discovery')
            phase_3_collection → (3, 'collection')
            outputs → None
        """
        match = re.match(r"^phase_(\d+)_(.+)$", dir_name)
        if match:
            return (int(match.group(1)), match.group(2))
        return None

    def extract_phase_sequence_from_file(self, file_path: Path) -> Optional[int]:
        """
        Extract PHASE_SEQUENCE constant from a Python file.

        Looks for pattern: PHASE_SEQUENCE = int(os.getenv('PHASE_SEQUENCE', 'N'))
        """
        if not file_path.exists():
            return None

        content = file_path.read_text()

        # Match: PHASE_SEQUENCE = int(os.getenv('PHASE_SEQUENCE', '3'))
        pattern = r"PHASE_SEQUENCE\s*=\s*int\(os\.getenv\(['\"]PHASE_SEQUENCE['\"],\s*['\"](\d+)['\"]\)"

        match = re.search(pattern, content)
        if match:
            return int(match.group(1))

        # Also try simpler pattern: PHASE_SEQUENCE = 3
        pattern_simple = r"PHASE_SEQUENCE\s*=\s*(\d+)"
        match_simple = re.search(pattern_simple, content)
        if match_simple:
            return int(match_simple.group(1))

        return None

    def get_physical_phases(self) -> List[Tuple[int, str, Path]]:
        """
        Get list of phase directories.

        Returns: List of (sequence, phase_id, directory_path)
        """
        phases = []

        for item in sorted(self.phases_dir.iterdir()):
            if item.is_dir():
                parsed = self.parse_directory_name(item.name)
                if parsed:
                    sequence, phase_id = parsed
                    phases.append((sequence, phase_id, item))

        return phases

    def validate_directory_sequence(
        self, physical_phases: List[Tuple[int, str, Path]]
    ) -> bool:
        """
        Validate that directory sequences are consecutive starting from 1.

        Returns: True if valid, False otherwise
        """
        sequences = [seq for seq, _, _ in physical_phases]

        if not sequences:
            self.log_error("No phase directories found")
            return False

        expected = list(range(1, len(sequences) + 1))

        if sequences != expected:
            self.log_error(
                f"Directory sequences not consecutive: found {sequences}, expected {expected}"
            )

            # Find gaps
            missing = set(expected) - set(sequences)
            if missing:
                self.log_error(f"  Missing sequences: {sorted(missing)}")

            # Find duplicates
            duplicates = [s for s in sequences if sequences.count(s) > 1]
            if duplicates:
                self.log_error(f"  Duplicate sequences: {sorted(set(duplicates))}")

            return False

        self.log_success(f"Directory sequences are consecutive: {sequences}")
        return True

    def validate_yaml_consistency(
        self, spec: Dict, physical_phases: List[Tuple[int, str, Path]]
    ) -> bool:
        """
        Validate control_flows.yml consistency with physical directories.

        Returns: True if valid, False otherwise
        """
        yaml_phases = self.get_main_flow_phases(spec)

        all_valid = True

        # Check phase count
        if len(yaml_phases) != len(physical_phases):
            self.log_error(
                f"Phase count mismatch: YAML has {len(yaml_phases)}, directories have {len(physical_phases)}"
            )
            all_valid = False

        # Build lookup dict
        physical_dict = {
            phase_id: (seq, path) for seq, phase_id, path in physical_phases
        }

        for yaml_phase in yaml_phases:
            phase_id = yaml_phase.get("phase_id")
            yaml_seq = yaml_phase.get("sequence")
            yaml_dir = yaml_phase.get("implementation", {}).get("phase_directory", "")

            if not phase_id:
                self.log_error("Phase in YAML missing 'phase_id'")
                all_valid = False
                continue

            # Check if directory exists
            if phase_id not in physical_dict:
                self.log_error(
                    f"Phase '{phase_id}' in YAML but no matching directory found"
                )
                all_valid = False
                continue

            physical_seq, physical_path = physical_dict[phase_id]

            # Check sequence match
            if yaml_seq != physical_seq:
                self.log_error(
                    f"Phase '{phase_id}': YAML sequence={yaml_seq}, directory sequence={physical_seq}"
                )
                all_valid = False

            # Check phase_directory path
            expected_dir = f"phases/phase_{physical_seq}_{phase_id}/"
            if yaml_dir != expected_dir:
                self.log_warning(
                    f"Phase '{phase_id}': YAML phase_directory='{yaml_dir}', expected '{expected_dir}'"
                )
                all_valid = False

            # Check orchestrator_file path
            yaml_orch = yaml_phase.get("implementation", {}).get(
                "orchestrator_file", ""
            )
            expected_orch = (
                f"phases/phase_{physical_seq}_{phase_id}/orchestrator_{phase_id}.py"
            )
            if yaml_orch != expected_orch:
                self.log_warning(
                    f"Phase '{phase_id}': YAML orchestrator_file='{yaml_orch}', expected '{expected_orch}'"
                )

        if all_valid:
            self.log_success("control_flows.yml is consistent with directories")

        return all_valid

    def validate_code_constants(
        self, physical_phases: List[Tuple[int, str, Path]]
    ) -> bool:
        """
        Validate PHASE_SEQUENCE constants in orchestrator files.

        Returns: True if valid, False otherwise
        """
        all_valid = True

        for seq, phase_id, phase_path in physical_phases:
            # Look for orchestrator file
            orchestrator_patterns = [
                f"orchestrator_{phase_id}.py",
                f"{phase_id}_orchestrator.py",
                "orchestrator.py",
            ]

            orchestrator_file = None
            for pattern in orchestrator_patterns:
                candidate = phase_path / pattern
                if candidate.exists():
                    orchestrator_file = candidate
                    break

            if not orchestrator_file:
                self.log_warning(
                    f"Phase '{phase_id}': No orchestrator file found (checked: {orchestrator_patterns})"
                )
                continue

            # Extract PHASE_SEQUENCE from file
            code_seq = self.extract_phase_sequence_from_file(orchestrator_file)

            if code_seq is None:
                self.log_warning(
                    f"Phase '{phase_id}': No PHASE_SEQUENCE constant found in {orchestrator_file.name}"
                )
                continue

            # Compare
            if code_seq != seq:
                self.log_error(
                    f"Phase '{phase_id}': Code PHASE_SEQUENCE={code_seq}, directory sequence={seq}"
                )
                all_valid = False
            else:
                self.log_info(
                    f"Phase '{phase_id}': PHASE_SEQUENCE constant matches ({seq})"
                )

        if all_valid:
            self.log_success("All PHASE_SEQUENCE constants are correct")

        return all_valid

    def fix_yaml_paths(
        self, spec: Dict, physical_phases: List[Tuple[int, str, Path]]
    ) -> bool:
        """
        Update control_flows.yml to match physical directories.

        Returns: True if changes made, False otherwise
        """
        yaml_phases = self.get_main_flow_phases(spec)

        physical_dict = {
            phase_id: (seq, path) for seq, phase_id, path in physical_phases
        }

        changes_made = False

        for yaml_phase in yaml_phases:
            phase_id = yaml_phase.get("phase_id")

            if not phase_id or phase_id not in physical_dict:
                continue

            physical_seq, _ = physical_dict[phase_id]

            # Update sequence
            if yaml_phase.get("sequence") != physical_seq:
                print(
                    f"  Updating {phase_id}: sequence {yaml_phase.get('sequence')} → {physical_seq}"
                )
                yaml_phase["sequence"] = physical_seq
                changes_made = True

            # Update phase_directory
            expected_dir = f"phases/phase_{physical_seq}_{phase_id}/"
            if (
                yaml_phase.get("implementation", {}).get("phase_directory")
                != expected_dir
            ):
                print(f"  Updating {phase_id}: phase_directory → {expected_dir}")
                yaml_phase.setdefault("implementation", {})[
                    "phase_directory"
                ] = expected_dir
                changes_made = True

            # Update orchestrator_file
            expected_orch = (
                f"phases/phase_{physical_seq}_{phase_id}/orchestrator_{phase_id}.py"
            )
            if (
                yaml_phase.get("implementation", {}).get("orchestrator_file")
                != expected_orch
            ):
                print(f"  Updating {phase_id}: orchestrator_file → {expected_orch}")
                yaml_phase.setdefault("implementation", {})[
                    "orchestrator_file"
                ] = expected_orch
                changes_made = True

        return changes_made

    def run_validation(self, fix_yaml: bool = False) -> bool:
        """
        Run full validation.

        Returns: True if all valid, False otherwise
        """
        print("\n" + "=" * 70)
        print("PHASE PATH VALIDATION")
        print("=" * 70 + "\n")

        print(f"📂 Project root: {self.project_root}")
        print(f"📂 Phases directory: {self.phases_dir}")
        print(f"📄 Config file: {self.control_flows_file}\n")

        # Load data
        spec = self.load_control_flows()
        physical_phases = self.get_physical_phases()

        print(f"📊 Found {len(physical_phases)} phase directories\n")

        # Step 1: Validate directory sequences
        print("=" * 70)
        print("STEP 1: Validating directory sequences")
        print("=" * 70 + "\n")

        dir_valid = self.validate_directory_sequence(physical_phases)

        # Step 2: Validate YAML consistency
        print("\n" + "=" * 70)
        print("STEP 2: Validating control_flows.yml")
        print("=" * 70 + "\n")

        yaml_valid = self.validate_yaml_consistency(spec, physical_phases)

        # Fix YAML if requested
        if fix_yaml and not yaml_valid:
            print("\n" + "=" * 70)
            print("FIXING control_flows.yml")
            print("=" * 70 + "\n")

            changes_made = self.fix_yaml_paths(spec, physical_phases)

            if changes_made:
                self.save_control_flows(spec)
                print("\n✅ Updated control_flows.yml")

                # Re-validate
                yaml_valid = self.validate_yaml_consistency(spec, physical_phases)
            else:
                print("\nℹ️  No changes needed")

        # Step 3: Validate code constants
        print("\n" + "=" * 70)
        print("STEP 3: Validating PHASE_SEQUENCE constants")
        print("=" * 70 + "\n")

        code_valid = self.validate_code_constants(physical_phases)

        # Summary
        print("\n" + "=" * 70)
        print("VALIDATION SUMMARY")
        print("=" * 70 + "\n")

        all_valid = dir_valid and yaml_valid and code_valid

        if all_valid:
            print("✅ ALL CHECKS PASSED")
            print(f"\n   Directory sequences: ✅ Valid")
            print(f"   control_flows.yml: ✅ Consistent")
            print(f"   Code constants: ✅ Correct")
        else:
            print("❌ VALIDATION FAILED")
            print(
                f"\n   Directory sequences: {'✅ Valid' if dir_valid else '❌ Invalid'}"
            )
            print(
                f"   control_flows.yml: {'✅ Consistent' if yaml_valid else '❌ Inconsistent'}"
            )
            print(
                f"   Code constants: {'✅ Correct' if code_valid else '❌ Incorrect'}"
            )

            if self.errors:
                print(f"\n   Errors: {len(self.errors)}")
            if self.warnings:
                print(f"   Warnings: {len(self.warnings)}")

        print()

        return all_valid


def main():
    parser = argparse.ArgumentParser(
        description="Phase Path Verification Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic validation
  python3 verify_phase_paths.py

  # Verbose output
  python3 verify_phase_paths.py --verbose

  # Fix control_flows.yml to match directories
  python3 verify_phase_paths.py --fix-yaml

  # Specify project root
  python3 verify_phase_paths.py --project-root /path/to/project
        """,
    )

    parser.add_argument(
        "--project-root",
        default=".",
        help="Project root directory (default: current directory)",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Show detailed information"
    )
    parser.add_argument(
        "--fix-yaml",
        action="store_true",
        help="Update control_flows.yml to match directories",
    )

    args = parser.parse_args()

    try:
        validator = PhasePathValidator(args.project_root, verbose=args.verbose)
        success = validator.run_validation(fix_yaml=args.fix_yaml)
        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
