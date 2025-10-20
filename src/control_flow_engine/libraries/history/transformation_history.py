"""
Transformation History Library

Manages persistent history of transformations for undo/rollback support.
This is a universal library that can track changes to any YAML-based system.

Key Features:
- Persistent history storage in JSON format
- Checksum-based change detection
- Rollback capability
- Transformation audit trail
- Import tracking for affected files

This library is universal and has no domain-specific dependencies.
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class TransformationMapping:
    """
    Records how an element changed during a transformation.
    Universal structure that works for any hierarchical YAML system.
    """

    element_type: str  # e.g., 'phase', 'step', 'field', 'section'
    element_id: str  # Unique identifier
    old_sequence: Optional[int] = None
    new_sequence: Optional[int] = None
    old_parent: Optional[str] = None
    new_parent: Optional[str] = None
    operation: str = ""  # 'insert', 'delete', 'move', 'renumber', 'update'
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Result of transformation validation."""

    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def add_error(self, error: str):
        """Add an error message."""
        self.errors.append(error)
        self.valid = False

    def add_warning(self, warning: str):
        """Add a warning message."""
        self.warnings.append(warning)


class TransformationHistory:
    """
    Manages persistent history of transformations for undo/rollback support.

    Stores transformation history in JSON format with:
    - Timestamp of each transformation
    - Complete transformation mappings
    - Checksums of affected files (YAML, directories)
    - Enough data to reverse the transformation

    History file format:
    {
        "version": "1.0",
        "created_at": "2025-10-16T00:00:00",
        "transformations": [
            {
                "timestamp": "2025-10-16T10:30:00",
                "transformation_type": "renumber",
                "context_name": "main_config_flow",
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
            history_file: Path to history JSON file (e.g., .transformation_history.json)
        """
        self.history_file = history_file
        self.history: Dict[str, Any] = self._load_history()

    def _load_history(self) -> Dict[str, Any]:
        """Load existing history or create new structure."""
        if self.history_file.exists():
            try:
                with open(self.history_file) as f:
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
        """
        Calculate SHA-256 checksum of a file for change detection.

        Args:
            file_path: Path to file to checksum

        Returns:
            Hex digest of SHA-256 hash, or error string
        """
        if not file_path.exists():
            return "FILE_NOT_FOUND"

        try:
            with open(file_path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            return f"ERROR:{str(e)}"

    def record_transformation(
        self,
        transformation_type: str,
        context_name: str,
        description: str,
        mappings: List[TransformationMapping],
        validation_result: Optional[ValidationResult] = None,
        metadata: Optional[Dict[str, Any]] = None,
        spec_file: Optional[Path] = None,
        affected_directories: Optional[List[Path]] = None,
        affected_files: Optional[List[Path]] = None,
    ) -> Dict[str, Any]:
        """
        Record a transformation in the history.

        Args:
            transformation_type: Type of transformation (e.g., 'move', 'insert', 'delete')
            context_name: Name of the context (e.g., flow name, form name)
            description: Human-readable description
            mappings: List of transformation mappings
            validation_result: Optional validation result
            metadata: Optional additional metadata
            spec_file: Path to the main spec file (for checksums)
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
        for mapping in mappings:
            mappings_data.append(
                {
                    "element_type": mapping.element_type,
                    "element_id": mapping.element_id,
                    "old_sequence": mapping.old_sequence,
                    "new_sequence": mapping.new_sequence,
                    "old_parent": mapping.old_parent,
                    "new_parent": mapping.new_parent,
                    "operation": mapping.operation,
                    "metadata": mapping.metadata,
                }
            )

        # Create history entry
        entry = {
            "timestamp": datetime.now().isoformat(),
            "transformation_type": transformation_type,
            "context_name": context_name,
            "description": description,
            "mappings": mappings_data,
            "metadata": metadata or {},
            "files_modified": files_modified,
            "checksums_after": checksums_after,
            "validation_valid": validation_result.valid if validation_result else None,
            "validation_errors": validation_result.errors if validation_result else [],
            "validation_warnings": (
                validation_result.warnings if validation_result else []
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
        transformations_copy = list(reversed(transformations))

        if limit:
            return transformations_copy[:limit]
        return transformations_copy

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
        output_file.parent.mkdir(parents=True, exist_ok=True)
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
                context = entry.get("context_name", "Unknown")
                desc = entry.get("description", "No description")

                lines.append(f"{len(transformations) - i}. [{timestamp}]")
                lines.append(f"   Type: {trans_type}")
                lines.append(f"   Context: {context}")
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
        self,
        steps: int,
        context_name: str = "multiple",
        spec_file: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Record a rollback operation in history.

        Args:
            steps: Number of transformations that were rolled back
            context_name: Name of context (defaults to 'multiple' if rolling back multiple)
            spec_file: Path to the spec file (for checksums)

        Returns:
            The rollback history entry
        """
        # Get the transformations that were rolled back
        transformations = self.history.get("transformations", [])
        rolled_back = transformations[-steps:] if steps <= len(transformations) else []

        # Determine context name
        if steps == 1 and rolled_back:
            context_name = rolled_back[0].get("context_name", "unknown")

        # Create rollback entry
        entry = {
            "timestamp": datetime.now().isoformat(),
            "transformation_type": "rollback",
            "context_name": context_name,
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
