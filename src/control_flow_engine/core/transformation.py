"""
Control Flow Transformation System

Provides safe, validated transformations for control flow specifications.
Implements a plan-validate-apply workflow for all YAML modifications.

Author: Control Flow Engine
Date: 2025-10-15
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set, Tuple
from enum import Enum
from pathlib import Path
import copy
import json
import shutil
import re
from datetime import datetime

# Import universal structure operation libraries
from ..libraries.structure_ops import (
    StructureDeleter,
    DeleteOperation,
    StructureInserter,
    InsertOperation,
    InsertPosition,
    InsertionPoint,
    StructureRenumberer,
    RenumberOperation,
    RenumberStrategy,
)

# Import universal YAML operation libraries
from ..libraries.yaml_ops import YAMLSaver, SaveOptions


class TransformationType(Enum):
    """Types of transformations that can be applied."""

    INSERT = "insert"
    DELETE = "delete"
    MOVE = "move"
    RENUMBER = "renumber"
    UPDATE = "update"
    MOCK = "mock"


class ValidationStatus(Enum):
    """Validation status for transformations."""

    PENDING = "pending"
    VALID = "valid"
    INVALID = "invalid"
    WARNING = "warning"


@dataclass
class TransformationMapping:
    """Maps old structure to new structure for a single element."""

    element_type: str  # 'phase', 'step', 'flow_step'
    element_id: str
    old_sequence: Optional[int] = None
    new_sequence: Optional[int] = None
    old_parent: Optional[str] = None  # parent phase_id if step
    new_parent: Optional[str] = None
    operation: str = "preserve"  # preserve, insert, delete, move, renumber
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self):
        if self.operation == "insert":
            return f"INSERT {self.element_type} '{self.element_id}' at seq {self.new_sequence}"
        elif self.operation == "delete":
            return f"DELETE {self.element_type} '{self.element_id}' (seq {self.old_sequence})"
        elif self.operation == "move":
            return f"MOVE {self.element_type} '{self.element_id}': {self.old_parent} → {self.new_parent}"
        elif self.operation == "renumber":
            return f"RENUMBER {self.element_type} '{self.element_id}': seq {self.old_sequence} → {self.new_sequence}"
        else:
            return f"{self.operation.upper()} {self.element_type} '{self.element_id}'"


@dataclass
class ValidationResult:
    """Result of transformation validation."""

    status: ValidationStatus
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    checks_performed: Dict[str, bool] = field(default_factory=dict)

    def add_error(self, message: str):
        """Add validation error."""
        self.errors.append(message)
        self.valid = False
        self.status = ValidationStatus.INVALID

    def add_warning(self, message: str):
        """Add validation warning."""
        self.warnings.append(message)
        if self.status == ValidationStatus.VALID:
            self.status = ValidationStatus.WARNING

    def __repr__(self):
        status_symbol = "✅" if self.valid else "❌"
        return f"{status_symbol} Validation: {self.status.value} ({len(self.errors)} errors, {len(self.warnings)} warnings)"


@dataclass
class TransformationPlan:
    """
    A plan for transforming a control flow specification.

    This represents the intended transformation before it's applied,
    allowing for validation and preview.
    """

    transformation_type: TransformationType
    flow_name: str
    description: str
    mappings: List[TransformationMapping] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    validation_result: Optional[ValidationResult] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def add_mapping(self, mapping: TransformationMapping):
        """Add a transformation mapping to the plan."""
        self.mappings.append(mapping)

    def get_affected_elements(self) -> Set[str]:
        """Get all element IDs affected by this transformation."""
        return {m.element_id for m in self.mappings}

    def get_inserts(self) -> List[TransformationMapping]:
        """Get all insert operations."""
        return [m for m in self.mappings if m.operation == "insert"]

    def get_deletes(self) -> List[TransformationMapping]:
        """Get all delete operations."""
        return [m for m in self.mappings if m.operation == "delete"]

    def get_moves(self) -> List[TransformationMapping]:
        """Get all move operations."""
        return [m for m in self.mappings if m.operation == "move"]

    def get_renumbers(self) -> List[TransformationMapping]:
        """Get all renumber operations."""
        return [m for m in self.mappings if m.operation == "renumber"]

    def summary(self) -> str:
        """Generate a human-readable summary of the plan."""
        lines = [
            f"Transformation Plan: {self.transformation_type.value}",
            f"Flow: {self.flow_name}",
            f"Description: {self.description}",
            f"Mappings: {len(self.mappings)}",
            f"  - Inserts: {len(self.get_inserts())}",
            f"  - Deletes: {len(self.get_deletes())}",
            f"  - Moves: {len(self.get_moves())}",
            f"  - Renumbers: {len(self.get_renumbers())}",
        ]

        if self.validation_result:
            lines.append(f"Validation: {self.validation_result.status.value}")

        return "\n".join(lines)


@dataclass
class DirectoryOperation:
    """Represents a file system operation needed to sync directories."""

    operation: str  # 'move', 'delete', 'create', 'update_imports'
    source: Optional[Path] = None
    destination: Optional[Path] = None
    element_id: str = ""
    element_type: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self):
        if self.operation == "move":
            return f"MOVE {self.source} → {self.destination}"
        elif self.operation == "delete":
            return f"DELETE {self.source}"
        elif self.operation == "create":
            return f"CREATE {self.destination}"
        elif self.operation == "update_imports":
            return f"UPDATE_IMPORTS in {self.source}"
        return f"{self.operation.upper()}"


class TransformationHistory:
    """
    Manages persistent history of transformations for undo/rollback support.

    Stores transformation history in .transformation_history.json with:
    - Timestamp of each transformation
    - Complete transformation plan and mappings
    - Checksums of affected files (YAML, directories)
    - Enough data to reverse the transformation

    History file format:
    {
        "version": "1.0",
        "transformations": [
            {
                "timestamp": "2024-10-15T10:30:00",
                "transformation_type": "renumber",
                "flow_name": "main_config_flow",
                "description": "Renumber discovery phase steps from 0",
                "mappings": [...],
                "files_modified": [...],
                "checksums_before": {...},
                "checksums_after": {...},
                "can_rollback": true
            }
        ]
    }
    """

    def __init__(self, history_file: Path):
        """
        Initialize transformation history manager.

        Args:
            history_file: Path to .transformation_history.json file
        """
        self.history_file = history_file
        self.history: Dict[str, Any] = self._load_history()

    def _load_history(self) -> Dict[str, Any]:
        """Load existing history or create new structure."""
        if self.history_file.exists():
            try:
                with open(self.history_file, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(
                    f"⚠️  Warning: Could not parse {self.history_file}, creating new history"
                )
                return self._create_empty_history()
        else:
            return self._create_empty_history()

    def _create_empty_history(self) -> Dict[str, Any]:
        """Create empty history structure."""
        return {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "transformations": [],
        }

    def _save_history(self):
        """Save history to file."""
        # Ensure parent directory exists
        self.history_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.history_file, "w") as f:
            json.dump(self.history, f, indent=2, default=str)

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate checksum of a file for change detection."""
        import hashlib

        if not file_path.exists():
            return "FILE_NOT_FOUND"

        try:
            with open(file_path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            return f"ERROR:{str(e)}"

    def record_transformation(
        self,
        plan: "TransformationPlan",
        spec_file: Optional[Path] = None,
        affected_directories: Optional[List[Path]] = None,
        affected_files: Optional[List[Path]] = None,
    ) -> Dict[str, Any]:
        """
        Record a transformation in the history.

        Args:
            plan: The transformation plan that was applied
            spec_file: Path to the YAML spec file (for checksums)
            affected_directories: List of directories that were modified
            affected_files: List of files that were modified (imports, configs, docs)

        Returns:
            The history entry that was created
        """
        # Build list of all affected files
        files_modified = []
        if spec_file:
            files_modified.append(str(spec_file))
        if affected_directories:
            files_modified.extend([str(d) for d in affected_directories])
        if affected_files:
            files_modified.extend([str(f) for f in affected_files])

        # Calculate checksums after transformation
        checksums_after = {}
        if spec_file and spec_file.exists():
            checksums_after[str(spec_file)] = self._calculate_checksum(spec_file)

        # Serialize mappings
        mappings_data = []
        for mapping in plan.mappings:
            mappings_data.append(
                {
                    "element_type": mapping.element_type,
                    "element_id": mapping.element_id,
                    "old_sequence": mapping.old_sequence,
                    "new_sequence": mapping.new_sequence,
                    "old_parent": mapping.old_parent,
                    "new_parent": mapping.new_parent,
                    "operation": mapping.operation,
                }
            )

        # Create history entry
        entry = {
            "timestamp": datetime.now().isoformat(),
            "transformation_type": plan.transformation_type.value,
            "flow_name": plan.flow_name,
            "description": plan.description,
            "mappings": mappings_data,
            "metadata": plan.metadata,
            "files_modified": files_modified,
            "checksums_after": checksums_after,
            "validation_valid": (
                plan.validation_result.valid if plan.validation_result else None
            ),
            "validation_errors": (
                plan.validation_result.errors if plan.validation_result else []
            ),
            "validation_warnings": (
                plan.validation_result.warnings if plan.validation_result else []
            ),
            "can_rollback": True,  # Will be set to False if rollback is not possible
        }

        # Add to history
        self.history["transformations"].append(entry)

        # Save to file
        self._save_history()

        return entry

    def get_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get transformation history.

        Args:
            limit: Maximum number of entries to return (most recent first)

        Returns:
            List of transformation history entries
        """
        transformations = self.history.get("transformations", [])

        # Return most recent first
        transformations.reverse()

        if limit:
            return transformations[:limit]
        return transformations

    def get_last_transformation(self) -> Optional[Dict[str, Any]]:
        """Get the most recent transformation."""
        transformations = self.history.get("transformations", [])
        return transformations[-1] if transformations else None

    def can_rollback(self, steps: int = 1) -> Tuple[bool, str]:
        """
        Check if rollback is possible for the last N transformations.

        Args:
            steps: Number of transformations to rollback

        Returns:
            Tuple of (can_rollback, reason_if_not)
        """
        transformations = self.history.get("transformations", [])

        if len(transformations) < steps:
            return (
                False,
                f"Not enough transformations in history ({len(transformations)} < {steps})",
            )

        # Check if all transformations in rollback range are marked as rollback-able
        for i in range(len(transformations) - steps, len(transformations)):
            if not transformations[i].get("can_rollback", True):
                return False, f"Transformation {i+1} cannot be rolled back"

        return True, ""

    def clear_history(self):
        """Clear all transformation history (use with caution!)."""
        self.history = self._create_empty_history()
        self._save_history()

    def export_history(self, output_file: Path):
        """Export history to a different file (for backup)."""
        with open(output_file, "w") as f:
            json.dump(self.history, f, indent=2, default=str)

    def summary(self) -> str:
        """Generate a human-readable summary of the history."""
        transformations = self.history.get("transformations", [])

        lines = [
            "=" * 60,
            "TRANSFORMATION HISTORY",
            "=" * 60,
            f"Total transformations: {len(transformations)}",
            f"History file: {self.history_file}",
            "",
        ]

        if transformations:
            lines.append("Recent transformations (most recent first):")
            lines.append("")

            for i, entry in enumerate(reversed(transformations[-10:])):
                timestamp = entry.get("timestamp", "Unknown")
                trans_type = entry.get("transformation_type", "Unknown")
                flow = entry.get("flow_name", "Unknown")
                desc = entry.get("description", "No description")

                lines.append(f"{len(transformations) - i}. [{timestamp}]")
                lines.append(f"   Type: {trans_type}")
                lines.append(f"   Flow: {flow}")
                lines.append(f"   Description: {desc}")
                lines.append(f"   Mappings: {len(entry.get('mappings', []))}")
                lines.append("")
        else:
            lines.append("No transformations in history")

        lines.append("=" * 60)

        return "\n".join(lines)

    def mark_rollback_executed(self, steps: int):
        """
        Mark transformations as rolled back in history.

        Args:
            steps: Number of transformations that were rolled back
        """
        transformations = self.history.get("transformations", [])

        if steps > len(transformations):
            return

        # Mark the rolled-back transformations
        for i in range(len(transformations) - steps, len(transformations)):
            transformations[i]["rolled_back"] = True
            transformations[i]["rolled_back_at"] = datetime.now().isoformat()

        self._save_history()

    def record_rollback(
        self, steps: int, spec_file: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Record a rollback operation in history.

        Args:
            steps: Number of transformations that were rolled back
            spec_file: Path to the spec file (for checksums)

        Returns:
            The rollback history entry
        """
        # Get the transformations that were rolled back
        transformations = self.history.get("transformations", [])
        rolled_back = transformations[-steps:] if steps <= len(transformations) else []

        # Create rollback entry
        entry = {
            "timestamp": datetime.now().isoformat(),
            "transformation_type": "rollback",
            "flow_name": (
                "multiple" if steps > 1 else rolled_back[0].get("flow_name", "unknown")
            ),
            "description": f"Rollback last {steps} transformation(s)",
            "mappings": [],
            "metadata": {
                "steps_rolled_back": steps,
                "rolled_back_transformations": [
                    {
                        "timestamp": t.get("timestamp"),
                        "type": t.get("transformation_type"),
                        "description": t.get("description"),
                    }
                    for t in rolled_back
                ],
            },
            "files_modified": [],
            "checksums_after": {},
            "validation_valid": True,
            "validation_errors": [],
            "validation_warnings": [],
            "can_rollback": False,  # Rollback operations themselves cannot be rolled back
        }

        # Calculate checksum after rollback
        if spec_file and spec_file.exists():
            entry["checksums_after"][str(spec_file)] = self._calculate_checksum(
                spec_file
            )

        # Add to history
        self.history["transformations"].append(entry)

        # Mark previous transformations as rolled back
        self.mark_rollback_executed(steps)

        # Save to file
        self._save_history()

        return entry


class DirectorySynchronizer:
    """
    Synchronizes directory structure with YAML transformations.

    After a transformation is applied to the YAML, this class uses the
    transformation mappings to update the physical directory structure:
    - Rename directories when sequences change
    - Move directories when phases/steps are reorganized
    - Delete directories when elements are removed
    - Update Python imports to match new paths
    """

    def __init__(self, base_path: Path, dry_run: bool = False):
        """
        Initialize directory synchronizer.

        Args:
            base_path: Base directory containing the project (e.g., config-manager root)
            dry_run: If True, plan operations but don't execute
        """
        self.base_path = base_path
        self.dry_run = dry_run
        self.operations: List[DirectoryOperation] = []

    def plan_synchronization(
        self, plan: "TransformationPlan", spec_data: Dict[str, Any]
    ) -> List[DirectoryOperation]:
        """
        Create a plan of directory operations needed to sync with YAML changes.

        Args:
            plan: The transformation plan that was applied
            spec_data: The NEW specification data after transformation

        Returns:
            List of directory operations to execute
        """
        operations = []

        # Get the flow data
        flow_name = plan.flow_name
        if flow_name not in spec_data.get("flows", {}):
            return operations

        flow = spec_data["flows"][flow_name]

        # Process each mapping
        for mapping in plan.mappings:
            if mapping.element_type == "phase":
                ops = self._plan_phase_operations(mapping, flow)
                operations.extend(ops)
            elif mapping.element_type == "step":
                ops = self._plan_step_operations(mapping, flow)
                operations.extend(ops)

        self.operations = operations
        return operations

    def _plan_phase_operations(
        self, mapping: TransformationMapping, flow: Dict[str, Any]
    ) -> List[DirectoryOperation]:
        """Plan directory operations for a phase transformation."""
        operations = []

        # Find the phase data
        phase_data = None
        for phase in flow.get("phases", []):
            if phase.get("phase_id") == mapping.element_id:
                phase_data = phase
                break

        if not phase_data:
            return operations

        phase_name = phase_data.get("name", mapping.element_id)

        if mapping.operation == "delete":
            # Delete phase directory
            old_dir = self._get_phase_directory(mapping.old_sequence, phase_name)
            if old_dir and old_dir.exists():
                operations.append(
                    DirectoryOperation(
                        operation="delete",
                        source=old_dir,
                        element_id=mapping.element_id,
                        element_type="phase",
                    )
                )

        elif mapping.operation == "renumber":
            # Rename phase directory
            old_dir = self._get_phase_directory(mapping.old_sequence, phase_name)
            new_dir = self._get_phase_directory(mapping.new_sequence, phase_name)

            if old_dir and old_dir.exists() and old_dir != new_dir:
                operations.append(
                    DirectoryOperation(
                        operation="move",
                        source=old_dir,
                        destination=new_dir,
                        element_id=mapping.element_id,
                        element_type="phase",
                        metadata={
                            "old_sequence": mapping.old_sequence,
                            "new_sequence": mapping.new_sequence,
                        },
                    )
                )

        elif mapping.operation == "insert":
            # Create new phase directory
            new_dir = self._get_phase_directory(mapping.new_sequence, phase_name)
            if new_dir:
                operations.append(
                    DirectoryOperation(
                        operation="create",
                        destination=new_dir,
                        element_id=mapping.element_id,
                        element_type="phase",
                        metadata={"phase_data": phase_data},
                    )
                )

        return operations

    def _plan_step_operations(
        self, mapping: TransformationMapping, flow: Dict[str, Any]
    ) -> List[DirectoryOperation]:
        """Plan directory operations for a step transformation."""
        operations = []

        # Find the parent phase
        parent_phase = None
        for phase in flow.get("phases", []):
            if phase.get("phase_id") == mapping.old_parent:
                parent_phase = phase
                break

        if not parent_phase:
            return operations

        # Find step data
        step_data = None
        for step in parent_phase.get("steps", []):
            if step.get("step_id") == mapping.element_id:
                step_data = step
                break

        if not step_data:
            return operations

        phase_seq = parent_phase.get("sequence", 0)
        phase_name = parent_phase.get("name", mapping.old_parent)
        step_name = step_data.get("step_id", mapping.element_id)

        if mapping.operation == "delete":
            # Delete step directory
            old_step_dir = self._get_step_directory(
                phase_seq, phase_name, mapping.old_sequence, step_name
            )
            if old_step_dir and old_step_dir.exists():
                operations.append(
                    DirectoryOperation(
                        operation="delete",
                        source=old_step_dir,
                        element_id=mapping.element_id,
                        element_type="step",
                    )
                )

        elif mapping.operation == "renumber":
            # Rename step directory
            old_step_dir = self._get_step_directory(
                phase_seq, phase_name, mapping.old_sequence, step_name
            )
            new_step_dir = self._get_step_directory(
                phase_seq, phase_name, mapping.new_sequence, step_name
            )

            if old_step_dir and old_step_dir.exists() and old_step_dir != new_step_dir:
                operations.append(
                    DirectoryOperation(
                        operation="move",
                        source=old_step_dir,
                        destination=new_step_dir,
                        element_id=mapping.element_id,
                        element_type="step",
                        metadata={
                            "old_sequence": mapping.old_sequence,
                            "new_sequence": mapping.new_sequence,
                        },
                    )
                )

        elif mapping.operation == "insert":
            # Create new step directory
            new_step_dir = self._get_step_directory(
                phase_seq, phase_name, mapping.new_sequence, step_name
            )
            if new_step_dir:
                operations.append(
                    DirectoryOperation(
                        operation="create",
                        destination=new_step_dir,
                        element_id=mapping.element_id,
                        element_type="step",
                        metadata={"step_data": step_data},
                    )
                )

        return operations

    def _get_phase_directory(self, sequence: int, phase_name: str) -> Optional[Path]:
        """Get the directory path for a phase."""
        # Convert phase name to directory name (lowercase, underscores)
        dir_name_part = phase_name.lower().replace(" ", "_").replace("-", "_")
        # Clean up any special characters
        dir_name_part = re.sub(r"[^a-z0-9_]", "", dir_name_part)

        dir_name = f"phase_{sequence}_{dir_name_part}"

        # Look for phases directory in base_path
        phases_dir = self.base_path / "phases"
        if not phases_dir.exists():
            # Try alternative locations
            phases_dir = self.base_path / "src" / "phases"

        if phases_dir.exists():
            return phases_dir / dir_name

        return None

    def _get_step_directory(
        self, phase_seq: int, phase_name: str, step_seq: int, step_name: str
    ) -> Optional[Path]:
        """Get the directory path for a step within a phase."""
        phase_dir = self._get_phase_directory(phase_seq, phase_name)
        if not phase_dir:
            return None

        # Convert step name to directory name
        dir_name_part = step_name.lower().replace(" ", "_").replace("-", "_")
        dir_name_part = re.sub(r"[^a-z0-9_]", "", dir_name_part)

        step_dir_name = f"step_{step_seq}_{dir_name_part}"
        return phase_dir / step_dir_name

    def execute_operations(
        self, operations: Optional[List[DirectoryOperation]] = None
    ) -> Dict[str, Any]:
        """
        Execute the planned directory operations.

        Args:
            operations: List of operations to execute (uses self.operations if None)

        Returns:
            Dict with execution results
        """
        if operations is None:
            operations = self.operations

        results = {
            "operations_planned": len(operations),
            "operations_executed": 0,
            "operations_failed": 0,
            "errors": [],
            "dry_run": self.dry_run,
        }

        for op in operations:
            try:
                if self.dry_run:
                    print(f"  [DRY RUN] {op}")
                    results["operations_executed"] += 1
                else:
                    self._execute_operation(op)
                    print(f"  ✓ {op}")
                    results["operations_executed"] += 1
            except Exception as e:
                error_msg = f"Failed to execute {op}: {e}"
                results["errors"].append(error_msg)
                results["operations_failed"] += 1
                print(f"  ✗ {error_msg}")

        return results

    def _execute_operation(self, op: DirectoryOperation):
        """Execute a single directory operation."""
        if op.operation == "move":
            if op.source and op.destination:
                # Ensure parent directory exists
                op.destination.parent.mkdir(parents=True, exist_ok=True)
                # Move/rename directory
                shutil.move(str(op.source), str(op.destination))

        elif op.operation == "delete":
            if op.source and op.source.exists():
                if op.source.is_dir():
                    shutil.rmtree(op.source)
                else:
                    op.source.unlink()

        elif op.operation == "create":
            if op.destination:
                op.destination.mkdir(parents=True, exist_ok=True)
                # Create basic __init__.py
                init_file = op.destination / "__init__.py"
                if not init_file.exists():
                    init_file.write_text(
                        '"""Auto-generated by transformation system."""\n'
                    )

    def preview_operations(
        self, operations: Optional[List[DirectoryOperation]] = None
    ) -> str:
        """Generate a preview of directory operations."""
        if operations is None:
            operations = self.operations

        lines = [
            "=" * 60,
            "DIRECTORY SYNCHRONIZATION PREVIEW",
            "=" * 60,
            f"Base Path: {self.base_path}",
            f"Operations: {len(operations)}",
            "",
            "=" * 60,
            "OPERATIONS",
            "=" * 60,
            "",
        ]

        for op in operations:
            lines.append(f"  {op}")

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)


class CodePathUpdater:
    """
    Updates code paths after directory transformations.

    After directories are moved/renamed, this class finds and updates:
    - Python import statements
    - Configuration file paths
    - Documentation references
    - Hardcoded path strings
    """

    def __init__(self, base_path: Path, dry_run: bool = False):
        """
        Initialize code path updater.

        Args:
            base_path: Base directory containing the project
            dry_run: If True, show changes without applying
        """
        self.base_path = base_path
        self.dry_run = dry_run
        self.path_mappings: Dict[str, str] = {}  # old_path -> new_path
        self.updates: List[Dict[str, Any]] = []

    def build_path_mappings(self, dir_operations: List[DirectoryOperation]):
        """
        Build a mapping of old paths to new paths from directory operations.

        Args:
            dir_operations: List of directory operations (moves, deletes)
        """
        self.path_mappings = {}

        for op in dir_operations:
            if op.operation == "move" and op.source and op.destination:
                # Get relative paths from base
                try:
                    old_rel = op.source.relative_to(self.base_path)
                    new_rel = op.destination.relative_to(self.base_path)

                    # Convert to Python module path
                    old_module = str(old_rel).replace("/", ".").replace("\\", ".")
                    new_module = str(new_rel).replace("/", ".").replace("\\", ".")

                    self.path_mappings[old_module] = new_module

                    # Also map as file paths
                    self.path_mappings[str(old_rel)] = str(new_rel)
                    self.path_mappings[str(old_rel).replace("\\", "/")] = str(
                        new_rel
                    ).replace("\\", "/")

                except ValueError:
                    # Path not relative to base, skip
                    pass

    def find_python_files(self) -> List[Path]:
        """Find all Python files in the project."""
        python_files = []

        for pattern in ["**/*.py", "**/*.pyi"]:
            python_files.extend(self.base_path.glob(pattern))

        return python_files

    def find_config_files(self) -> List[Path]:
        """Find all configuration files."""
        config_files = []

        for pattern in [
            "**/*.yml",
            "**/*.yaml",
            "**/*.json",
            "**/*.toml",
            "**/*.ini",
            "**/*.cfg",
        ]:
            config_files.extend(self.base_path.glob(pattern))

        return config_files

    def find_documentation_files(self) -> List[Path]:
        """Find all documentation files."""
        doc_files = []

        for pattern in ["**/*.md", "**/*.rst", "**/*.txt"]:
            doc_files.extend(self.base_path.glob(pattern))

        return doc_files

    def update_python_imports(self) -> int:
        """
        Update Python import statements in all .py files.

        Returns:
            Number of files updated
        """
        if not self.path_mappings:
            return 0

        files_updated = 0
        python_files = self.find_python_files()

        for py_file in python_files:
            try:
                content = py_file.read_text(encoding="utf-8")
                updated_content = content
                changes_made = []

                # Update various import patterns
                for old_path, new_path in self.path_mappings.items():
                    # Skip non-module paths
                    if "/" in old_path or "\\" in old_path:
                        continue

                    # Pattern 1: from old.path import X
                    pattern1 = rf"\bfrom\s+{re.escape(old_path)}\s+import\s+"
                    replacement1 = f"from {new_path} import "
                    if re.search(pattern1, updated_content):
                        updated_content = re.sub(
                            pattern1, replacement1, updated_content
                        )
                        changes_made.append(
                            f"from {old_path} import → from {new_path} import"
                        )

                    # Pattern 2: from old.path.module import X
                    pattern2 = rf"\bfrom\s+{re.escape(old_path)}\."
                    replacement2 = f"from {new_path}."
                    if re.search(pattern2, updated_content):
                        updated_content = re.sub(
                            pattern2, replacement2, updated_content
                        )
                        changes_made.append(f"from {old_path}.* → from {new_path}.*")

                    # Pattern 3: import old.path
                    pattern3 = rf"\bimport\s+{re.escape(old_path)}\b"
                    replacement3 = f"import {new_path}"
                    if re.search(pattern3, updated_content):
                        updated_content = re.sub(
                            pattern3, replacement3, updated_content
                        )
                        changes_made.append(f"import {old_path} → import {new_path}")

                if updated_content != content:
                    if not self.dry_run:
                        py_file.write_text(updated_content, encoding="utf-8")

                    self.updates.append(
                        {
                            "file": str(py_file.relative_to(self.base_path)),
                            "type": "python_import",
                            "changes": changes_made,
                        }
                    )

                    files_updated += 1
                    print(
                        f"  ✓ Updated {py_file.relative_to(self.base_path)}: {len(changes_made)} import(s)"
                    )

            except Exception as e:
                print(f"  ✗ Error updating {py_file}: {e}")

        return files_updated

    def update_config_paths(self) -> int:
        """
        Update file paths in configuration files.

        Returns:
            Number of files updated
        """
        if not self.path_mappings:
            return 0

        files_updated = 0
        config_files = self.find_config_files()

        for config_file in config_files:
            try:
                content = config_file.read_text(encoding="utf-8")
                updated_content = content
                changes_made = []

                # Update path references
                for old_path, new_path in self.path_mappings.items():
                    # Only update file path patterns (with / or \)
                    if "/" not in old_path and "\\" not in old_path:
                        continue

                    # Escape special regex characters in paths
                    old_escaped = re.escape(old_path)

                    # Update quoted paths
                    patterns = [
                        (rf'["\']({old_escaped})["\']', f'"{new_path}"'),
                        (rf":\s+({old_escaped})\b", f": {new_path}"),
                        (rf"=\s*({old_escaped})\b", f"= {new_path}"),
                    ]

                    for pattern, replacement_base in patterns:
                        if re.search(pattern, updated_content):
                            # Preserve the matched prefix
                            updated_content = re.sub(
                                pattern,
                                lambda m: m.group(0).replace(old_path, new_path),
                                updated_content,
                            )
                            changes_made.append(f"{old_path} → {new_path}")

                if updated_content != content:
                    if not self.dry_run:
                        config_file.write_text(updated_content, encoding="utf-8")

                    self.updates.append(
                        {
                            "file": str(config_file.relative_to(self.base_path)),
                            "type": "config_path",
                            "changes": list(set(changes_made)),  # Deduplicate
                        }
                    )

                    files_updated += 1
                    print(
                        f"  ✓ Updated {config_file.relative_to(self.base_path)}: {len(set(changes_made))} path(s)"
                    )

            except Exception as e:
                print(f"  ✗ Error updating {config_file}: {e}")

        return files_updated

    def update_documentation_paths(self) -> int:
        """
        Update file paths in documentation files.

        Returns:
            Number of files updated
        """
        if not self.path_mappings:
            return 0

        files_updated = 0
        doc_files = self.find_documentation_files()

        for doc_file in doc_files:
            try:
                content = doc_file.read_text(encoding="utf-8")
                updated_content = content
                changes_made = []

                # Update markdown links and file references
                for old_path, new_path in self.path_mappings.items():
                    # Only update file path patterns
                    if "/" not in old_path and "\\" not in old_path:
                        continue

                    old_escaped = re.escape(old_path)

                    # Markdown link patterns
                    patterns = [
                        # [text](path)
                        (
                            rf"\[([^\]]+)\]\({old_escaped}([^\)]*)\)",
                            lambda m: f"[{m.group(1)}]({new_path}{m.group(2)})",
                        ),
                        # `path`
                        (rf"`{old_escaped}`", f"`{new_path}`"),
                        # Plain path references
                        (rf"\b{old_escaped}\b", new_path),
                    ]

                    for pattern, replacement in patterns:
                        if callable(replacement):
                            if re.search(pattern, updated_content):
                                updated_content = re.sub(
                                    pattern, replacement, updated_content
                                )
                                changes_made.append(f"{old_path} → {new_path}")
                        else:
                            if re.search(pattern, updated_content):
                                updated_content = re.sub(
                                    pattern, replacement, updated_content
                                )
                                changes_made.append(f"{old_path} → {new_path}")

                if updated_content != content:
                    if not self.dry_run:
                        doc_file.write_text(updated_content, encoding="utf-8")

                    self.updates.append(
                        {
                            "file": str(doc_file.relative_to(self.base_path)),
                            "type": "documentation_path",
                            "changes": list(set(changes_made)),
                        }
                    )

                    files_updated += 1
                    print(
                        f"  ✓ Updated {doc_file.relative_to(self.base_path)}: {len(set(changes_made))} path(s)"
                    )

            except Exception as e:
                print(f"  ✗ Error updating {doc_file}: {e}")

        return files_updated

    def update_all(self, dir_operations: List[DirectoryOperation]) -> Dict[str, Any]:
        """
        Update all code paths after directory operations.

        Args:
            dir_operations: List of directory operations that were executed

        Returns:
            Summary of updates performed
        """
        # Build path mappings
        self.build_path_mappings(dir_operations)

        if not self.path_mappings:
            return {
                "path_mappings": 0,
                "python_files_updated": 0,
                "config_files_updated": 0,
                "doc_files_updated": 0,
                "total_files_updated": 0,
            }

        print(f"\n📝 Updating code paths ({len(self.path_mappings)} mappings)...")

        if self.dry_run:
            print("  [DRY RUN MODE]")

        # Show path mappings
        print("\n  Path mappings:")
        for old, new in list(self.path_mappings.items())[:10]:  # Show first 10
            print(f"    {old} → {new}")
        if len(self.path_mappings) > 10:
            print(f"    ... and {len(self.path_mappings) - 10} more")

        # Update Python imports
        print("\n  Updating Python imports...")
        python_updated = self.update_python_imports()

        # Update config files
        print("\n  Updating configuration files...")
        config_updated = self.update_config_paths()

        # Update documentation
        print("\n  Updating documentation...")
        doc_updated = self.update_documentation_paths()

        total = python_updated + config_updated + doc_updated

        print(f"\n  ✅ Code path updates complete:")
        print(f"    Python files: {python_updated}")
        print(f"    Config files: {config_updated}")
        print(f"    Doc files: {doc_updated}")
        print(f"    Total: {total}")

        return {
            "path_mappings": len(self.path_mappings),
            "python_files_updated": python_updated,
            "config_files_updated": config_updated,
            "doc_files_updated": doc_updated,
            "total_files_updated": total,
            "updates": self.updates,
        }


class ControlFlowTransformation:
    """
    Manages safe transformations of control flow specifications.

    Implements a three-phase workflow:
    1. PLAN: Create transformation plan with mappings
    2. VALIDATE: Verify transformation maintains integrity
    3. APPLY: Execute transformation and update files

    Example:
        transformer = ControlFlowTransformation(spec_data)

        # Create a renumbering plan
        plan = transformer.plan_renumber(
            flow_name="main_config_flow",
            phase_id="discovery",
            start_from=1
        )

        # Validate the plan
        validation = transformer.validate(plan)
        if validation.valid:
            # Apply the transformation
            new_spec = transformer.apply(plan)
    """

    def __init__(self, original_spec: Dict[str, Any], spec_file: Optional[Path] = None):
        """
        Initialize transformer with original specification.

        Args:
            original_spec: The original control flow specification (parsed YAML)
            spec_file: Optional path to the specification file
        """
        self.original_spec = copy.deepcopy(original_spec)
        self.spec_file = spec_file
        self.transformation_history: List[TransformationPlan] = []

        # Initialize persistent history tracking
        if spec_file:
            history_file = spec_file.parent / ".transformation_history.json"
        else:
            history_file = Path.cwd() / ".transformation_history.json"
        self.history_manager = TransformationHistory(history_file)

    def plan_renumber(
        self,
        flow_name: str,
        phase_id: Optional[str] = None,
        start_from: int = 1,
        strategy: str = "compact",
    ) -> TransformationPlan:
        """
        Create a plan to renumber sequences.

        Args:
            flow_name: Name of the flow to renumber
            phase_id: Optional phase ID (None = renumber all phases)
            start_from: Starting sequence number
            strategy: "compact" (remove gaps) or "minimal" (preserve gaps)

        Returns:
            TransformationPlan with renumber mappings
        """
        plan = TransformationPlan(
            transformation_type=TransformationType.RENUMBER,
            flow_name=flow_name,
            description=f"Renumber sequences in {flow_name}"
            + (f" (phase: {phase_id})" if phase_id else ""),
            metadata={
                "start_from": start_from,
                "strategy": strategy,
                "phase_id": phase_id,
            },
        )

        if flow_name not in self.original_spec.get("flows", {}):
            raise ValueError(f"Flow '{flow_name}' not found")

        flow = self.original_spec["flows"][flow_name]

        # Renumber phases
        if "phases" in flow and phase_id is None:
            phases = flow["phases"]
            sorted_phases = sorted(phases, key=lambda p: p.get("sequence", 0))

            for idx, phase in enumerate(sorted_phases):
                old_seq = phase.get("sequence", 0)
                new_seq = (
                    start_from + idx
                    if strategy == "compact"
                    else max(old_seq, start_from + idx)
                )

                if old_seq != new_seq:
                    plan.add_mapping(
                        TransformationMapping(
                            element_type="phase",
                            element_id=phase.get("phase_id", "unknown"),
                            old_sequence=old_seq,
                            new_sequence=new_seq,
                            operation="renumber",
                        )
                    )

        # Renumber steps within phases
        if "phases" in flow:
            phases_to_process = flow["phases"]
            if phase_id:
                phases_to_process = [
                    p for p in phases_to_process if p.get("phase_id") == phase_id
                ]

            for phase in phases_to_process:
                if "steps" in phase:
                    steps = phase["steps"]
                    sorted_steps = sorted(steps, key=lambda s: s.get("sequence", 0))

                    for step_idx, step in enumerate(sorted_steps):
                        old_step_seq = step.get("sequence", 0)
                        new_step_seq = (
                            start_from + step_idx
                            if strategy == "compact"
                            else max(old_step_seq, start_from + step_idx)
                        )

                        if old_step_seq != new_step_seq:
                            plan.add_mapping(
                                TransformationMapping(
                                    element_type="step",
                                    element_id=step.get("step_id", "unknown"),
                                    old_sequence=old_step_seq,
                                    new_sequence=new_step_seq,
                                    old_parent=phase.get("phase_id"),
                                    new_parent=phase.get("phase_id"),
                                    operation="renumber",
                                )
                            )

        # Handle flows with direct steps (no phases)
        elif "flow_steps" in flow:
            steps = flow["flow_steps"]
            sorted_steps = sorted(steps, key=lambda s: s.get("sequence", 0))

            for step_idx, step in enumerate(sorted_steps):
                old_step_seq = step.get("sequence", 0)
                new_step_seq = (
                    start_from + step_idx
                    if strategy == "compact"
                    else max(old_step_seq, start_from + step_idx)
                )

                if old_step_seq != new_step_seq:
                    plan.add_mapping(
                        TransformationMapping(
                            element_type="flow_step",
                            element_id=step.get("step_id", "unknown"),
                            old_sequence=old_step_seq,
                            new_sequence=new_step_seq,
                            operation="renumber",
                        )
                    )

        return plan

    def plan_insert(
        self,
        flow_name: str,
        phase_id: Optional[str],
        new_element: Dict[str, Any],
        insert_after: Optional[str] = None,
        insert_before: Optional[str] = None,
        cascade_renumber: bool = True,
    ) -> TransformationPlan:
        """
        Create a plan to insert a new phase or step.

        Args:
            flow_name: Name of the flow
            phase_id: Phase ID (None if inserting a phase)
            new_element: The new phase or step data
            insert_after: Insert after this element ID
            insert_before: Insert before this element ID
            cascade_renumber: Whether to renumber subsequent elements

        Returns:
            TransformationPlan with insert and optional renumber mappings
        """
        element_type = "step" if phase_id else "phase"
        new_id = new_element.get("step_id" if phase_id else "phase_id", "unknown")

        plan = TransformationPlan(
            transformation_type=TransformationType.INSERT,
            flow_name=flow_name,
            description=f"Insert {element_type} '{new_id}'"
            + (f" in phase {phase_id}" if phase_id else ""),
            metadata={
                "phase_id": phase_id,
                "insert_after": insert_after,
                "insert_before": insert_before,
                "cascade_renumber": cascade_renumber,
                "new_element": new_element,
            },
        )

        if flow_name not in self.original_spec.get("flows", {}):
            raise ValueError(f"Flow '{flow_name}' not found")

        flow = self.original_spec["flows"][flow_name]

        # Determine insertion point and sequence
        insert_seq = None

        if phase_id is None:
            # Inserting a phase
            if "phases" not in flow:
                raise ValueError(f"Flow '{flow_name}' has no phases")

            phases = flow["phases"]

            if insert_after:
                for i, p in enumerate(phases):
                    if p.get("phase_id") == insert_after:
                        insert_seq = p.get("sequence", 0) + 1
                        break
            elif insert_before:
                for i, p in enumerate(phases):
                    if p.get("phase_id") == insert_before:
                        insert_seq = p.get("sequence", 0)
                        break
            else:
                # Insert at end
                insert_seq = max([p.get("sequence", 0) for p in phases], default=0) + 1

            if insert_seq is None:
                raise ValueError(f"Insertion point not found")

            # Add insert mapping
            plan.add_mapping(
                TransformationMapping(
                    element_type="phase",
                    element_id=new_id,
                    old_sequence=None,
                    new_sequence=insert_seq,
                    operation="insert",
                    metadata={"element_data": new_element},
                )
            )

            # Add renumber mappings for affected phases
            if cascade_renumber:
                for phase in phases:
                    phase_seq = phase.get("sequence", 0)
                    if phase_seq >= insert_seq:
                        plan.add_mapping(
                            TransformationMapping(
                                element_type="phase",
                                element_id=phase.get("phase_id"),
                                old_sequence=phase_seq,
                                new_sequence=phase_seq + 1,
                                operation="renumber",
                            )
                        )

        else:
            # Inserting a step
            target_phase = None
            for phase in flow.get("phases", []):
                if phase.get("phase_id") == phase_id:
                    target_phase = phase
                    break

            if not target_phase:
                raise ValueError(f"Phase '{phase_id}' not found")

            if "steps" not in target_phase:
                target_phase["steps"] = []

            steps = target_phase["steps"]

            if insert_after:
                for i, s in enumerate(steps):
                    if s.get("step_id") == insert_after:
                        insert_seq = s.get("sequence", 0) + 1
                        break
            elif insert_before:
                for i, s in enumerate(steps):
                    if s.get("step_id") == insert_before:
                        insert_seq = s.get("sequence", 0)
                        break
            else:
                # Insert at end
                insert_seq = max([s.get("sequence", 0) for s in steps], default=0) + 1

            if insert_seq is None:
                raise ValueError(f"Insertion point not found")

            # Add insert mapping
            plan.add_mapping(
                TransformationMapping(
                    element_type="step",
                    element_id=new_id,
                    old_sequence=None,
                    new_sequence=insert_seq,
                    old_parent=phase_id,
                    new_parent=phase_id,
                    operation="insert",
                    metadata={"element_data": new_element},
                )
            )

            # Add renumber mappings for affected steps
            if cascade_renumber:
                for step in steps:
                    step_seq = step.get("sequence", 0)
                    if step_seq >= insert_seq:
                        plan.add_mapping(
                            TransformationMapping(
                                element_type="step",
                                element_id=step.get("step_id"),
                                old_sequence=step_seq,
                                new_sequence=step_seq + 1,
                                old_parent=phase_id,
                                new_parent=phase_id,
                                operation="renumber",
                            )
                        )

        return plan

    def plan_delete(
        self,
        flow_name: str,
        element_id: str,
        phase_id: Optional[str] = None,
        cascade_renumber: bool = True,
    ) -> TransformationPlan:
        """
        Create a plan to delete a phase or step.

        Args:
            flow_name: Name of the flow
            element_id: ID of the element to delete
            phase_id: Parent phase ID if deleting a step
            cascade_renumber: Whether to renumber subsequent elements

        Returns:
            TransformationPlan with delete and optional renumber mappings
        """
        element_type = "step" if phase_id else "phase"

        plan = TransformationPlan(
            transformation_type=TransformationType.DELETE,
            flow_name=flow_name,
            description=f"Delete {element_type} '{element_id}'"
            + (f" from phase {phase_id}" if phase_id else ""),
            metadata={
                "element_id": element_id,
                "phase_id": phase_id,
                "cascade_renumber": cascade_renumber,
                "deleted_element": {},  # Will be filled in below
            },
        )

        if flow_name not in self.original_spec.get("flows", {}):
            raise ValueError(f"Flow '{flow_name}' not found")

        flow = self.original_spec["flows"][flow_name]

        if phase_id is None:
            # Deleting a phase
            if "phases" not in flow:
                raise ValueError(f"Flow '{flow_name}' has no phases")

            phases = flow["phases"]
            deleted_phase = None

            for phase in phases:
                if phase.get("phase_id") == element_id:
                    deleted_phase = phase
                    break

            if not deleted_phase:
                raise ValueError(f"Phase '{element_id}' not found")

            deleted_seq = deleted_phase.get("sequence", 0)

            # Store deleted element in plan metadata for rollback
            plan.metadata["deleted_element"] = copy.deepcopy(deleted_phase)

            # Add delete mapping
            plan.add_mapping(
                TransformationMapping(
                    element_type="phase",
                    element_id=element_id,
                    old_sequence=deleted_seq,
                    new_sequence=None,
                    operation="delete",
                    metadata={"element_data": deleted_phase},
                )
            )

            # Add renumber mappings for subsequent phases
            if cascade_renumber:
                for phase in phases:
                    phase_seq = phase.get("sequence", 0)
                    if phase_seq > deleted_seq and phase.get("phase_id") != element_id:
                        plan.add_mapping(
                            TransformationMapping(
                                element_type="phase",
                                element_id=phase.get("phase_id"),
                                old_sequence=phase_seq,
                                new_sequence=phase_seq - 1,
                                operation="renumber",
                            )
                        )

        else:
            # Deleting a step
            target_phase = None
            for phase in flow.get("phases", []):
                if phase.get("phase_id") == phase_id:
                    target_phase = phase
                    break

            if not target_phase:
                raise ValueError(f"Phase '{phase_id}' not found")

            if "steps" not in target_phase:
                raise ValueError(f"Phase '{phase_id}' has no steps")

            steps = target_phase["steps"]
            deleted_step = None

            for step in steps:
                if step.get("step_id") == element_id:
                    deleted_step = step
                    break

            if not deleted_step:
                raise ValueError(f"Step '{element_id}' not found in phase '{phase_id}'")

            deleted_seq = deleted_step.get("sequence", 0)

            # Store deleted element in plan metadata for rollback
            plan.metadata["deleted_element"] = copy.deepcopy(deleted_step)

            # Add delete mapping
            plan.add_mapping(
                TransformationMapping(
                    element_type="step",
                    element_id=element_id,
                    old_sequence=deleted_seq,
                    new_sequence=None,
                    old_parent=phase_id,
                    new_parent=None,
                    operation="delete",
                    metadata={"element_data": deleted_step},
                )
            )

            # Add renumber mappings for subsequent steps
            if cascade_renumber:
                for step in steps:
                    step_seq = step.get("sequence", 0)
                    if step_seq > deleted_seq and step.get("step_id") != element_id:
                        plan.add_mapping(
                            TransformationMapping(
                                element_type="step",
                                element_id=step.get("step_id"),
                                old_sequence=step_seq,
                                new_sequence=step_seq - 1,
                                old_parent=phase_id,
                                new_parent=phase_id,
                                operation="renumber",
                            )
                        )

        return plan

    def validate(self, plan: TransformationPlan) -> ValidationResult:
        """
        Validate a transformation plan.

        Checks:
        - Dependency integrity (no broken dependencies)
        - Data flow consistency (artifacts produced/consumed match)
        - Sequence consistency (no duplicate sequences)
        - Reference validity (all IDs are valid)

        Args:
            plan: The transformation plan to validate

        Returns:
            ValidationResult with status and any errors/warnings
        """
        result = ValidationResult(status=ValidationStatus.VALID, valid=True)

        # Create a virtual spec with transformations applied
        virtual_spec = self._apply_plan_to_virtual_spec(plan)

        # Check 1: Sequence uniqueness
        result.checks_performed["sequence_uniqueness"] = True
        self._validate_sequence_uniqueness(virtual_spec, plan.flow_name, result)

        # Check 2: Dependency integrity
        result.checks_performed["dependency_integrity"] = True
        self._validate_dependencies(virtual_spec, plan.flow_name, result)

        # Check 3: Artifact flow
        result.checks_performed["artifact_flow"] = True
        self._validate_artifact_flow(virtual_spec, plan.flow_name, result)

        # Check 4: Reference validity
        result.checks_performed["reference_validity"] = True
        self._validate_references(virtual_spec, plan.flow_name, result)

        # Store result in plan
        plan.validation_result = result

        return result

    def _apply_plan_to_virtual_spec(
        self, plan: TransformationPlan, spec: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Apply transformation plan to a virtual copy of the spec.

        Args:
            plan: The transformation plan to apply
            spec: Optional specification to transform (defaults to self.original_spec)

        Returns:
            Transformed specification

        NOTE: This method has been refactored to use universal structure operation
        libraries instead of inline manipulation logic. This eliminates code
        duplication and ensures consistent behavior across the system.
        """
        virtual_spec = copy.deepcopy(spec if spec is not None else self.original_spec)

        if plan.flow_name not in virtual_spec.get("flows", {}):
            return virtual_spec

        flow = virtual_spec["flows"][plan.flow_name]

        # Initialize deleter and inserter (universal libraries)
        deleter = StructureDeleter()
        inserter = StructureInserter()

        # Apply deletions first (using StructureDeleter library)
        for mapping in plan.get_deletes():
            if mapping.element_type == "phase":
                operation = DeleteOperation(
                    element_id=mapping.element_id,
                    cascade_renumber=False,  # Manual renumber via plan mappings
                    element_path="phases",
                    id_field="phase_id",
                )
                result = deleter.delete_element(flow, operation)
                if not result.success:
                    print(f"⚠️  Delete failed: {result.errors}")

            elif mapping.element_type == "step":
                operation = DeleteOperation(
                    element_id=mapping.element_id,
                    cascade_renumber=False,
                    element_path="steps",
                    id_field="step_id",
                    parent_path="phases",
                    parent_id=mapping.old_parent,
                    parent_id_field="phase_id",
                )
                result = deleter.delete_element(flow, operation)
                if not result.success:
                    print(f"⚠️  Delete failed: {result.errors}")

        # Apply inserts (using StructureInserter library)
        for mapping in plan.get_inserts():
            new_element = mapping.metadata.get("element_data", {})
            new_element["sequence"] = mapping.new_sequence

            if mapping.element_type == "phase":
                operation = InsertOperation(
                    new_element=new_element,
                    insertion_point=InsertionPoint(
                        position=InsertPosition.AT_SEQUENCE,
                        target_sequence=mapping.new_sequence,
                    ),
                    cascade_renumber=False,  # Manual renumber via plan mappings
                    element_path="phases",
                    id_field="phase_id",
                )
                result = inserter.insert_element(flow, operation)
                if not result.success:
                    print(f"⚠️  Insert failed: {result.errors}")

            elif mapping.element_type == "step":
                operation = InsertOperation(
                    new_element=new_element,
                    insertion_point=InsertionPoint(
                        position=InsertPosition.AT_SEQUENCE,
                        target_sequence=mapping.new_sequence,
                    ),
                    cascade_renumber=False,
                    element_path="steps",
                    id_field="step_id",
                    parent_path="phases",
                    parent_id=mapping.new_parent,
                    parent_id_field="phase_id",
                )
                result = inserter.insert_element(flow, operation)
                if not result.success:
                    print(f"⚠️  Insert failed: {result.errors}")

        # Apply renumbers (using StructureRenumberer library)
        renumberer = StructureRenumberer()

        # Group renumber mappings by scope (phases, steps per phase, flow_steps)
        phase_mappings = {}
        step_mappings = {}  # {phase_id: {step_id: new_seq}}
        flow_step_mappings = {}

        for mapping in plan.get_renumbers():
            if mapping.element_type == "phase":
                phase_mappings[mapping.element_id] = mapping.new_sequence
            elif mapping.element_type == "step":
                phase_id = mapping.old_parent
                if phase_id not in step_mappings:
                    step_mappings[phase_id] = {}
                step_mappings[phase_id][mapping.element_id] = mapping.new_sequence
            elif mapping.element_type == "flow_step":
                flow_step_mappings[mapping.element_id] = mapping.new_sequence

        # Apply phase renumbering
        if phase_mappings:
            operation = RenumberOperation(
                strategy=RenumberStrategy.EXPLICIT,
                explicit_mappings=phase_mappings,
                element_path="phases",
                id_field="phase_id",
            )
            result = renumberer.renumber(flow, operation)
            if not result.success:
                print(f"⚠️  Phase renumber failed: {result.errors}")

        # Apply step renumbering (per phase)
        for phase_id, mappings in step_mappings.items():
            operation = RenumberOperation(
                strategy=RenumberStrategy.EXPLICIT,
                explicit_mappings=mappings,
                element_path="steps",
                id_field="step_id",
                parent_path="phases",
                parent_id=phase_id,
                parent_id_field="phase_id",
            )
            result = renumberer.renumber(flow, operation)
            if not result.success:
                print(f"⚠️  Step renumber failed for phase {phase_id}: {result.errors}")

        # Apply flow_step renumbering
        if flow_step_mappings:
            operation = RenumberOperation(
                strategy=RenumberStrategy.EXPLICIT,
                explicit_mappings=flow_step_mappings,
                element_path="flow_steps",
                id_field="step_id",
            )
            result = renumberer.renumber(flow, operation)
            if not result.success:
                print(f"⚠️  Flow step renumber failed: {result.errors}")

        return virtual_spec

    def _validate_sequence_uniqueness(
        self, virtual_spec: Dict[str, Any], flow_name: str, result: ValidationResult
    ):
        """Check that all sequences are unique within their scope."""
        if flow_name not in virtual_spec.get("flows", {}):
            return

        flow = virtual_spec["flows"][flow_name]

        # Check phase sequences
        if "phases" in flow:
            phase_seqs = [p.get("sequence") for p in flow["phases"]]
            if len(phase_seqs) != len(set(phase_seqs)):
                result.add_error(f"Duplicate phase sequences in flow '{flow_name}'")

            # Check step sequences within each phase
            for phase in flow["phases"]:
                if "steps" in phase:
                    step_seqs = [s.get("sequence") for s in phase["steps"]]
                    if len(step_seqs) != len(set(step_seqs)):
                        result.add_error(
                            f"Duplicate step sequences in phase '{phase.get('phase_id')}'"
                        )

        # Check flow_step sequences
        if "flow_steps" in flow:
            step_seqs = [s.get("sequence") for s in flow["flow_steps"]]
            if len(step_seqs) != len(set(step_seqs)):
                result.add_error(f"Duplicate flow_step sequences in flow '{flow_name}'")

    def _validate_dependencies(
        self, virtual_spec: Dict[str, Any], flow_name: str, result: ValidationResult
    ):
        """Check that all dependencies still exist after transformation."""
        if flow_name not in virtual_spec.get("flows", {}):
            return

        flow = virtual_spec["flows"][flow_name]

        # Collect all step IDs
        all_step_ids = set()

        if "phases" in flow:
            for phase in flow["phases"]:
                if "steps" in phase:
                    for step in phase["steps"]:
                        all_step_ids.add(step.get("step_id"))

        if "flow_steps" in flow:
            for step in flow["flow_steps"]:
                all_step_ids.add(step.get("step_id"))

        # Check all dependencies
        if "phases" in flow:
            for phase in flow["phases"]:
                if "steps" in phase:
                    for step in phase["steps"]:
                        deps = step.get("dependencies", [])
                        for dep in deps:
                            if dep not in all_step_ids:
                                result.add_error(
                                    f"Step '{step.get('step_id')}' has broken dependency: '{dep}'"
                                )

        if "flow_steps" in flow:
            for step in flow["flow_steps"]:
                deps = step.get("dependencies", [])
                for dep in deps:
                    if dep not in all_step_ids:
                        result.add_error(
                            f"Flow step '{step.get('step_id')}' has broken dependency: '{dep}'"
                        )

    def _validate_artifact_flow(
        self, virtual_spec: Dict[str, Any], flow_name: str, result: ValidationResult
    ):
        """Check that all consumed artifacts are produced by some step."""
        if flow_name not in virtual_spec.get("flows", {}):
            return

        flow = virtual_spec["flows"][flow_name]

        # Collect all produced artifacts
        produced = set()
        consumed = []

        if "phases" in flow:
            for phase in flow["phases"]:
                # Phase-level artifacts
                produced.update(phase.get("artifacts_produced", []))

                if "steps" in phase:
                    for step in phase["steps"]:
                        produced.update(step.get("artifacts_produced", []))

                        for artifact in step.get("artifacts_consumed", []):
                            consumed.append((step.get("step_id"), artifact))

        if "flow_steps" in flow:
            for step in flow["flow_steps"]:
                produced.update(step.get("artifacts_produced", []))

                for artifact in step.get("artifacts_consumed", []):
                    consumed.append((step.get("step_id"), artifact))

        # Check consumed artifacts
        for step_id, artifact in consumed:
            if artifact not in produced:
                result.add_warning(
                    f"Step '{step_id}' consumes artifact '{artifact}' which is not produced by any step"
                )

    def _validate_references(
        self, virtual_spec: Dict[str, Any], flow_name: str, result: ValidationResult
    ):
        """Check that all references (sub_flows, etc.) are valid."""
        if flow_name not in virtual_spec.get("flows", {}):
            return

        flow = virtual_spec["flows"][flow_name]
        all_flows = set(virtual_spec.get("flows", {}).keys())

        # Check sub_flow references
        if "phases" in flow:
            for phase in flow["phases"]:
                sub_flows = phase.get("sub_flows", [])
                for sub_flow in sub_flows:
                    if sub_flow not in all_flows:
                        result.add_error(
                            f"Phase '{phase.get('phase_id')}' references non-existent sub_flow: '{sub_flow}'"
                        )

    def apply(
        self,
        plan: TransformationPlan,
        save: bool = True,
        sync_directories: bool = False,
        project_base_path: Optional[Path] = None,
        dry_run_sync: bool = False,
        update_code_paths: bool = False,
        regenerate_orchestrators: bool = False,
        flow_name: str = "main_config_flow",
    ) -> Dict[str, Any]:
        """
        Apply a transformation plan to create the new specification.

        Args:
            plan: The validated transformation plan
            save: Whether to save the new spec to file
            sync_directories: Whether to synchronize directory structure
            project_base_path: Base path for directory synchronization (required if sync_directories=True)
            dry_run_sync: If True, preview directory operations without executing
            update_code_paths: If True, update Python imports, config paths, and docs after directory sync
            regenerate_orchestrators: If True, regenerate affected orchestrator files after transformation
            flow_name: Flow name for orchestrator regeneration (default: "main_config_flow")

        Returns:
            The new specification with transformations applied

        Raises:
            ValueError: If plan has not been validated or is invalid
        """
        if plan.validation_result is None:
            raise ValueError(
                "Plan must be validated before applying. Call validate() first."
            )

        if not plan.validation_result.valid:
            raise ValueError(
                f"Cannot apply invalid plan. Errors: {plan.validation_result.errors}"
            )

        # Apply transformations to create new spec
        new_spec = self._apply_plan_to_virtual_spec(plan)

        # Save to file if requested (using YAMLSaver library)
        if save and self.spec_file:
            saver = YAMLSaver()
            options = SaveOptions(
                default_flow_style=False,
                sort_keys=False,
                indent=2,
                allow_unicode=True,
                create_backup=False,  # No backup for transformations
            )
            result = saver.save(new_spec, self.spec_file, options)
            if result.success:
                print(f"✅ Applied transformation and saved to {self.spec_file}")
            else:
                print(f"⚠️  Failed to save: {result.errors}")

        # Synchronize directories if requested
        dir_operations = []
        if sync_directories:
            if not project_base_path:
                # Try to infer from spec_file
                if self.spec_file:
                    project_base_path = self.spec_file.parent.parent
                else:
                    raise ValueError(
                        "project_base_path required when sync_directories=True"
                    )

            print(f"\n🔄 Synchronizing directory structure...")
            synchronizer = DirectorySynchronizer(
                project_base_path, dry_run=dry_run_sync
            )

            # Plan directory operations
            dir_operations = synchronizer.plan_synchronization(plan, new_spec)

            if dir_operations:
                print(f"  Planned {len(dir_operations)} directory operations:")
                for op in dir_operations:
                    print(f"    {op}")

                # Execute operations
                print(f"\n  Executing directory operations...")
                results = synchronizer.execute_operations(dir_operations)

                print(f"\n  ✅ Directory sync complete:")
                print(f"    Executed: {results['operations_executed']}")
                print(f"    Failed: {results['operations_failed']}")
                if results["errors"]:
                    print(f"    Errors:")
                    for error in results["errors"]:
                        print(f"      - {error}")

                # Update code paths after directory operations
                if update_code_paths and dir_operations:
                    print(f"\n📝 Updating code paths...")
                    path_updater = CodePathUpdater(
                        project_base_path, dry_run=dry_run_sync
                    )
                    path_results = path_updater.update_all(dir_operations)

                    print(f"\n  ✅ Code path updates complete:")
                    print(f"    Path mappings: {path_results['path_mappings']}")
                    print(f"    Python files: {path_results['python_files_updated']}")
                    print(f"    Config files: {path_results['config_files_updated']}")
                    print(f"    Doc files: {path_results['doc_files_updated']}")
                    print(
                        f"    Total files updated: {path_results['total_files_updated']}"
                    )
            else:
                print("  No directory operations needed")

        # Record transformation in persistent history
        if not dry_run_sync:  # Only record actual transformations, not dry runs
            affected_dirs = [op.source for op in dir_operations if op.source] + [
                op.destination for op in dir_operations if op.destination
            ]
            affected_files = []
            if update_code_paths and "updates" in locals():
                # Get files from path_results if available
                affected_files = [
                    Path(u["file"]) for u in path_results.get("updates", [])
                ]

            history_entry = self.history_manager.record_transformation(
                plan=plan,
                spec_file=self.spec_file if save else None,
                affected_directories=affected_dirs if sync_directories else None,
                affected_files=affected_files if update_code_paths else None,
            )

            print(
                f"\n📝 Transformation recorded in history (entry #{len(self.history_manager.history['transformations'])})"
            )

        # Add to in-memory history
        self.transformation_history.append(plan)

        # Update original spec to new state
        self.original_spec = new_spec

        # Regenerate orchestrators if requested
        if regenerate_orchestrators and not dry_run_sync:
            if not project_base_path:
                if self.spec_file:
                    project_base_path = self.spec_file.parent.parent
                else:
                    print(
                        "⚠️  Cannot regenerate orchestrators: project_base_path not provided"
                    )
                    return new_spec

            print(f"\n🔄 Regenerating affected orchestrators...")
            try:
                from .transformation_regenerator_bridge import (
                    regenerate_after_transformation,
                )

                regen_results = regenerate_after_transformation(
                    plan=plan,
                    spec_file=self.spec_file,
                    project_base_path=project_base_path,
                    flow_name=flow_name,
                )

                print(f"\n  ✅ Orchestrator regeneration complete:")
                print(f"    Regenerated: {len(regen_results['regenerated'])}")
                print(f"    Failed: {len(regen_results['failed'])}")
                print(f"    Skipped: {len(regen_results['skipped'])}")

                if regen_results["regenerated"]:
                    print(f"\n    Updated files:")
                    for file in regen_results["regenerated"]:
                        print(f"      ✓ {file}")

                if regen_results["failed"]:
                    print(f"\n    ⚠️  Failed to regenerate:")
                    for file in regen_results["failed"]:
                        print(f"      ✗ {file}")

            except ImportError as e:
                print(f"⚠️  Could not import regenerator bridge: {e}")
            except Exception as e:
                print(f"⚠️  Error during orchestrator regeneration: {e}")

        return new_spec

    def preview(self, plan: TransformationPlan) -> str:
        """
        Generate a preview of what the transformation will do.

        Args:
            plan: The transformation plan

        Returns:
            Human-readable preview text
        """
        lines = [
            "=" * 60,
            "TRANSFORMATION PREVIEW",
            "=" * 60,
            "",
            plan.summary(),
            "",
            "=" * 60,
            "CHANGES",
            "=" * 60,
            "",
        ]

        for mapping in plan.mappings:
            lines.append(f"  {mapping}")

        lines.append("")

        if plan.validation_result:
            lines.append("=" * 60)
            lines.append("VALIDATION")
            lines.append("=" * 60)
            lines.append("")
            lines.append(str(plan.validation_result))

            if plan.validation_result.errors:
                lines.append("")
                lines.append("Errors:")
                for error in plan.validation_result.errors:
                    lines.append(f"  ❌ {error}")

            if plan.validation_result.warnings:
                lines.append("")
                lines.append("Warnings:")
                for warning in plan.validation_result.warnings:
                    lines.append(f"  ⚠️  {warning}")

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)

    def get_history(self) -> List[TransformationPlan]:
        """Get the in-memory history of transformations applied."""
        return self.transformation_history.copy()

    def get_persistent_history(
        self, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get persistent transformation history from .transformation_history.json.

        Args:
            limit: Maximum number of entries to return (most recent first)

        Returns:
            List of transformation history entries
        """
        return self.history_manager.get_history(limit=limit)

    def show_history_summary(self) -> str:
        """Get a human-readable summary of transformation history."""
        return self.history_manager.summary()

    def can_rollback(self, steps: int = 1) -> Tuple[bool, str]:
        """
        Check if rollback is possible for the last N transformations.

        Args:
            steps: Number of transformations to rollback

        Returns:
            Tuple of (can_rollback, reason_if_not)
        """
        return self.history_manager.can_rollback(steps)

    def _create_inverse_transformation(
        self, entry: Dict[str, Any]
    ) -> TransformationPlan:
        """
        Create an inverse transformation from a history entry.

        Args:
            entry: History entry to reverse

        Returns:
            TransformationPlan that reverses the original transformation
        """
        trans_type = entry.get("transformation_type")
        flow_name = entry.get("flow_name")
        mappings_data = entry.get("mappings", [])
        metadata = entry.get("metadata", {})

        # Create inverse plan based on transformation type
        if trans_type == "renumber":
            # For renumber: swap old and new sequences
            plan = TransformationPlan(
                transformation_type=TransformationType.RENUMBER,
                flow_name=flow_name,
                description=f"Rollback: {entry.get('description')}",
            )

            for mapping_data in mappings_data:
                # Create inverse mapping (swap old and new)
                plan.add_mapping(
                    TransformationMapping(
                        element_type=mapping_data["element_type"],
                        element_id=mapping_data["element_id"],
                        old_sequence=mapping_data["new_sequence"],  # Swapped!
                        new_sequence=mapping_data["old_sequence"],  # Swapped!
                        old_parent=mapping_data.get("new_parent"),  # Swapped!
                        new_parent=mapping_data.get("old_parent"),  # Swapped!
                        operation="renumber",
                    )
                )

        elif trans_type == "insert":
            # For insert: delete the inserted element
            plan = TransformationPlan(
                transformation_type=TransformationType.DELETE,
                flow_name=flow_name,
                description=f"Rollback: {entry.get('description')}",
            )

            # Find the inserted element (operation='insert')
            for mapping_data in mappings_data:
                if mapping_data.get("operation") == "insert":
                    plan.add_mapping(
                        TransformationMapping(
                            element_type=mapping_data["element_type"],
                            element_id=mapping_data["element_id"],
                            old_sequence=mapping_data["new_sequence"],
                            new_sequence=None,
                            old_parent=mapping_data.get("new_parent"),
                            new_parent=None,
                            operation="delete",
                        )
                    )
                elif mapping_data.get("operation") == "renumber":
                    # Also reverse any cascade renumbering
                    plan.add_mapping(
                        TransformationMapping(
                            element_type=mapping_data["element_type"],
                            element_id=mapping_data["element_id"],
                            old_sequence=mapping_data["new_sequence"],
                            new_sequence=mapping_data["old_sequence"],
                            old_parent=mapping_data.get("new_parent"),
                            new_parent=mapping_data.get("old_parent"),
                            operation="renumber",
                        )
                    )

        elif trans_type == "delete":
            # For delete: re-insert the deleted element
            # This requires the element data from metadata
            plan = TransformationPlan(
                transformation_type=TransformationType.INSERT,
                flow_name=flow_name,
                description=f"Rollback: {entry.get('description')}",
            )

            # Get deleted element data from metadata
            deleted_element = metadata.get("deleted_element", {})

            for mapping_data in mappings_data:
                if mapping_data.get("operation") == "delete":
                    plan.add_mapping(
                        TransformationMapping(
                            element_type=mapping_data["element_type"],
                            element_id=mapping_data["element_id"],
                            old_sequence=None,
                            new_sequence=mapping_data["old_sequence"],
                            old_parent=None,
                            new_parent=mapping_data.get("old_parent"),
                            operation="insert",
                        )
                    )
                    plan.metadata["new_element"] = deleted_element
                elif mapping_data.get("operation") == "renumber":
                    # Reverse cascade renumbering
                    plan.add_mapping(
                        TransformationMapping(
                            element_type=mapping_data["element_type"],
                            element_id=mapping_data["element_id"],
                            old_sequence=mapping_data["new_sequence"],
                            new_sequence=mapping_data["old_sequence"],
                            old_parent=mapping_data.get("new_parent"),
                            new_parent=mapping_data.get("old_parent"),
                            operation="renumber",
                        )
                    )

        else:
            raise ValueError(
                f"Cannot create inverse for transformation type: {trans_type}"
            )

        return plan

    def rollback(
        self,
        steps: int = 1,
        save: bool = True,
        sync_directories: bool = False,
        project_base_path: Optional[Path] = None,
        update_code_paths: bool = False,
    ) -> Dict[str, Any]:
        """
        Rollback the last N transformations.

        This creates and applies inverse transformations for the last N
        transformations in history, effectively undoing them.

        Args:
            steps: Number of transformations to rollback
            save: Whether to save the rolled-back spec
            sync_directories: Whether to sync directories after rollback
            project_base_path: Base path for directory sync
            update_code_paths: Whether to update code paths after rollback

        Returns:
            The specification after rollback

        Raises:
            ValueError: If rollback is not possible
        """
        # Check if rollback is possible
        can_rollback, reason = self.can_rollback(steps)
        if not can_rollback:
            raise ValueError(f"Cannot rollback: {reason}")

        print(f"\n🔄 Rolling back last {steps} transformation(s)...")

        # Get transformations to rollback
        history = self.history_manager.get_history()
        to_rollback = history[:steps]  # Already in reverse order (most recent first)

        print(f"\n📜 Transformations to rollback:")
        for i, entry in enumerate(to_rollback, 1):
            print(f"  {i}. {entry['transformation_type']}: {entry['description']}")
            print(f"     Timestamp: {entry['timestamp']}")

        # Apply inverse transformations in reverse order
        current_spec = self.original_spec

        for i, entry in enumerate(to_rollback, 1):
            print(f"\n  ⏪ Rolling back transformation {i}/{steps}...")

            try:
                # Create inverse transformation
                inverse_plan = self._create_inverse_transformation(entry)

                # Apply the inverse (directly modify spec, skip validation for rollback)
                current_spec = self._apply_plan_to_virtual_spec(
                    inverse_plan, current_spec
                )

                print(f"     ✅ Rolled back: {entry['transformation_type']}")

            except Exception as e:
                print(f"     ❌ Error rolling back: {e}")
                raise ValueError(f"Rollback failed at step {i}: {e}")

        # Save the rolled-back spec (using YAMLSaver library)
        if save and self.spec_file:
            saver = YAMLSaver()
            options = SaveOptions(
                default_flow_style=False,
                sort_keys=False,
                indent=2,
                allow_unicode=True,
                create_backup=False,
            )
            result = saver.save(current_spec, self.spec_file, options)
            if result.success:
                print(f"\n✅ Rolled-back spec saved to {self.spec_file}")
            else:
                print(f"\n⚠️  Failed to save rolled-back spec: {result.errors}")

        # Sync directories if requested
        if sync_directories:
            if not project_base_path:
                if self.spec_file:
                    project_base_path = self.spec_file.parent.parent
                else:
                    raise ValueError(
                        "project_base_path required when sync_directories=True"
                    )

            print(f"\n🔄 Synchronizing directory structure after rollback...")
            # Note: Directory sync after rollback uses the inverse transformations
            # This will be handled by reapplying the transformations in the correct order
            print("  ⚠️  Manual directory sync may be needed after rollback")

        # Record rollback in history
        self.history_manager.record_rollback(
            steps=steps, spec_file=self.spec_file if save else None
        )

        print(f"\n📝 Rollback recorded in history")

        # Update state
        self.original_spec = current_spec

        # Remove rolled-back transformations from in-memory history
        if steps <= len(self.transformation_history):
            self.transformation_history = self.transformation_history[:-steps]

        print(f"\n✅ Rollback complete!")

        return current_spec


# =============================================================================
# SCAFFOLDING INTEGRATION
# =============================================================================


def scaffold_transformer(
    spec_file: Path,
    phase_data: Optional[Dict[str, Any]] = None,
    step_data: Optional[Dict[str, Any]] = None,
    project_base_path: Optional[str] = None,
    create_directories: bool = True,
    initialize_history: bool = True,
    save: bool = True,
) -> Dict[str, Any]:
    """
    Create a new phase or step from scratch using the transformation system.

    This is the zero-point creation function that integrates with the existing
    scaffolding system. It creates the YAML structure, optionally creates
    directories, and initializes transformation history.

    Args:
        spec_file: Path to the YAML spec file (will be created if doesn't exist)
        phase_data: Phase definition dict with keys:
            - phase_id: str
            - name: str
            - sequence: int
            - description: str (optional)
            - status: str (optional, default: 'not_started')
            - initial_steps: List[Dict] (optional)
        step_data: Step definition dict with keys:
            - step_id: str
            - name: str
            - sequence: int
            - description: str (optional)
            - action: str (optional)
            - phase_id: str (required if adding to existing phase)
        project_base_path: Base directory for project structure
        create_directories: Whether to create directory structure
        initialize_history: Whether to initialize transformation history
        save: Whether to save the created spec

    Returns:
        Dict with:
            - spec_file: Path to created spec
            - created: What was created ('phase', 'step', or 'both')
            - phase_dir: Path to phase directory (if created)
            - step_dir: Path to step directory (if created)
            - history_file: Path to history file (if initialized)
            - transformer: ControlFlowTransformation instance

    Example - Create new phase with initial steps:
        result = scaffold_transformer(
            spec_file=Path("specs/new_phase.yaml"),
            phase_data={
                'phase_id': 'validation',
                'name': 'Validation Phase',
                'sequence': 10,
                'description': 'Validate configuration',
                'initial_steps': [
                    {
                        'step_id': 'check_syntax',
                        'name': 'Check Syntax',
                        'sequence': 10,
                        'description': 'Validate YAML syntax',
                        'action': 'validate'
                    },
                    {
                        'step_id': 'verify_schema',
                        'name': 'Verify Schema',
                        'sequence': 20,
                        'description': 'Check against schema',
                        'action': 'verify'
                    }
                ]
            },
            create_directories=True,
            project_base_path="project"
        )

    Example - Add step to existing phase:
        result = scaffold_transformer(
            spec_file=Path("specs/existing_phase.yaml"),
            step_data={
                'step_id': 'new_step',
                'name': 'New Step',
                'sequence': 35,
                'description': 'New functionality',
                'action': 'process',
                'phase_id': 'validation'
            },
            create_directories=True,
            project_base_path="project"
        )
    """
    from .scaffolder import (
        ScaffoldGenerator,
        PhaseInsertion,
        StepInsertion,
        ImplementationStatus,
    )

    result = {
        "spec_file": spec_file,
        "created": None,
        "phase_dir": None,
        "step_dir": None,
        "history_file": None,
        "transformer": None,
    }

    # Validate inputs
    if not phase_data and not step_data:
        raise ValueError("Must provide either phase_data or step_data")

    if step_data and not spec_file.exists() and not phase_data:
        raise ValueError("Cannot add step to non-existent spec without phase_data")

    # Create or load spec
    spec_exists = spec_file.exists()

    if not spec_exists:
        # Create new spec with phase
        if not phase_data:
            raise ValueError("Must provide phase_data when creating new spec")

        initial_steps = phase_data.get("initial_steps", [])

        # Build phase spec
        phase_spec = {
            "phase": {
                "phase_id": phase_data["phase_id"],
                "name": phase_data["name"],
                "sequence": phase_data["sequence"],
                "description": phase_data.get("description", ""),
                "status": phase_data.get("status", "not_started"),
                "steps": [],
            }
        }

        # Add initial steps to spec
        for step in initial_steps:
            phase_spec["phase"]["steps"].append(
                {
                    "step_id": step["step_id"],
                    "name": step["name"],
                    "sequence": step["sequence"],
                    "description": step.get("description", ""),
                    "action": step.get("action", ""),
                }
            )

        # Save new spec (using YAMLSaver library)
        if save:
            spec_file.parent.mkdir(parents=True, exist_ok=True)
            saver = YAMLSaver()
            options = SaveOptions(
                default_flow_style=False, sort_keys=False, create_backup=False
            )
            result_save = saver.save(phase_spec, spec_file, options)
            if not result_save.success:
                print(f"⚠️  Failed to save phase spec: {result_save.errors}")

        result["created"] = "phase"

        # Create directories if requested
        if create_directories and project_base_path:
            scaffolder = ScaffoldGenerator(Path(project_base_path))

            # Map status string to enum
            status_str = phase_data.get("status", "not_started").upper()
            status_map = {
                "NOT_STARTED": ImplementationStatus.TODO,
                "TODO": ImplementationStatus.TODO,
                "PLANNED": ImplementationStatus.PLANNED,
                "IN_PROGRESS": ImplementationStatus.IN_PROGRESS,
                "IMPLEMENTED": ImplementationStatus.IMPLEMENTED,
            }
            status_enum = status_map.get(status_str, ImplementationStatus.TODO)

            # Create phase insertion object
            phase_insertion = PhaseInsertion(
                phase_id=phase_data["phase_id"],
                name=phase_data["name"],
                sequence=phase_data["sequence"],
                description=phase_data.get("description", ""),
                status=status_enum,
                create_scaffolding=True,
                base_path=Path("phases"),
            )

            # Create phase scaffolding
            base_path = Path(project_base_path) / "phases"
            phase_files = scaffolder.create_phase_scaffolding(
                phase_insertion, base_path, force=False
            )

            if phase_files:
                result["phase_dir"] = phase_files["directory"]

            # Create step scaffolding for initial steps
            if initial_steps and phase_files:
                phase_dir = phase_files["directory"]
                for step in initial_steps:
                    step_insertion = StepInsertion(
                        step_id=step["step_id"],
                        name=step["name"],
                        sequence=step["sequence"],
                        description=step.get("description", ""),
                        status=ImplementationStatus.TODO,
                        step_type=step.get("step_type", "processing"),
                        phase_id=phase_data["phase_id"],
                        phase_sequence=phase_data["sequence"],
                    )

                    step_files = scaffolder.create_step_scaffolding(
                        step_insertion, phase_dir, force=False
                    )

                    if step_files and not result["step_dir"]:
                        result["step_dir"] = step_files["directory"]

    else:
        # Spec exists - add step using transformation system
        if step_data:
            transformer = ControlFlowTransformation(str(spec_file))

            # Create step element
            new_step = {
                "step_id": step_data["step_id"],
                "name": step_data["name"],
                "sequence": step_data["sequence"],
                "description": step_data.get("description", ""),
                "action": step_data.get("action", ""),
            }

            # Plan insert
            plan = transformer.plan_insert(
                element=new_step,
                target_type="step",
                cascade_renumber=step_data.get("cascade_renumber", False),
            )

            # Validate
            validation = transformer.validate(plan)
            if not validation.valid:
                raise ValueError(f"Invalid step insertion: {validation.errors}")

            # Apply transformation
            transformer.apply(
                plan,
                save=save,
                sync_directories=create_directories,
                project_base_path=project_base_path,
            )

            result["created"] = "step"
            result["transformer"] = transformer

            # Create step directory if requested
            if create_directories and project_base_path:
                scaffolder = ScaffoldGenerator(Path(project_base_path))

                # Determine phase directory
                phase_id = (
                    step_data.get("phase_id")
                    or transformer.original_spec["phase"]["phase_id"]
                )
                phase_seq = transformer.original_spec["phase"]["sequence"]
                phase_dir = (
                    Path(project_base_path) / "phases" / f"phase_{phase_seq}_{phase_id}"
                )

                step_insertion = StepInsertion(
                    step_id=step_data["step_id"],
                    name=step_data["name"],
                    sequence=step_data["sequence"],
                    description=step_data.get("description", ""),
                    status=ImplementationStatus.TODO,
                    step_type=step_data.get("step_type", "processing"),
                    phase_id=phase_id,
                    phase_sequence=phase_seq,
                )

                step_files = scaffolder.create_step_scaffolding(
                    step_insertion, phase_dir, force=False
                )

                if step_files:
                    result["step_dir"] = step_files["directory"]

    # Initialize history if requested
    if initialize_history and not spec_exists:
        transformer = ControlFlowTransformation(str(spec_file))
        # History file is automatically created during ControlFlowTransformation init
        result["history_file"] = transformer.history_manager.history_file
        result["transformer"] = transformer

    return result


if __name__ == "__main__":
    demo()
