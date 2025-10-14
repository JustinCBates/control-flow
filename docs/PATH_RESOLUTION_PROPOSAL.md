# Path Resolution System - Proposal

**Date:** October 14, 2025  
**Status:** PROPOSAL  
**Context:** Addresses inconsistent path resolution across phases, steps, and orchestrators when handling insertions, moves, and deletions of control flow components.

---

## Problem Statement

The current control flow system has **inconsistent path resolution** behavior:

1. **Step files** when run standalone calculate output as: `step_dir.parent.parent / "outputs"` → `phases/outputs/`
2. **Orchestrator files** when calling steps pass: `phase_dir / "outputs"` → `phases/phase_X_Y/outputs/`
3. **control_flows.yml** specifies paths as: `phases/phase_X_Y/outputs/file.yml`

This creates a **pathing mismatch** where:
- Step standalone → produces outputs in `phases/outputs/` ❌
- Orchestrator calling step → expects outputs in `phases/phase_X_Y/outputs/` ✅
- Result: Standalone testing produces files in wrong location

### Root Cause

**Hardcoded relative path calculations** scattered across generated code:
```python
# In step standalone main():
output_dir = step_dir.parent.parent / "outputs"  # Goes to phases/outputs/

# In orchestrator execute_step() call:
output_dir = phase_dir / "outputs"  # Goes to phases/phase_X_Y/outputs/
```

When control flow structure changes (phase moved, step relocated, flow reorganized), **all path calculations break**.

---

## Design Principles

### 1. **Single Source of Truth**
All paths must be resolvable from `control_flows.yml` specification - no hardcoded relative paths.

### 2. **Context-Aware Resolution**
Path resolution must work correctly in three execution contexts:
- **Pipeline execution**: Main orchestrator → phase orchestrator → step
- **Phase standalone**: Phase orchestrator → step
- **Step standalone**: Step running directly

### 3. **Graceful Degradation**
If path resolution fails, provide clear error with resolution hints rather than writing to wrong location.

### 4. **Refactoring-Safe**
Moving/renaming phases or steps should require only `control_flows.yml` updates, not code changes.

---

## Proposed Solution: Path Resolution Service

### Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    PathResolver Service                       │
│                                                               │
│  Responsibilities:                                            │
│  • Load control_flows.yml specification                       │
│  • Resolve artifact paths by artifact_id                      │
│  • Calculate project_root from execution context              │
│  • Validate resolved paths exist (read) or can be created     │
│  • Provide path hints for debugging                           │
└──────────────────────────────────────────────────────────────┘
         ▲                    ▲                    ▲
         │                    │                    │
    ┌────┴────┐          ┌────┴────┐         ┌────┴────┐
    │  Main   │          │  Phase  │         │  Step   │
    │Orchestr.│          │Orchestr.│         │  File   │
    └─────────┘          └─────────┘         └─────────┘
```

### Core Components

#### 1. PathResolver Class

```python
# control-flow/src/control_flow_engine/runtime/path_resolver.py

from pathlib import Path
from typing import Dict, Any, Optional, Union
import yaml

class PathResolutionError(Exception):
    """Raised when path cannot be resolved."""
    pass

class PathResolver:
    """
    Centralized path resolution service for control flow execution.
    
    Resolves artifact paths from control_flows.yml specification regardless
    of execution context (pipeline, phase standalone, step standalone).
    
    Usage:
        resolver = PathResolver.from_execution_context(__file__)
        output_path = resolver.resolve_artifact_path(
            phase_id='collection',
            artifact_id='user_configuration'
        )
    """
    
    def __init__(self, project_root: Path, control_flows_spec: Dict[str, Any]):
        """
        Initialize path resolver.
        
        Args:
            project_root: Absolute path to project root (contains phases/)
            control_flows_spec: Parsed control_flows.yml dictionary
        """
        self.project_root = Path(project_root).resolve()
        self.spec = control_flows_spec
        self._artifact_cache = {}
        self._build_artifact_index()
    
    @classmethod
    def from_execution_context(cls, executing_file: Union[str, Path]) -> 'PathResolver':
        """
        Create PathResolver by detecting project root from executing file.
        
        Searches upward from executing file for control_flows.yml or phases/ directory.
        
        Args:
            executing_file: __file__ from the calling script
            
        Returns:
            PathResolver instance
            
        Raises:
            PathResolutionError: If project root cannot be detected
        """
        current = Path(executing_file).resolve().parent
        
        # Search upward for project root markers
        max_depth = 10
        for _ in range(max_depth):
            # Check for control_flows.yml
            if (current / "design_specs" / "control_flows.yml").exists():
                spec_file = current / "design_specs" / "control_flows.yml"
                with open(spec_file) as f:
                    spec = yaml.safe_load(f)
                return cls(project_root=current, control_flows_spec=spec)
            
            # Check for phases directory (fallback)
            if (current / "phases").is_dir():
                # Try to find control_flows.yml nearby
                for candidate in [current, current.parent]:
                    spec_file = candidate / "design_specs" / "control_flows.yml"
                    if spec_file.exists():
                        with open(spec_file) as f:
                            spec = yaml.safe_load(f)
                        return cls(project_root=current, control_flows_spec=spec)
            
            # Move up one level
            if current.parent == current:
                break
            current = current.parent
        
        raise PathResolutionError(
            f"Could not detect project root from {executing_file}.\n"
            f"Project root should contain 'design_specs/control_flows.yml' or 'phases/' directory."
        )
    
    def _build_artifact_index(self):
        """Build index of artifacts from control_flows.yml for fast lookup."""
        self._artifact_cache = {}
        
        for flow in self.spec.get('control_flows', []):
            for phase in flow.get('phases', []):
                phase_id = phase.get('phase_id')
                
                # Index artifacts produced by phase
                for side_effect in phase.get('implementation', {}).get('side_effects', []):
                    if side_effect.get('action') == 'writes':
                        artifact_id = side_effect.get('artifact')
                        location = side_effect.get('location')
                        
                        if artifact_id and location:
                            self._artifact_cache[artifact_id] = {
                                'phase_id': phase_id,
                                'location': location,
                                'action': 'writes'
                            }
                
                # Also index consumed artifacts for validation
                for side_effect in phase.get('implementation', {}).get('side_effects', []):
                    if side_effect.get('action') == 'reads':
                        artifact_id = side_effect.get('artifact')
                        location = side_effect.get('location')
                        
                        if artifact_id and location:
                            # Don't overwrite if already exists from writes
                            if artifact_id not in self._artifact_cache:
                                self._artifact_cache[artifact_id] = {
                                    'phase_id': phase_id,
                                    'location': location,
                                    'action': 'reads'
                                }
    
    def resolve_artifact_path(
        self, 
        artifact_id: str,
        phase_id: Optional[str] = None,
        ensure_exists: bool = False,
        create_parent: bool = False
    ) -> Path:
        """
        Resolve artifact path from artifact ID.
        
        Args:
            artifact_id: Artifact identifier from control_flows.yml
            phase_id: Optional phase context for disambiguation
            ensure_exists: If True, raise error if path doesn't exist
            create_parent: If True, create parent directories
            
        Returns:
            Absolute Path to artifact
            
        Raises:
            PathResolutionError: If artifact cannot be resolved
        """
        # Look up artifact in index
        if artifact_id not in self._artifact_cache:
            raise PathResolutionError(
                f"Artifact '{artifact_id}' not found in control_flows.yml.\n"
                f"Available artifacts: {list(self._artifact_cache.keys())}"
            )
        
        artifact_info = self._artifact_cache[artifact_id]
        relative_path = artifact_info['location']
        
        # Resolve to absolute path
        absolute_path = (self.project_root / relative_path).resolve()
        
        # Validate or create
        if ensure_exists and not absolute_path.exists():
            raise PathResolutionError(
                f"Artifact '{artifact_id}' path does not exist: {absolute_path}\n"
                f"Expected by phase '{artifact_info['phase_id']}'"
            )
        
        if create_parent:
            absolute_path.parent.mkdir(parents=True, exist_ok=True)
        
        return absolute_path
    
    def resolve_phase_output_dir(self, phase_id: str, create: bool = False) -> Path:
        """
        Resolve output directory for a phase.
        
        Args:
            phase_id: Phase identifier (e.g., 'discovery', 'collection')
            create: If True, create directory if it doesn't exist
            
        Returns:
            Absolute Path to phase output directory
        """
        # Find phase in spec
        for flow in self.spec.get('control_flows', []):
            for phase in flow.get('phases', []):
                if phase.get('phase_id') == phase_id:
                    phase_dir = phase.get('implementation', {}).get('phase_directory')
                    if phase_dir:
                        output_dir = self.project_root / phase_dir / "outputs"
                        if create:
                            output_dir.mkdir(parents=True, exist_ok=True)
                        return output_dir
        
        raise PathResolutionError(
            f"Phase '{phase_id}' not found in control_flows.yml"
        )
    
    def get_project_root(self) -> Path:
        """Get absolute path to project root."""
        return self.project_root
    
    def validate_artifact_accessible(self, artifact_id: str, mode: str = 'read') -> bool:
        """
        Validate artifact is accessible for read or write.
        
        Args:
            artifact_id: Artifact identifier
            mode: 'read' or 'write'
            
        Returns:
            True if accessible, False otherwise
        """
        try:
            path = self.resolve_artifact_path(artifact_id, ensure_exists=(mode == 'read'))
            
            if mode == 'read':
                return path.exists() and path.is_file()
            elif mode == 'write':
                # Check if parent directory exists or can be created
                return path.parent.exists() or path.parent.parent.exists()
            
        except PathResolutionError:
            return False
        
        return False
```

#### 2. Integration with Generated Code

Update generator templates to inject PathResolver usage:

```python
# In generator.py - Phase orchestrator template

def _generate_phase_content(self, phase: PhaseInfo) -> str:
    """Generate phase orchestrator content with PathResolver integration."""
    
    return f'''"""
Phase: {phase.name}
{phase.description}

Generated by Control Flow Engine
"""

from pathlib import Path
from typing import Dict, Any
import logging
import sys

# Conditional imports to handle both module context and standalone execution
if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from phases.{phase.module_name}.{phase.steps[0].module_name} import {phase.steps[0].function_name}
    from control_flow_engine.runtime.path_resolver import PathResolver
else:
    from .{phase.steps[0].module_name} import {phase.steps[0].function_name}
    from control_flow_engine.runtime.path_resolver import PathResolver

logger = logging.getLogger(__name__)


class {phase.class_name}:
    """
    {phase.name}
    Status: {phase.status}
    
    {phase.description}
    
    Artifacts Consumed: {', '.join(phase.artifacts_consumed)}
    Artifacts Produced: {', '.join(phase.artifacts_produced)}
    """
    
    def __init__(self, project_root: Path, ui=None):
        self.project_root = project_root
        self.ui = ui
        self.phase_dir = project_root / "{phase.directory}"
        
        # Initialize path resolver
        self.path_resolver = PathResolver.from_execution_context(__file__)
        
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute {phase.name}.
        
        Args:
            context: Execution context with consumed artifacts
            
        Returns:
            Dict with produced artifacts as absolute paths
        """
        if self.ui:
            self.ui.show_phase_header("{phase.name}", "{phase.description}")
        
        logger.info("Executing {phase.name}")
        
        # Resolve input artifact paths
        resolved_context = {{}}
        for artifact_id in {phase.artifacts_consumed}:
            try:
                artifact_path = self.path_resolver.resolve_artifact_path(
                    artifact_id, 
                    ensure_exists=True
                )
                resolved_context[f'{{artifact_id}}_file'] = str(artifact_path)
            except Exception as e:
                logger.warning(f"Could not resolve artifact {{artifact_id}}: {{e}}")
        
        # Merge with original context
        resolved_context.update(context)
        
        # Execute step
        try:
            step_result = {phase.steps[0].function_name}(
                resolved_context, 
                self.phase_dir
            )
            
            logger.info(f"{phase.name} completed: {{step_result['status']}}")
            
            # Resolve output artifact paths
            result = {{}}
            for artifact_id in {phase.artifacts_produced}:
                try:
                    artifact_path = self.path_resolver.resolve_artifact_path(
                        artifact_id,
                        create_parent=True
                    )
                    result[f'{{artifact_id}}_file'] = str(artifact_path)
                except Exception as e:
                    logger.error(f"Could not resolve output artifact {{artifact_id}}: {{e}}")
            
            logger.info("{phase.name} completed")
            return result
            
        except Exception as e:
            logger.error(f"{phase.name} failed: {{e}}")
            raise
'''
```

#### 3. Step File Template Update

```python
# In generator.py - Step file template

def _generate_step_content(self, step: StepInfo, phase: PhaseInfo) -> str:
    """Generate step file content with PathResolver integration."""
    
    return f'''"""
Step: {step.name}
{step.description}
"""

from pathlib import Path
from typing import Dict, Any
import logging
import sys

# Conditional imports
if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from control_flow_engine.runtime.path_resolver import PathResolver

logger = logging.getLogger(__name__)


def {step.function_name}(context: Dict[str, Any], phase_dir: Path) -> Dict[str, Any]:
    """
    {step.name}
    Status: {step.status}
    
    {step.description}
    
    Args:
        context: Execution context with input artifacts
        phase_dir: Phase directory path
        
    Returns:
        Dict with step results
    """
    logger.info("Executing step: {step.name}")
    
    # Step implementation here
    
    result = {{
        'step': '{step.step_id}',
        'status': 'completed'
    }}
    
    logger.info("Step {step.name} completed successfully")
    return result


def main():
    """Main entry point for standalone testing."""
    import argparse
    from control_flow_engine.runtime.path_resolver import PathResolver
    
    parser = argparse.ArgumentParser(description="{step.name}")
    parser.add_argument('--input', help='Input file path')
    parser.add_argument('--output', help='Output file path')
    
    args = parser.parse_args()
    
    try:
        # Initialize path resolver from current file
        resolver = PathResolver.from_execution_context(__file__)
        
        # Use resolver for all path operations
        if args.output:
            output_path = Path(args.output)
        else:
            # Resolve from phase context
            output_path = resolver.resolve_phase_output_dir('{phase.phase_id}', create=True)
        
        # Build context
        context = {{}}
        
        # Execute step
        result = {step.function_name}(context, resolver.project_root / "{phase.directory}")
        
        print(f"✅ Step completed: {{result}}")
        return 0
        
    except Exception as e:
        print(f"❌ Step failed: {{e}}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
'''
```

---

## Migration Strategy

### Phase 1: Add PathResolver Service (No Breaking Changes)
1. Create `control-flow/src/control_flow_engine/runtime/path_resolver.py`
2. Add comprehensive tests
3. Document API usage

### Phase 2: Update Generator Templates
1. Modify `_generate_phase_content()` to inject PathResolver
2. Modify `_generate_step_content()` to inject PathResolver
3. Test generated code with existing phases

### Phase 3: Regenerate Existing Phases
1. Backup current phase implementations
2. Regenerate all phases with new templates
3. Run full pipeline test suite
4. Validate outputs match expected paths

### Phase 4: Add Validation Tools
1. Create `validate_paths.py` tool to check all artifact paths
2. Add pre-commit hook to validate path changes
3. Update CI/CD to run path validation

---

## Benefits

### 1. **Refactoring Safety**
Move or rename phases/steps by only updating `control_flows.yml`:
```yaml
# Before
phase_directory: "phases/phase_3_collection/"

# After (moved to subdir)
phase_directory: "phases/data_collection/phase_3_collection/"
```
All code automatically resolves new paths via PathResolver.

### 2. **Consistent Behavior**
Step standalone, phase standalone, and full pipeline all use same path resolution logic.

### 3. **Clear Error Messages**
```
PathResolutionError: Artifact 'user_configuration' not found in control_flows.yml.
Available artifacts: ['discovered_environment', 'system_configuration', 'tui_defaults_file']

Hint: Add to control_flows.yml under phase side_effects:
  - action: "writes"
    artifact: "user_configuration"
    location: "phases/phase_3_collection/outputs/collected_configuration.yml"
```

### 4. **Testing Improvements**
Can mock PathResolver to test phases with synthetic paths without touching filesystem.

### 5. **Multi-Repo Support**
PathResolver can be extended to resolve artifacts across repository boundaries for monorepo setups.

---

## Alternative Approaches Considered

### Alternative 1: Environment Variables
**Approach:** Use `PROJECT_ROOT` environment variable  
**Rejected:** Fragile, easy to forget, breaks in CI/CD, not explicit in code

### Alternative 2: Config File in Each Phase
**Approach:** Each phase has `phase_config.yml` with paths  
**Rejected:** Duplicates information, violates DRY, more files to maintain

### Alternative 3: Registry Pattern
**Approach:** Global registry of artifact locations  
**Rejected:** Too complex, harder to debug, potential race conditions in parallel execution

---

## Open Questions

1. **How to handle external artifacts?** (e.g., user-provided config files)
   - **Proposal:** Add `external_artifacts` section in control_flows.yml with placeholder paths

2. **How to handle temporary artifacts?** (intermediate files not in spec)
   - **Proposal:** PathResolver.get_temp_dir(phase_id) returns phase-specific temp directory

3. **Should PathResolver cache parsed control_flows.yml?**
   - **Proposal:** Yes, use singleton pattern to avoid re-parsing on every instantiation

4. **How to handle path resolution in tests?**
   - **Proposal:** Provide MockPathResolver for unit tests with configurable paths

---

## Implementation Checklist

- [ ] Create PathResolver class in control-flow repo
- [ ] Add comprehensive unit tests for PathResolver
- [ ] Update generator phase template with PathResolver integration
- [ ] Update generator step template with PathResolver integration
- [ ] Test generator with sample control flow
- [ ] Document PathResolver API and usage patterns
- [ ] Create migration guide for existing phases
- [ ] Regenerate config-manager phases with new templates
- [ ] Run full pipeline test suite
- [ ] Update ARCHITECTURE.md with path resolution design
- [ ] Add validation tools (validate_paths.py)
- [ ] Update CI/CD to validate path resolution

---

## Success Criteria

1. ✅ Step files produce output in correct location when run standalone
2. ✅ Phase orchestrators find inputs and produce outputs in correct location
3. ✅ Full pipeline execution works end-to-end
4. ✅ Moving a phase in control_flows.yml requires no code changes
5. ✅ Path resolution errors provide actionable debugging information
6. ✅ All existing tests pass with new path resolution system

---

## References

- Related Issues: phases/phases path doubling bug, Phase 3 output location mismatch
- Design Docs: RUNNABLE_CODE_PATTERN.md, control_flows.yml specification
- Similar Patterns: Django settings resolution, Flask app context, Bazel workspace resolution

