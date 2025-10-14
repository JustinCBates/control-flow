# Path Configuration Pattern for Control Flow Scripts

**Date:** October 14, 2025  
**Enhancement to PathResolver Implementation**

---

## Problem

While PathResolver auto-detects paths, developers benefit from:
1. **Explicit path declarations** at the top of scripts for clarity
2. **Easy override** for testing or non-standard layouts
3. **Documentation** of path assumptions
4. **IDE navigation** - can click to see what paths are used

---

## Solution: Path Configuration Block Pattern

Add a standardized configuration block at the top of each script that:
- Declares expected paths explicitly
- Can be overridden via environment variables
- Documents path structure
- Provides fallback to PathResolver auto-detection

---

## Implementation

### 1. Phase Orchestrator Pattern

```python
#!/usr/bin/env python3
"""
Phase: Collection Phase
Interactive user configuration collection
"""

# ============================================================================
# PATH CONFIGURATION
# ============================================================================
# These paths can be overridden via environment variables for testing
# or non-standard project layouts. If not set, PathResolver auto-detects.

import os
from pathlib import Path

# Project structure
PROJECT_ROOT = Path(os.getenv('PROJECT_ROOT', Path(__file__).parent.parent.parent)).resolve()
PHASE_DIR = Path(os.getenv('PHASE_DIR', Path(__file__).parent)).resolve()
PHASE_ID = os.getenv('PHASE_ID', 'collection')

# Input/Output directories
OUTPUTS_DIR = PHASE_DIR / "outputs"
TESTS_DIR = PHASE_DIR / "tests"

# External dependencies
CONTROL_FLOW_SPEC = PROJECT_ROOT / "design_specs" / "control_flows.yml"

# ============================================================================

from typing import Dict, Any
import logging
import sys

# Conditional imports
if __name__ == '__main__':
    sys.path.insert(0, str(PROJECT_ROOT))
    sys.path.insert(0, str(PROJECT_ROOT.parent / "control-flow/src"))
    from phases.phase_3_collection.step_1_collect_user_configuration import collect_user_configuration
    from control_flow_engine.runtime import PathResolver, PathResolutionError
else:
    from .step_1_collect_user_configuration import collect_user_configuration
    from control_flow_engine.runtime import PathResolver, PathResolutionError

logger = logging.getLogger(__name__)

# Log path configuration for debugging
logger.debug(f"Path Configuration:")
logger.debug(f"  PROJECT_ROOT: {PROJECT_ROOT}")
logger.debug(f"  PHASE_DIR: {PHASE_DIR}")
logger.debug(f"  OUTPUTS_DIR: {OUTPUTS_DIR}")


class CollectionPhase:
    """Interactive Collection Phase."""
    
    def __init__(self, project_root: Path = None, ui=None, path_resolver=None):
        # Use provided root or fall back to configured constant
        self.project_root = Path(project_root) if project_root else PROJECT_ROOT
        self.ui = ui
        self.phase_dir = PHASE_DIR
        
        # Initialize path resolver (prefer provided, fall back to auto-detect)
        if path_resolver:
            self.path_resolver = path_resolver
        else:
            try:
                self.path_resolver = PathResolver.from_execution_context(__file__)
                # Validate detected root matches our configuration
                detected_root = self.path_resolver.get_project_root()
                if detected_root != self.project_root:
                    logger.warning(
                        f"PathResolver detected different root: {detected_root} "
                        f"(configured: {self.project_root})"
                    )
            except PathResolutionError as e:
                logger.warning(f"PathResolver unavailable: {e}")
                self.path_resolver = None
        
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute collection phase."""
        if self.ui:
            self.ui.show_phase_header("Interactive Collection", "Collect user configuration")
        
        logger.info("Executing Interactive Collection")
        
        # Use PathResolver if available, otherwise use configured paths
        if self.path_resolver:
            try:
                output_file = self.path_resolver.resolve_artifact_path(
                    'user_configuration',
                    create_parent=True
                )
            except PathResolutionError:
                logger.warning("PathResolver failed, using configured path")
                output_file = OUTPUTS_DIR / "collected_configuration.yml"
        else:
            output_file = OUTPUTS_DIR / "collected_configuration.yml"
        
        # Execute step
        step_result = collect_user_configuration.execute_collect_user_configuration(
            context, 
            self.phase_dir
        )
        
        return {
            'user_configuration_file': str(output_file),
            'user_configuration': str(output_file)
        }


def main():
    """Standalone entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description=f"Phase: Interactive Collection\nPhase ID: {PHASE_ID}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Path Configuration:
  PROJECT_ROOT: {PROJECT_ROOT}
  PHASE_DIR: {PHASE_DIR}
  OUTPUTS_DIR: {OUTPUTS_DIR}

Environment Variables:
  PROJECT_ROOT: Override project root directory
  PHASE_DIR: Override phase directory
  PHASE_ID: Override phase identifier
        """
    )
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--show-paths', action='store_true', help='Show path configuration and exit')
    
    args = parser.parse_args()
    
    if args.show_paths:
        print("\n" + "=" * 70)
        print("PATH CONFIGURATION")
        print("=" * 70)
        print(f"  PROJECT_ROOT:   {PROJECT_ROOT}")
        print(f"  PHASE_DIR:      {PHASE_DIR}")
        print(f"  PHASE_ID:       {PHASE_ID}")
        print(f"  OUTPUTS_DIR:    {OUTPUTS_DIR}")
        print(f"  TESTS_DIR:      {TESTS_DIR}")
        print(f"  CONTROL_SPEC:   {CONTROL_FLOW_SPEC}")
        print("\nEnvironment Overrides:")
        print(f"  PROJECT_ROOT:   {os.getenv('PROJECT_ROOT', '(not set)')}")
        print(f"  PHASE_DIR:      {os.getenv('PHASE_DIR', '(not set)')}")
        print(f"  PHASE_ID:       {os.getenv('PHASE_ID', '(not set)')}")
        print("=" * 70)
        return 0
    
    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Initialize phase
        phase = CollectionPhase(project_root=PROJECT_ROOT, ui=None)
        
        # Execute
        result = phase.execute({})
        
        print("\n" + "=" * 70)
        print("✅ PHASE COMPLETE: Interactive Collection")
        print("=" * 70)
        for key, value in result.items():
            print(f"  • {key}: {value}")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Phase failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
```

### 2. Step File Pattern

```python
#!/usr/bin/env python3
"""
Step: Collect User Configuration
Load TUI layout and collect user input
"""

# ============================================================================
# PATH CONFIGURATION
# ============================================================================

import os
from pathlib import Path

# Project structure
PROJECT_ROOT = Path(os.getenv('PROJECT_ROOT', Path(__file__).parent.parent.parent.parent)).resolve()
STEP_DIR = Path(os.getenv('STEP_DIR', Path(__file__).parent)).resolve()
PHASE_DIR = STEP_DIR.parent
PHASE_ID = os.getenv('PHASE_ID', 'collection')

# Step-specific directories
LAYOUTS_DIR = STEP_DIR / "layouts"
DEFAULT_OUTPUT_DIR = PHASE_DIR / "outputs"

# ============================================================================

from typing import Dict, Any, Optional
import logging
import sys

# Conditional imports
if __name__ == '__main__':
    sys.path.insert(0, str(PROJECT_ROOT))
    sys.path.insert(0, str(PROJECT_ROOT.parent / "control-flow/src"))
    from control_flow_engine.runtime import PathResolver, PathResolutionError
else:
    try:
        from control_flow_engine.runtime import PathResolver, PathResolutionError
    except ImportError:
        PathResolver = None
        PathResolutionError = Exception

logger = logging.getLogger(__name__)


def execute_collect_user_configuration(context: Dict[str, Any], phase_dir: Path) -> Dict[str, Any]:
    """
    Execute user configuration collection step.
    
    Args:
        context: Execution context
        phase_dir: Phase directory (can override PHASE_DIR constant)
    
    Returns:
        Step results dictionary
    """
    # Use provided phase_dir or configured constant
    phase_dir = Path(phase_dir) if phase_dir else PHASE_DIR
    
    logger.info("Executing step: Collect User Configuration")
    logger.debug(f"Using phase_dir: {phase_dir}")
    logger.debug(f"Layouts dir: {LAYOUTS_DIR}")
    
    # Step implementation...
    
    return {
        'step': 'collect_user_configuration',
        'status': 'completed'
    }


def main():
    """Standalone entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Step: Collect User Configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Path Configuration:
  PROJECT_ROOT: {PROJECT_ROOT}
  STEP_DIR: {STEP_DIR}
  PHASE_DIR: {PHASE_DIR}
  PHASE_ID: {PHASE_ID}
  LAYOUTS_DIR: {LAYOUTS_DIR}
  DEFAULT_OUTPUT_DIR: {DEFAULT_OUTPUT_DIR}

Environment Variables:
  PROJECT_ROOT: Override project root directory
  STEP_DIR: Override step directory
  PHASE_ID: Override phase identifier
        """
    )
    parser.add_argument('--output-dir', help='Override output directory')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--show-paths', action='store_true', help='Show path configuration and exit')
    
    args = parser.parse_args()
    
    if args.show_paths:
        print("\n" + "=" * 70)
        print("PATH CONFIGURATION")
        print("=" * 70)
        print(f"  PROJECT_ROOT:         {PROJECT_ROOT}")
        print(f"  STEP_DIR:             {STEP_DIR}")
        print(f"  PHASE_DIR:            {PHASE_DIR}")
        print(f"  PHASE_ID:             {PHASE_ID}")
        print(f"  LAYOUTS_DIR:          {LAYOUTS_DIR}")
        print(f"  DEFAULT_OUTPUT_DIR:   {DEFAULT_OUTPUT_DIR}")
        print("=" * 70)
        return 0
    
    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Determine output directory (priority: CLI arg > PathResolver > constant)
        if args.output_dir:
            output_dir = Path(args.output_dir)
            logger.info(f"Using CLI output dir: {output_dir}")
        elif PathResolver:
            try:
                resolver = PathResolver.from_execution_context(__file__)
                output_dir = resolver.resolve_phase_output_dir(PHASE_ID, create=True)
                logger.info(f"Using PathResolver output dir: {output_dir}")
            except PathResolutionError as e:
                logger.warning(f"PathResolver failed: {e}")
                output_dir = DEFAULT_OUTPUT_DIR
                logger.info(f"Using default output dir: {output_dir}")
        else:
            output_dir = DEFAULT_OUTPUT_DIR
            logger.info(f"Using default output dir: {output_dir}")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Execute step
        result = execute_collect_user_configuration({}, PHASE_DIR)
        
        print("\n" + "=" * 70)
        print(f"✅ Step completed: {result.get('status', 'unknown')}")
        print("=" * 70)
        print(f"  Output directory: {output_dir}")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Step failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
```

---

## Benefits

### 1. **Explicit and Visible**
```python
# At the top of every file - immediately clear
PROJECT_ROOT = Path(os.getenv('PROJECT_ROOT', Path(__file__).parent.parent.parent)).resolve()
PHASE_DIR = Path(os.getenv('PHASE_DIR', Path(__file__).parent)).resolve()
```

### 2. **Environment Variable Override**
```bash
# Test with alternate layout
PROJECT_ROOT=/tmp/test-project python3 orchestrator_collection.py

# Override phase directory
PHASE_DIR=/custom/location python3 collect_user_configuration.py
```

### 3. **Show Paths Flag**
```bash
$ python3 orchestrator_collection.py --show-paths

======================================================================
PATH CONFIGURATION
======================================================================
  PROJECT_ROOT:   /opt/openproject/external/config-manager
  PHASE_DIR:      /opt/openproject/external/config-manager/phases/phase_3_collection
  PHASE_ID:       collection
  OUTPUTS_DIR:    /opt/openproject/external/config-manager/phases/phase_3_collection/outputs
  TESTS_DIR:      /opt/openproject/external/config-manager/phases/phase_3_collection/tests
  CONTROL_SPEC:   /opt/openproject/external/config-manager/design_specs/control_flows.yml

Environment Overrides:
  PROJECT_ROOT:   (not set)
  PHASE_DIR:      (not set)
  PHASE_ID:       (not set)
======================================================================
```

### 4. **Self-Documenting**
```python
# Clear documentation of path structure
parser = argparse.ArgumentParser(
    epilog="""
Path Configuration:
  PROJECT_ROOT: {PROJECT_ROOT}
  PHASE_DIR: {PHASE_DIR}
  OUTPUTS_DIR: {OUTPUTS_DIR}
    """
)
```

### 5. **Validation**
```python
# Warn if PathResolver detects different root
detected_root = self.path_resolver.get_project_root()
if detected_root != self.project_root:
    logger.warning(
        f"PathResolver detected different root: {detected_root} "
        f"(configured: {self.project_root})"
    )
```

---

## Integration with PathResolver

The path configuration pattern **complements** PathResolver:

```python
# Priority chain:
# 1. Explicit parameter (highest priority)
# 2. Environment variable
# 3. PathResolver auto-detection
# 4. Hardcoded constant (fallback)

if explicit_param:
    path = explicit_param
elif os.getenv('PROJECT_ROOT'):
    path = Path(os.getenv('PROJECT_ROOT'))
elif path_resolver:
    path = path_resolver.get_project_root()
else:
    path = PROJECT_ROOT  # Constant fallback
```

---

## Generator Template Integration

Update generator templates to include path configuration block:

```python
def _generate_phase_content(self, phase: PhaseConfig) -> str:
    """Generate phase file with path configuration block."""
    
    path_config_block = f'''
# ============================================================================
# PATH CONFIGURATION
# ============================================================================

import os
from pathlib import Path

PROJECT_ROOT = Path(os.getenv('PROJECT_ROOT', Path(__file__).parent.parent.parent)).resolve()
PHASE_DIR = Path(os.getenv('PHASE_DIR', Path(__file__).parent)).resolve()
PHASE_ID = os.getenv('PHASE_ID', '{phase.phase_id}')
OUTPUTS_DIR = PHASE_DIR / "outputs"
CONTROL_FLOW_SPEC = PROJECT_ROOT / "design_specs" / "control_flows.yml"

# ============================================================================
'''
    
    return f'''"""
Phase: {phase.name}
{phase.description}
"""

{path_config_block}

from typing import Dict, Any
import logging
...
'''
```

---

## Usage Examples

### Example 1: Normal Execution
```bash
# Uses auto-detected paths
python3 orchestrator_collection.py
```

### Example 2: Test with Alternate Root
```bash
# Override project root for testing
PROJECT_ROOT=/tmp/test-config python3 orchestrator_collection.py
```

### Example 3: Debug Path Issues
```bash
# Show configured paths
python3 orchestrator_collection.py --show-paths --verbose
```

### Example 4: CI/CD Override
```bash
# In CI, use explicit paths
export PROJECT_ROOT=/workspace/config-manager
export PHASE_ID=collection
python3 orchestrator_collection.py
```

---

## Comparison

| Aspect | PathResolver Only | With Path Config Block | Both Combined |
|--------|------------------|----------------------|---------------|
| Auto-detection | ✅ Yes | ❌ No | ✅ Yes |
| Explicit paths | ❌ Hidden | ✅ Visible | ✅ Visible |
| Easy override | ❌ Hard | ✅ Easy (env vars) | ✅ Easy |
| Documentation | ❌ In code | ✅ At top | ✅ Both |
| Testability | ⚠️ Mock needed | ✅ Env vars | ✅ Best of both |
| IDE navigation | ❌ Hard | ✅ Easy | ✅ Easy |

---

## Recommendation

**Use both patterns together:**

1. **Path Configuration Block** - Explicit, visible, overridable
2. **PathResolver** - Auto-detection, validation, artifact resolution

This gives you:
- ✅ Explicit documentation of path assumptions
- ✅ Easy testing via environment variables
- ✅ Validation that detected paths match expectations
- ✅ Fallback if PathResolver unavailable
- ✅ `--show-paths` flag for debugging

---

## Next Steps

1. Update generator templates to include path configuration block
2. Add `--show-paths` flag to all generated scripts
3. Document environment variable overrides in README
4. Create path validation tests

