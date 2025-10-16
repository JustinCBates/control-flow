"""
Path Resolution Library - Context-Aware Path Resolution

This library provides centralized path resolution for artifacts across
hierarchical workflows, ensuring consistent behavior regardless of execution context.

Components:
- PathResolver: Main path resolution service
- PathResolutionError: Exception for resolution failures

Features:
- Auto-detect project root from execution context
- Resolve artifact paths from YAML specifications
- Phase/step output directory resolution
- Artifact validation and accessibility checking
- Caching for performance
- Universal - works with any YAML-based workflow system

Example Usage:
    ```python
    from control_flow_engine.libraries.path_resolution import PathResolver
    
    # Auto-detect from current file
    resolver = PathResolver.from_execution_context(__file__)
    
    # Resolve artifact by ID
    config_path = resolver.resolve_artifact_path('user_configuration')
    
    # Resolve phase output directory
    output_dir = resolver.resolve_phase_output_dir('collection', create=True)
    
    # Get project root
    root = resolver.get_project_root()
    
    # List all artifacts
    artifacts = resolver.list_artifacts()
    
    # Validate artifact accessibility
    can_read = resolver.validate_artifact_accessible('config', mode='read')
    ```

Key Methods:
- from_execution_context(__file__): Auto-detect project root
- resolve_artifact_path(artifact_id): Get absolute path to artifact
- resolve_phase_output_dir(phase_id): Get phase output directory
- resolve_phase_directory(phase_id): Get phase directory
- get_artifact_info(artifact_id): Get artifact metadata
- list_artifacts(): List all known artifacts
- list_phases(): List all known phases
"""

from .path_resolver import PathResolver, PathResolutionError

__all__ = ['PathResolver', 'PathResolutionError']
