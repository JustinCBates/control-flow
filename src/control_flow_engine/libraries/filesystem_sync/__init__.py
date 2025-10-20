"""
Filesystem Sync Library - Directory Synchronization

This library synchronizes filesystem directory structures with YAML transformations.

Components:
- DirectorySynchronizer: Plans and executes directory operations
- DirectoryOperation: Represents a filesystem operation

Features:
- Rename directories when sequences change
- Move directories when structure changes
- Delete directories when elements removed
- Create directories for new elements
- Configurable naming patterns
- Dry-run mode for preview
- Operation rollback support

Universal library - works with any hierarchical YAML system.

Example Usage:
    ```python
    from pathlib import Path
    from control_flow_engine.libraries.filesystem_sync import DirectorySynchronizer
    from control_flow_engine.libraries.history import TransformationMapping

    # Initialize synchronizer
    sync = DirectorySynchronizer(
        base_path=Path('/project/phases'),
        dry_run=False,
        naming_pattern='phase_{sequence}_{name}'
    )

    # Create mapping for a move operation
    mapping = TransformationMapping(
        element_type='phase',
        element_id='discovery',
        old_sequence=1,
        new_sequence=2,
        operation='move'
    )

    # Plan operations
    operations = sync.plan_operations_from_mappings([mapping], structure_data={})

    # Preview
    print(sync.preview_operations())

    # Execute
    results = sync.execute_operations()
    ```
"""

from .directory_synchronizer import DirectorySynchronizer, DirectoryOperation

__all__ = ["DirectorySynchronizer", "DirectoryOperation"]
