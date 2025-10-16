"""
History Library - Transformation History and Rollback Support

This library provides persistent history tracking for any YAML transformation system.

Components:
- TransformationHistory: Manages transformation history with checksums and rollback
- TransformationMapping: Records how elements changed
- ValidationResult: Validation results for transformations

Features:
- Persistent JSON-based history storage
- SHA-256 checksums for change detection
- Rollback capability
- Transformation audit trail
- Universal - works with any hierarchical YAML system

Example Usage:
    ```python
    from pathlib import Path
    from control_flow_engine.libraries.history import TransformationHistory, TransformationMapping
    
    # Initialize history
    history = TransformationHistory(Path('.transformation_history.json'))
    
    # Record a transformation
    mapping = TransformationMapping(
        element_type='phase',
        element_id='discovery',
        old_sequence=1,
        new_sequence=2,
        operation='move'
    )
    
    history.record_transformation(
        transformation_type='move',
        context_name='main_flow',
        description='Move discovery phase to position 2',
        mappings=[mapping],
        spec_file=Path('spec.yml')
    )
    
    # View history
    print(history.summary())
    
    # Check if can rollback
    can_rollback, reason = history.can_rollback(steps=1)
    ```
"""

from .transformation_history import (
    TransformationHistory,
    TransformationMapping,
    ValidationResult
)

__all__ = [
    'TransformationHistory',
    'TransformationMapping',
    'ValidationResult'
]
