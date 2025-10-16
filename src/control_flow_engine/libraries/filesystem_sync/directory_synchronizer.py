"""
Filesystem Synchronization Library

Synchronizes directory structure with YAML transformations.
After a transformation is applied to YAML, this library updates the physical
directory structure to match.

Key Features:
- Rename directories when sequences change
- Move directories when elements are reorganized
- Delete directories when elements are removed
- Create directories for new elements
- Update Python imports to match new paths
- Dry-run mode for preview
- Operation planning and execution

This is a universal library that works with any hierarchical YAML system
that maps to a directory structure.
"""

import re
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class DirectoryOperation:
    """
    Represents a filesystem operation needed to sync directories.
    
    Attributes:
        operation: Type of operation ('move', 'delete', 'create', 'update_imports')
        source: Source path for move/delete operations
        destination: Destination path for move/create operations
        element_id: Identifier of the element being operated on
        element_type: Type of element (e.g., 'phase', 'step', 'section', 'field')
        metadata: Additional metadata about the operation
    """
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


class DirectorySynchronizer:
    """
    Synchronizes directory structure with YAML transformations.
    
    After a transformation is applied to the YAML, this class uses the
    transformation mappings to update the physical directory structure:
    - Rename directories when sequences change
    - Move directories when elements are reorganized
    - Delete directories when elements are removed
    - Create directories for new elements
    - Update Python imports to match new paths
    
    This is a universal library - configure it with your own naming pattern.
    """
    
    def __init__(
        self,
        base_path: Path,
        dry_run: bool = False,
        naming_pattern: Optional[str] = None
    ):
        """
        Initialize directory synchronizer.
        
        Args:
            base_path: Base directory containing the project
            dry_run: If True, plan operations but don't execute
            naming_pattern: Pattern for directory names (default: "{element}_{sequence}_{name}")
                Examples:
                - "phase_{sequence}_{name}" - for control-flow phases
                - "step_{sequence}_{name}" - for control-flow steps
                - "section_{sequence}_{name}" - for form sections
                - "{sequence}_{name}" - simple numbered pattern
        """
        self.base_path = base_path
        self.dry_run = dry_run
        self.naming_pattern = naming_pattern or "{element}_{sequence}_{name}"
        self.operations: List[DirectoryOperation] = []
    
    def plan_operations_from_mappings(
        self,
        mappings: List,  # List of TransformationMapping
        structure_data: Dict[str, Any],
        parent_path: Optional[Path] = None
    ) -> List[DirectoryOperation]:
        """
        Create a plan of directory operations from transformation mappings.
        
        Args:
            mappings: List of transformation mappings
            structure_data: The NEW structure data after transformation
            parent_path: Parent directory path (for nested structures)
            
        Returns:
            List of directory operations to execute
        """
        operations = []
        
        for mapping in mappings:
            ops = self._plan_mapping_operations(mapping, structure_data, parent_path)
            operations.extend(ops)
        
        self.operations = operations
        return operations
    
    def _plan_mapping_operations(
        self,
        mapping: Any,  # TransformationMapping
        structure_data: Dict[str, Any],
        parent_path: Optional[Path] = None
    ) -> List[DirectoryOperation]:
        """Plan directory operations for a single mapping."""
        operations = []
        element_type = mapping.element_type
        element_id = mapping.element_id
        operation = mapping.operation
        
        if operation == 'delete':
            # Delete directory
            old_dir = self._get_directory_path(
                element_type,
                mapping.old_sequence,
                element_id,
                parent_path
            )
            if old_dir and old_dir.exists():
                operations.append(DirectoryOperation(
                    operation='delete',
                    source=old_dir,
                    element_id=element_id,
                    element_type=element_type
                ))
        
        elif operation == 'renumber' or operation == 'move':
            # Rename/move directory
            old_dir = self._get_directory_path(
                element_type,
                mapping.old_sequence,
                element_id,
                parent_path
            )
            new_dir = self._get_directory_path(
                element_type,
                mapping.new_sequence,
                element_id,
                parent_path
            )
            
            if old_dir and old_dir.exists() and old_dir != new_dir:
                operations.append(DirectoryOperation(
                    operation='move',
                    source=old_dir,
                    destination=new_dir,
                    element_id=element_id,
                    element_type=element_type,
                    metadata={
                        'old_sequence': mapping.old_sequence,
                        'new_sequence': mapping.new_sequence
                    }
                ))
        
        elif operation == 'insert':
            # Create new directory
            new_dir = self._get_directory_path(
                element_type,
                mapping.new_sequence,
                element_id,
                parent_path
            )
            if new_dir:
                operations.append(DirectoryOperation(
                    operation='create',
                    destination=new_dir,
                    element_id=element_id,
                    element_type=element_type,
                    metadata={'element_data': structure_data}
                ))
        
        return operations
    
    def _get_directory_path(
        self,
        element_type: str,
        sequence: int,
        element_name: str,
        parent_path: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Get the directory path for an element based on naming pattern.
        
        Args:
            element_type: Type of element (e.g., 'phase', 'step')
            sequence: Sequence number
            element_name: Name of the element
            parent_path: Parent directory path (for nested structures)
            
        Returns:
            Full path to the directory
        """
        # Convert element name to directory-safe format
        dir_name_part = element_name.lower().replace(' ', '_').replace('-', '_')
        # Clean up any special characters
        dir_name_part = re.sub(r'[^a-z0-9_]', '', dir_name_part)
        
        # Apply naming pattern
        dir_name = self.naming_pattern.format(
            element=element_type,
            sequence=sequence,
            name=dir_name_part
        )
        
        # Determine base path
        if parent_path:
            return parent_path / dir_name
        else:
            return self.base_path / dir_name
    
    def execute_operations(
        self,
        operations: Optional[List[DirectoryOperation]] = None
    ) -> Dict[str, Any]:
        """
        Execute the planned directory operations.
        
        Args:
            operations: List of operations to execute (uses self.operations if None)
            
        Returns:
            Dict with execution results:
                {
                    'operations_planned': int,
                    'operations_executed': int,
                    'operations_failed': int,
                    'errors': List[str],
                    'dry_run': bool
                }
        """
        if operations is None:
            operations = self.operations
        
        results = {
            'operations_planned': len(operations),
            'operations_executed': 0,
            'operations_failed': 0,
            'errors': [],
            'dry_run': self.dry_run
        }
        
        for op in operations:
            try:
                if self.dry_run:
                    print(f"  [DRY RUN] {op}")
                    results['operations_executed'] += 1
                else:
                    self._execute_operation(op)
                    print(f"  ✓ {op}")
                    results['operations_executed'] += 1
            except Exception as e:
                error_msg = f"Failed to execute {op}: {e}"
                results['errors'].append(error_msg)
                results['operations_failed'] += 1
                print(f"  ✗ {error_msg}")
        
        return results
    
    def _execute_operation(self, op: DirectoryOperation):
        """Execute a single directory operation."""
        if op.operation == 'move':
            if op.source and op.destination:
                # Ensure parent directory exists
                op.destination.parent.mkdir(parents=True, exist_ok=True)
                # Move/rename directory
                shutil.move(str(op.source), str(op.destination))
        
        elif op.operation == 'delete':
            if op.source and op.source.exists():
                if op.source.is_dir():
                    shutil.rmtree(op.source)
                else:
                    op.source.unlink()
        
        elif op.operation == 'create':
            if op.destination:
                op.destination.mkdir(parents=True, exist_ok=True)
                # Create basic __init__.py if it's a Python package
                init_file = op.destination / "__init__.py"
                if not init_file.exists():
                    init_file.write_text('"""Auto-generated by transformation system."""\n')
    
    def preview_operations(
        self,
        operations: Optional[List[DirectoryOperation]] = None
    ) -> str:
        """
        Generate a preview of directory operations.
        
        Args:
            operations: Operations to preview (uses self.operations if None)
            
        Returns:
            Formatted string showing planned operations
        """
        if operations is None:
            operations = self.operations
        
        lines = [
            "=" * 60,
            "DIRECTORY SYNCHRONIZATION PREVIEW",
            "=" * 60,
            f"Base Path: {self.base_path}",
            f"Operations: {len(operations)}",
            f"Dry Run: {self.dry_run}",
            "",
            "=" * 60,
            "OPERATIONS",
            "=" * 60,
            ""
        ]
        
        for i, op in enumerate(operations, 1):
            lines.append(f"{i}. {op}")
        
        if not operations:
            lines.append("  No operations planned")
        
        lines.append("")
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def rollback_operation(self, op: DirectoryOperation) -> bool:
        """
        Attempt to rollback a single operation.
        
        Args:
            op: The operation to rollback
            
        Returns:
            True if rollback succeeded, False otherwise
        """
        try:
            if op.operation == 'move':
                # Move back
                if op.destination and op.source and op.destination.exists():
                    shutil.move(str(op.destination), str(op.source))
                    return True
            
            elif op.operation == 'create':
                # Delete what was created
                if op.destination and op.destination.exists():
                    if op.destination.is_dir():
                        shutil.rmtree(op.destination)
                    else:
                        op.destination.unlink()
                    return True
            
            elif op.operation == 'delete':
                # Can't restore deleted files without backup
                return False
            
            return False
        except Exception as e:
            print(f"Rollback failed for {op}: {e}")
            return False
