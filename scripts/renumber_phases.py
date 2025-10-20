#!/usr/bin/env python3
"""
Phase Renumbering Automation Tool

Handles mechanical aspects of phase insertions, deletions, and moves:
- Renames phase directories
- Updates control_flows.yml
- Updates PHASE_SEQUENCE constants in code
- Validates changes

Usage:
    # Insert new phase at position 3
    python3 renumber_phases.py insert --at 3 --name "Preprocessing Phase" --id preprocessing

    # Delete phase 3
    python3 renumber_phases.py delete --at 3

    # Move phase 3 to position 5
    python3 renumber_phases.py move --from 3 --to 5

    # Dry run (show what would happen without making changes)
    python3 renumber_phases.py insert --at 3 --name "Preprocessing" --id preprocessing --dry-run
"""

import argparse
import shutil
import yaml
from pathlib import Path
import re
import sys
from typing import Dict, List, Optional


class PhaseRenumberer:
    """Automates phase renumbering operations."""

    def __init__(self, project_root: Path, dry_run: bool = False):
        self.project_root = Path(project_root).resolve()
        self.dry_run = dry_run
        self.phases_dir = self.project_root / "phases"
        self.control_flows_file = (
            self.project_root / "design_specs" / "control_flows.yml"
        )

        if not self.control_flows_file.exists():
            raise FileNotFoundError(
                f"control_flows.yml not found at {self.control_flows_file}"
            )

        if not self.phases_dir.exists():
            raise FileNotFoundError(f"phases directory not found at {self.phases_dir}")

    def load_control_flows(self) -> Dict:
        """Load control_flows.yml"""
        with open(self.control_flows_file) as f:
            return yaml.safe_load(f)

    def save_control_flows(self, spec: Dict):
        """Save control_flows.yml"""
        if self.dry_run:
            print(f"  [DRY RUN] Would save control_flows.yml")
            return

        with open(self.control_flows_file, "w") as f:
            yaml.dump(spec, f, default_flow_style=False, sort_keys=False)
        print(f"  ✅ Saved control_flows.yml")

    def get_main_flow_phases(self, spec: Dict) -> List[Dict]:
        """Extract phases list from control_flows.yml"""
        flows = spec.get("flows", {})

        # Find the main flow with phases
        for flow_name, flow_data in flows.items():
            if isinstance(flow_data, dict) and "phases" in flow_data:
                return flow_data["phases"]

        raise ValueError("Could not find phases in control_flows.yml")

    def update_phase_sequence_in_file(
        self, file_path: Path, old_seq: int, new_seq: int
    ) -> bool:
        """Update PHASE_SEQUENCE constant in a Python file"""
        if not file_path.exists():
            return False

        content = file_path.read_text()

        # Match: PHASE_SEQUENCE = int(os.getenv('PHASE_SEQUENCE', '3'))
        pattern = rf"(PHASE_SEQUENCE\s*=\s*int\(os\.getenv\(['\"]PHASE_SEQUENCE['\"],\s*['\"])(\d+)(['\"])"

        matches = list(re.finditer(pattern, content))

        if not matches:
            return False

        # Check if the old sequence matches
        for match in matches:
            if int(match.group(2)) == old_seq:
                if self.dry_run:
                    print(
                        f"    [DRY RUN] Would update {file_path.name}: sequence {old_seq} → {new_seq}"
                    )
                    return True

                new_content = re.sub(pattern, rf"\g<1>{new_seq}\g<3>", content)
                file_path.write_text(new_content)
                print(
                    f"    ✅ Updated {file_path.name}: sequence {old_seq} → {new_seq}"
                )
                return True

        return False

    def rename_phase_directory(
        self, old_num: int, new_num: int, phase_id: str
    ) -> Optional[Path]:
        """Rename phase directory"""
        old_dir = self.phases_dir / f"phase_{old_num}_{phase_id}"
        new_dir = self.phases_dir / f"phase_{new_num}_{phase_id}"

        if not old_dir.exists():
            print(f"  ⚠️  Warning: {old_dir.name} does not exist")
            return None

        if new_dir.exists():
            print(f"  ⚠️  Warning: {new_dir.name} already exists")
            return None

        if self.dry_run:
            print(f"  [DRY RUN] Would rename: {old_dir.name} → {new_dir.name}")
            return new_dir

        shutil.move(str(old_dir), str(new_dir))
        print(f"  ✅ Renamed: {old_dir.name} → {new_dir.name}")
        return new_dir

    def update_orchestrator_file(
        self, phase_dir: Path, phase_id: str, old_seq: int, new_seq: int
    ):
        """Update PHASE_SEQUENCE in orchestrator file"""
        orchestrator_patterns = [
            f"orchestrator_{phase_id}.py",
            f"{phase_id}_orchestrator.py",
            "orchestrator.py",
        ]

        for pattern in orchestrator_patterns:
            orchestrator = phase_dir / pattern
            if orchestrator.exists():
                self.update_phase_sequence_in_file(orchestrator, old_seq, new_seq)
                return

        print(f"    ⚠️  No orchestrator file found in {phase_dir.name}")

    def insert_phase(self, position: int, phase_name: str, phase_id: str):
        """Insert a new phase at the given position"""
        print(f"\n{'='*70}")
        print(f"INSERTING PHASE: {phase_name} (ID: {phase_id}) at position {position}")
        print(f"{'='*70}\n")

        if self.dry_run:
            print("🔍 DRY RUN MODE - No actual changes will be made\n")

        # Load spec
        spec = self.load_control_flows()
        phases = self.get_main_flow_phases(spec)

        if position < 1 or position > len(phases) + 1:
            print(
                f"❌ Error: Position {position} is out of range (1-{len(phases) + 1})"
            )
            return False

        # Step 1: Shift subsequent phases
        print(f"📦 Step 1: Shifting phases {position} onwards...\n")

        # Rename directories in reverse order (to avoid conflicts)
        for i in range(len(phases) - 1, position - 1, -1):
            phase = phases[i]
            old_seq = i + 1
            new_seq = i + 2
            phase_id_current = phase["phase_id"]

            print(f"  Phase: {phase_id_current}")

            # Rename directory
            new_dir = self.rename_phase_directory(old_seq, new_seq, phase_id_current)

            # Update control_flows.yml phase entry
            phase["sequence"] = new_seq
            old_dir_path = phase.get("implementation", {}).get(
                "phase_directory", f"phases/phase_{old_seq}_{phase_id_current}/"
            )
            new_dir_path = f"phases/phase_{new_seq}_{phase_id_current}/"
            phase["implementation"]["phase_directory"] = new_dir_path
            phase["implementation"][
                "orchestrator_file"
            ] = f"{new_dir_path}orchestrator_{phase_id_current}.py"

            if old_dir_path != new_dir_path:
                print(f"    Updated phase_directory: {old_dir_path} → {new_dir_path}")

            # Update PHASE_SEQUENCE in orchestrator file
            if new_dir and not self.dry_run:
                self.update_orchestrator_file(
                    new_dir, phase_id_current, old_seq, new_seq
                )

            print()

        # Step 2: Create new phase directory
        print(f"📦 Step 2: Creating new phase '{phase_name}' at position {position}\n")

        new_dir = self.phases_dir / f"phase_{position}_{phase_id}"

        if self.dry_run:
            print(f"  [DRY RUN] Would create directory: {new_dir}")
        else:
            new_dir.mkdir(parents=True, exist_ok=True)
            (new_dir / "outputs").mkdir(exist_ok=True)
            (new_dir / "tests").mkdir(exist_ok=True)
            print(f"  ✅ Created directory: {new_dir}")
            print(f"  ✅ Created outputs directory")
            print(f"  ✅ Created tests directory")

        # Step 3: Add to control_flows.yml
        print(f"\n📦 Step 3: Updating control_flows.yml\n")

        new_phase_entry = {
            "phase_id": phase_id,
            "name": phase_name,
            "sequence": position,
            "status": "PLANNED",
            "description": f"{phase_name}",
            "sub_flows": [],
            "artifacts_produced": [],
            "artifacts_consumed": [],
            "implementation": {
                "phase_directory": f"phases/phase_{position}_{phase_id}/",
                "orchestrator_file": f"phases/phase_{position}_{phase_id}/orchestrator_{phase_id}.py",
                "module": f"phases.phase_{position}_{phase_id}",
                "class": f"{self._class_name_from_id(phase_id)}Phase",
                "method": "execute(context)",
                "side_effects": [],
            },
        }

        phases.insert(position - 1, new_phase_entry)
        self.save_control_flows(spec)

        # Summary
        print(f"\n{'='*70}")
        print(f"✅ INSERTION COMPLETE!")
        print(f"{'='*70}\n")
        print(f"New phase directory: {new_dir}")
        print(f"Phase ID: {phase_id}")
        print(f"Position: {position}")

        if not self.dry_run:
            print(f"\n📋 Next steps:")
            print(f"  1. Generate phase scaffolding:")
            print(f"     cd {self.project_root}")
            print(f"     python3 generator.py scaffold-phase --phase {phase_id}")
            print(f"  2. Verify all phases:")
            print(f"     python3 scripts/verify_phase_paths.py")
            print(f"  3. Test phase sequence:")
            print(
                f"     python3 phases/phase_{position}_{phase_id}/orchestrator_{phase_id}.py --show-paths"
            )

        return True

    def delete_phase(self, position: int):
        """Delete a phase at the given position"""
        print(f"\n{'='*70}")
        print(f"DELETING PHASE at position {position}")
        print(f"{'='*70}\n")

        if self.dry_run:
            print("🔍 DRY RUN MODE - No actual changes will be made\n")

        # Load spec
        spec = self.load_control_flows()
        phases = self.get_main_flow_phases(spec)

        if position < 1 or position > len(phases):
            print(f"❌ Error: Position {position} is out of range (1-{len(phases)})")
            return False

        phase_to_delete = phases[position - 1]
        phase_id = phase_to_delete["phase_id"]
        phase_name = phase_to_delete["name"]

        print(f"⚠️  About to delete: {phase_name} (ID: {phase_id})")
        print(f"⚠️  Directory: phase_{position}_{phase_id}\n")

        if not self.dry_run:
            response = input(
                "Are you sure? This cannot be undone. Type 'yes' to confirm: "
            )
            if response.lower() != "yes":
                print("❌ Deletion cancelled")
                return False

        # Step 1: Remove from control_flows.yml
        print(f"📦 Step 1: Removing from control_flows.yml\n")
        phases.pop(position - 1)
        self.save_control_flows(spec)

        # Step 2: Shift subsequent phases
        print(f"📦 Step 2: Shifting phases {position + 1} onwards...\n")

        for i in range(position - 1, len(phases)):
            phase = phases[i]
            old_seq = i + 2  # +2 because we deleted one and array is 0-indexed
            new_seq = i + 1
            phase_id_current = phase["phase_id"]

            print(f"  Phase: {phase_id_current}")

            # Rename directory
            new_dir = self.rename_phase_directory(old_seq, new_seq, phase_id_current)

            # Update control_flows.yml
            phase["sequence"] = new_seq
            phase["implementation"][
                "phase_directory"
            ] = f"phases/phase_{new_seq}_{phase_id_current}/"
            phase["implementation"][
                "orchestrator_file"
            ] = f"phases/phase_{new_seq}_{phase_id_current}/orchestrator_{phase_id_current}.py"

            # Update PHASE_SEQUENCE in orchestrator file
            if new_dir and not self.dry_run:
                self.update_orchestrator_file(
                    new_dir, phase_id_current, old_seq, new_seq
                )

            print()

        self.save_control_flows(spec)

        # Step 3: Archive deleted phase directory
        print(f"📦 Step 3: Archiving deleted phase\n")

        deleted_dir = self.phases_dir / f"phase_{position}_{phase_id}"
        archive_dir = self.project_root / "archived_phases"

        if deleted_dir.exists():
            if self.dry_run:
                print(f"  [DRY RUN] Would move {deleted_dir.name} → archived_phases/")
            else:
                archive_dir.mkdir(exist_ok=True)
                archive_path = archive_dir / f"phase_{position}_{phase_id}_deleted"
                shutil.move(str(deleted_dir), str(archive_path))
                print(f"  ✅ Archived to: {archive_path}")
        else:
            print(f"  ⚠️  Directory {deleted_dir} not found")

        # Summary
        print(f"\n{'='*70}")
        print(f"✅ DELETION COMPLETE!")
        print(f"{'='*70}\n")
        print(f"Deleted: {phase_name} (ID: {phase_id})")
        print(f"Archived to: archived_phases/phase_{position}_{phase_id}_deleted")

        return True

    def move_phase(self, from_pos: int, to_pos: int):
        """Move a phase from one position to another"""
        print(f"\n{'='*70}")
        print(f"MOVING PHASE from position {from_pos} to position {to_pos}")
        print(f"{'='*70}\n")

        if self.dry_run:
            print("🔍 DRY RUN MODE - No actual changes will be made\n")

        # Load spec
        spec = self.load_control_flows()
        phases = self.get_main_flow_phases(spec)

        if from_pos < 1 or from_pos > len(phases):
            print(
                f"❌ Error: Source position {from_pos} is out of range (1-{len(phases)})"
            )
            return False

        if to_pos < 1 or to_pos > len(phases):
            print(
                f"❌ Error: Target position {to_pos} is out of range (1-{len(phases)})"
            )
            return False

        if from_pos == to_pos:
            print(f"❌ Error: Source and target positions are the same")
            return False

        phase_to_move = phases[from_pos - 1]
        phase_id = phase_to_move["phase_id"]
        phase_name = phase_to_move["name"]

        print(f"Moving: {phase_name} (ID: {phase_id})")
        print(f"From: position {from_pos}")
        print(f"To: position {to_pos}\n")

        # This is complex - use temp directory to avoid conflicts
        temp_dir = self.phases_dir / f"_temp_move_{phase_id}"
        original_dir = self.phases_dir / f"phase_{from_pos}_{phase_id}"

        # Step 1: Move source to temp
        print(f"📦 Step 1: Moving to temporary location\n")
        if original_dir.exists():
            if self.dry_run:
                print(f"  [DRY RUN] Would move {original_dir.name} → {temp_dir.name}")
            else:
                shutil.move(str(original_dir), str(temp_dir))
                print(f"  ✅ Moved to temp: {temp_dir.name}")

        # Step 2: Shift intermediate phases
        print(f"\n📦 Step 2: Shifting intermediate phases\n")

        if from_pos < to_pos:
            # Moving forward - shift phases backward
            for pos in range(from_pos + 1, to_pos + 1):
                phase = phases[pos - 1]
                phase_id_current = phase["phase_id"]
                new_pos = pos - 1

                print(f"  Phase {pos} ({phase_id_current}) → Position {new_pos}")
                new_dir = self.rename_phase_directory(pos, new_pos, phase_id_current)

                # Update control_flows.yml
                phase["sequence"] = new_pos
                phase["implementation"][
                    "phase_directory"
                ] = f"phases/phase_{new_pos}_{phase_id_current}/"
                phase["implementation"][
                    "orchestrator_file"
                ] = f"phases/phase_{new_pos}_{phase_id_current}/orchestrator_{phase_id_current}.py"

                if new_dir and not self.dry_run:
                    self.update_orchestrator_file(
                        new_dir, phase_id_current, pos, new_pos
                    )
        else:
            # Moving backward - shift phases forward
            for pos in range(from_pos - 1, to_pos - 1, -1):
                phase = phases[pos - 1]
                phase_id_current = phase["phase_id"]
                new_pos = pos + 1

                print(f"  Phase {pos} ({phase_id_current}) → Position {new_pos}")
                new_dir = self.rename_phase_directory(pos, new_pos, phase_id_current)

                # Update control_flows.yml
                phase["sequence"] = new_pos
                phase["implementation"][
                    "phase_directory"
                ] = f"phases/phase_{new_pos}_{phase_id_current}/"
                phase["implementation"][
                    "orchestrator_file"
                ] = f"phases/phase_{new_pos}_{phase_id_current}/orchestrator_{phase_id_current}.py"

                if new_dir and not self.dry_run:
                    self.update_orchestrator_file(
                        new_dir, phase_id_current, pos, new_pos
                    )

        # Step 3: Move temp to final position
        print(f"\n📦 Step 3: Moving to final position {to_pos}\n")

        final_dir = self.phases_dir / f"phase_{to_pos}_{phase_id}"

        if self.dry_run:
            print(f"  [DRY RUN] Would move {temp_dir.name} → {final_dir.name}")
        else:
            if temp_dir.exists():
                shutil.move(str(temp_dir), str(final_dir))
                print(f"  ✅ Moved to final position: {final_dir.name}")

                # Update PHASE_SEQUENCE in orchestrator
                self.update_orchestrator_file(final_dir, phase_id, from_pos, to_pos)

        # Step 4: Update control_flows.yml for moved phase and reorder
        print(f"\n📦 Step 4: Updating control_flows.yml\n")

        moved_phase = phases.pop(from_pos - 1)
        phases.insert(to_pos - 1, moved_phase)

        moved_phase["sequence"] = to_pos
        moved_phase["implementation"][
            "phase_directory"
        ] = f"phases/phase_{to_pos}_{phase_id}/"
        moved_phase["implementation"][
            "orchestrator_file"
        ] = f"phases/phase_{to_pos}_{phase_id}/orchestrator_{phase_id}.py"

        self.save_control_flows(spec)

        # Summary
        print(f"\n{'='*70}")
        print(f"✅ MOVE COMPLETE!")
        print(f"{'='*70}\n")
        print(f"Moved: {phase_name} (ID: {phase_id})")
        print(f"From position {from_pos} → To position {to_pos}")

        return True

    @staticmethod
    def _class_name_from_id(phase_id: str) -> str:
        """Convert phase_id to PascalCase class name"""
        return "".join(word.capitalize() for word in phase_id.split("_"))


def main():
    parser = argparse.ArgumentParser(
        description="Phase Renumbering Automation Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Insert new phase
  python3 renumber_phases.py insert --at 3 --name "Preprocessing Phase" --id preprocessing

  # Delete phase 3
  python3 renumber_phases.py delete --at 3

  # Move phase 3 to position 5
  python3 renumber_phases.py move --from 3 --to 5

  # Dry run (show what would happen)
  python3 renumber_phases.py insert --at 3 --name "Test" --id test --dry-run
        """,
    )

    parser.add_argument(
        "--project-root",
        default=".",
        help="Project root directory (default: current directory)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without making changes",
    )

    subparsers = parser.add_subparsers(
        dest="command", help="Command to execute", required=True
    )

    # Insert command
    insert_parser = subparsers.add_parser("insert", help="Insert a new phase")
    insert_parser.add_argument(
        "--at", type=int, required=True, help="Position to insert (1-based)"
    )
    insert_parser.add_argument("--name", required=True, help="Phase display name")
    insert_parser.add_argument(
        "--id",
        dest="phase_id",
        required=True,
        help="Phase identifier (lowercase_with_underscores)",
    )

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a phase")
    delete_parser.add_argument(
        "--at", type=int, required=True, help="Position to delete (1-based)"
    )

    # Move command
    move_parser = subparsers.add_parser("move", help="Move a phase")
    move_parser.add_argument(
        "--from",
        dest="from_pos",
        type=int,
        required=True,
        help="Current position (1-based)",
    )
    move_parser.add_argument(
        "--to", dest="to_pos", type=int, required=True, help="New position (1-based)"
    )

    args = parser.parse_args()

    try:
        renumberer = PhaseRenumberer(args.project_root, dry_run=args.dry_run)

        if args.command == "insert":
            success = renumberer.insert_phase(args.at, args.name, args.phase_id)
        elif args.command == "delete":
            success = renumberer.delete_phase(args.at)
        elif args.command == "move":
            success = renumberer.move_phase(args.from_pos, args.to_pos)
        else:
            parser.print_help()
            sys.exit(1)

        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
