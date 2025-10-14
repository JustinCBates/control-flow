# Runnable Code Pattern - Standard Template

## Problem
Code cannot be tested at individual levels (step, phase, full pipeline) without modification.

## Solution: Three-Level Runnable Pattern

### Design Principles
1. **Every module has TWO entry points:**
   - `execute_*()` - Called by parent orchestrator (takes context dict)
   - `main()` - Standalone CLI entry point (parses args, builds context)

2. **Separation of concerns:**
   - Orchestrator interface: `execute_*()` functions
   - CLI interface: `main()` functions with argparse
   - Core logic: Classes and helper functions

3. **Always runnable:**
   - Every `.py` file ends with `if __name__ == "__main__": exit(main())`
   - No code changes needed to test at any level

### File Structure Template

```python
#!/usr/bin/env python3
"""
Module Description
"""

from pathlib import Path
from typing import Dict, Any
import logging
import argparse

logger = logging.getLogger(__name__)


# ============================================================================
# CORE IMPLEMENTATION
# ============================================================================

class MyImplementation:
    """Core implementation class."""
    
    def do_work(self):
        """Business logic here."""
        pass


# ============================================================================
# ORCHESTRATOR ENTRY POINT (called by parent)
# ============================================================================

def execute_my_step(context: Dict[str, Any], phase_dir: Path) -> Dict[str, Any]:
    """
    Orchestrator Entry Point
    
    Called by parent orchestrator. Receives context dict, returns result dict.
    
    Args:
        context: Execution context with input data
        phase_dir: Phase directory path
        
    Returns:
        Dict with step results
    """
    logger.info("Executing step...")
    
    # Extract inputs from context
    input_data = context.get('input_data')
    
    # Do work
    impl = MyImplementation()
    result = impl.do_work()
    
    # Return results for next step
    return {
        'step': 'my_step',
        'status': 'completed',
        'output_data': result
    }


# ============================================================================
# STANDALONE CLI ENTRY POINT (for testing)
# ============================================================================

def main():
    """
    Standalone Entry Point
    
    Parses CLI arguments, builds context, calls execute function.
    Allows running this step independently for testing.
    """
    parser = argparse.ArgumentParser(description="Step Description")
    parser.add_argument('--input', help='Input file path')
    parser.add_argument('--output', help='Output directory')
    
    args = parser.parse_args()
    
    # Build context from CLI args
    context = {
        'input_data': args.input
    }
    
    # Setup phase_dir
    phase_dir = Path(__file__).parent.parent
    
    try:
        # Call orchestrator entry point
        result = execute_my_step(context, phase_dir)
        
        print(f"✅ Step completed: {result['status']}")
        return 0
        
    except Exception as e:
        print(f"❌ Step failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
```

## Application to Config Manager

### Step Files
Each `step_N_*/step_name.py` should have:
- Class implementation (e.g., `DefaultsTransformer`)
- `execute_<step_name>()` - orchestrator entry point
- `main()` - standalone CLI with argparse
- `if __name__ == "__main__": exit(main())`

### Phase Orchestrators  
Each `phase_N/orchestrator_*.py` should have:
- `PhaseOrchestrator` class with `execute(context)` method
- `main()` - standalone CLI to run just this phase
- `if __name__ == "__main__": exit(main())`

### Main Orchestrator
`phases/phases_orchestrator.py` already has:
- `PhasesOrchestrator` class
- `main()` with argparse
- `if __name__ == "__main__": exit(main())`

## Benefits

1. **Test any level independently:**
   ```bash
   # Test a single step
   python3 phases/phase_1_discovery/step_1_env_discovery/env_discovery.py --output /tmp/test
   
   # Test a single phase
   python3 phases/phase_1_discovery/orchestrator_discovery.py --output /tmp/test
   
   # Test full pipeline
   python3 phases/phases_orchestrator.py --all
   ```

2. **No code changes needed** - works out of the box

3. **Consistent pattern** - every file follows same structure

4. **Easy debugging** - can test small units in isolation

5. **CI/CD friendly** - can test components independently

## Implementation Priority

1. ✅ Main orchestrator (already done)
2. 🔄 Phase orchestrators (add main() functions)
3. 🔄 Step files (add main() functions)

## Example Commands After Implementation

```bash
# Step level
./phases/phase_2_tui_mapping/step_1_transform_defaults/transform_defaults.py \
  --input phases/phase_1_discovery/outputs/enhanced_defaults.yml \
  --output /tmp/test

# Phase level  
./phases/phase_3_collection/orchestrator_collection.py \
  --tui-defaults phases/phase_2_tui_mapping/outputs/tui/tui_defaults.yml \
  --mock-responses mock_responses.json

# Full pipeline
./run_config_manager.sh --mock-responses mock_responses.json
```

All three levels work without modifying code!
