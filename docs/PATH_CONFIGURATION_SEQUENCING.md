# Path Configuration with Logical-Physical Separation

**Date:** October 14, 2025  
**Enhancement: Handling Phase/Step Renumbering**

---

## Problem Statement

Current directory structure uses numbered sequences that break when phases are reordered:

```
phases/
├── phase_1_discovery/           # What if we insert a new phase 1?
├── phase_2_tui_mapping/         # Would this become phase_3?
├── phase_3_collection/          # Would this become phase_4?
├── phase_4_validation/
└── phase_5_export/
```

**Issues:**
1. Insert new phase → all subsequent numbers shift
2. Delete a phase → gap in numbering or need to renumber
3. Move a phase → physical directory must be renamed
4. **Hard to maintain:** Code references hardcoded directory names

---

## Solution: Logical ID vs Physical Location Separation

### Concept

Separate **logical identity** (phase_id) from **physical location** (directory name):

```yaml
# control_flows.yml
phases:
  - phase_id: "discovery"              # ← Logical ID (stable)
    sequence: 10                       # ← Ordering number (can have gaps)
    implementation:
      phase_directory: "phases/phase_1_discovery/"  # ← Physical location
```

### Path Configuration Enhancement

```python
# ============================================================================
# PATH CONFIGURATION - Enhanced with Logical/Physical Separation
# ============================================================================

import os
from pathlib import Path

# Logical identity (stable - never changes even when reordered)
PHASE_ID = os.getenv('PHASE_ID', 'collection')        # Logical identifier
STEP_ID = os.getenv('STEP_ID', 'collect_user_config') # Step identifier

# Physical location (can change when reordered)
PHASE_SEQUENCE = int(os.getenv('PHASE_SEQUENCE', '3'))  # Current sequence number
STEP_SEQUENCE = int(os.getenv('STEP_SEQUENCE', '1'))    # Step sequence number

# Auto-compute directory names from sequence numbers
PHASE_DIR_NAME = f"phase_{PHASE_SEQUENCE}_{PHASE_ID}"
STEP_DIR_NAME = f"step_{STEP_SEQUENCE}_{STEP_ID}"

# Project structure
PROJECT_ROOT = Path(os.getenv('PROJECT_ROOT', Path(__file__).parent.parent.parent)).resolve()
PHASE_DIR = Path(os.getenv('PHASE_DIR', PROJECT_ROOT / "phases" / PHASE_DIR_NAME)).resolve()
STEP_DIR = Path(os.getenv('STEP_DIR', PHASE_DIR / STEP_DIR_NAME)).resolve()

# Outputs
OUTPUTS_DIR = PHASE_DIR / "outputs"

# ============================================================================
```

---

## Usage Scenarios

### Scenario 1: Normal Operation (No Changes)

```python
# phase_3_collection/orchestrator_collection.py

PHASE_ID = 'collection'        # Stable
PHASE_SEQUENCE = 3             # Current position
# Results in: phases/phase_3_collection/
```

### Scenario 2: Insert New Phase Before Collection

```yaml
# control_flows.yml - Insert "preprocessing" phase before collection
phases:
  - phase_id: "discovery"
    sequence: 10
    phase_directory: "phases/phase_1_discovery/"
    
  - phase_id: "tui_mapping"
    sequence: 20
    phase_directory: "phases/phase_2_tui_mapping/"
    
  - phase_id: "preprocessing"        # ← NEW PHASE
    sequence: 25                     # Inserted between 20 and 30
    phase_directory: "phases/phase_3_preprocessing/"
    
  - phase_id: "collection"           # This was phase 3
    sequence: 30                     # Now effectively "phase 4"
    phase_directory: "phases/phase_4_collection/"  # ← Directory renamed
```

**Update the collection phase:**
```bash
# 1. Rename directory
mv phases/phase_3_collection phases/phase_4_collection

# 2. Update environment or config
PHASE_SEQUENCE=4 python3 phases/phase_4_collection/orchestrator_collection.py

# Or update the constant in the file:
# PHASE_SEQUENCE = int(os.getenv('PHASE_SEQUENCE', '4'))  # Changed from 3
```

### Scenario 3: Use Logical IDs Only (No Numbers)

**Even better approach** - stop using sequence numbers in directory names:

```yaml
# control_flows.yml
phases:
  - phase_id: "discovery"
    sequence: 10                                    # For ordering only
    phase_directory: "phases/discovery/"            # ← No number!
    
  - phase_id: "tui_mapping"
    sequence: 20
    phase_directory: "phases/tui_mapping/"
    
  - phase_id: "preprocessing"                       # New phase
    sequence: 25
    phase_directory: "phases/preprocessing/"        # Easy insertion!
    
  - phase_id: "collection"
    sequence: 30
    phase_directory: "phases/collection/"           # No rename needed!
```

Now insertion/deletion requires:
- ✅ Update control_flows.yml only
- ✅ No directory renaming
- ✅ No code changes

---

## Recommended Path Configuration Pattern

### Option A: Dynamic Sequence-Based (Maximum Flexibility)

```python
# ============================================================================
# PATH CONFIGURATION - Sequence-Aware
# ============================================================================

import os
from pathlib import Path

# === PHASE IDENTITY ===
PHASE_ID = os.getenv('PHASE_ID', 'collection')
PHASE_SEQUENCE = int(os.getenv('PHASE_SEQUENCE', '3'))

# === DYNAMIC PATH CONSTRUCTION ===
# Directory name computed from sequence + ID (can change when reordered)
PHASE_DIR_NAME = os.getenv('PHASE_DIR_NAME', f"phase_{PHASE_SEQUENCE}_{PHASE_ID}")

# Project structure
PROJECT_ROOT = Path(os.getenv('PROJECT_ROOT', Path(__file__).parent.parent.parent)).resolve()
PHASE_DIR = Path(os.getenv('PHASE_DIR', PROJECT_ROOT / "phases" / PHASE_DIR_NAME)).resolve()
OUTPUTS_DIR = PHASE_DIR / "outputs"

# === PATHRESOLVER INTEGRATION ===
# Use PathResolver as source of truth for artifact locations
from control_flow_engine.runtime import PathResolver, PathResolutionError

try:
    PATH_RESOLVER = PathResolver.from_execution_context(__file__)
    
    # Validate our configuration against PathResolver
    resolver_phase_dir = PATH_RESOLVER.resolve_phase_directory(PHASE_ID)
    if resolver_phase_dir != PHASE_DIR:
        import logging
        logging.getLogger(__name__).warning(
            f"Path mismatch detected!\n"
            f"  Configured: {PHASE_DIR}\n"
            f"  Resolver:   {resolver_phase_dir}\n"
            f"  Using resolver path for safety."
        )
        PHASE_DIR = resolver_phase_dir
        OUTPUTS_DIR = PHASE_DIR / "outputs"
        
except PathResolutionError:
    PATH_RESOLVER = None
    # Use configured paths as fallback

# ============================================================================
```

**Benefits:**
- ✅ Can handle renumbering via environment variables
- ✅ PathResolver validates configuration
- ✅ Clear error messages when paths mismatch
- ✅ Fallback to configured constants

### Option B: Logical ID Only (Recommended)

```python
# ============================================================================
# PATH CONFIGURATION - Logical ID Based (RECOMMENDED)
# ============================================================================

import os
from pathlib import Path

# === PHASE IDENTITY (Stable - never changes) ===
PHASE_ID = os.getenv('PHASE_ID', 'collection')

# === PATH RESOLUTION ===
# Primary: Use PathResolver to get directory from logical ID
# Fallback: Construct from convention (no sequence numbers)

PROJECT_ROOT = Path(os.getenv('PROJECT_ROOT', Path(__file__).parent.parent.parent)).resolve()

# Try PathResolver first (source of truth from control_flows.yml)
try:
    from control_flow_engine.runtime import PathResolver, PathResolutionError
    PATH_RESOLVER = PathResolver.from_execution_context(__file__)
    
    # Get phase directory from logical ID
    PHASE_DIR = PATH_RESOLVER.resolve_phase_directory(PHASE_ID)
    OUTPUTS_DIR = PATH_RESOLVER.resolve_phase_output_dir(PHASE_ID, create=False)
    
except (PathResolutionError, ImportError):
    # Fallback: Use convention-based path (no sequence number)
    PHASE_DIR = Path(os.getenv('PHASE_DIR', PROJECT_ROOT / "phases" / PHASE_ID)).resolve()
    OUTPUTS_DIR = PHASE_DIR / "outputs"
    PATH_RESOLVER = None

# ============================================================================
```

**Benefits:**
- ✅ **Best approach** - logical ID is stable
- ✅ No renumbering needed on insertions
- ✅ PathResolver determines physical location
- ✅ Clean directory names (`phases/collection/` not `phases/phase_3_collection/`)

---

## Migration Strategy: Removing Sequence Numbers

### Phase 1: Add Sequence Variable (No Breaking Changes)

Current: `phases/phase_3_collection/`  
Keep directory name, but add sequence awareness:

```python
PHASE_SEQUENCE = 3
PHASE_DIR_NAME = f"phase_{PHASE_SEQUENCE}_{PHASE_ID}"
```

### Phase 2: Make Sequence Overridable

Allow renumbering without code changes:

```bash
# After renumbering from 3 to 4
PHASE_SEQUENCE=4 python3 phases/phase_4_collection/orchestrator.py
```

### Phase 3: Migrate to Logical IDs Only

```bash
# Rename directories to remove numbers
mv phases/phase_1_discovery phases/discovery
mv phases/phase_2_tui_mapping phases/tui_mapping
mv phases/phase_3_collection phases/collection
mv phases/phase_4_validation phases/validation
mv phases/phase_5_export phases/export

# Update control_flows.yml
phases:
  - phase_id: "discovery"
    sequence: 10
    phase_directory: "phases/discovery/"  # No number!
```

Now insertions are trivial:
```bash
# Insert new phase - just add directory
mkdir phases/preprocessing
# Update control_flows.yml - no renaming needed!
```

---

## Enhanced control_flows.yml Schema

```yaml
phases:
  - phase_id: "discovery"                    # Logical ID (stable)
    name: "Discovery Phase"
    sequence: 10                             # Ordering (can have gaps: 10, 20, 30...)
    
    implementation:
      # Physical location (determined by PathResolver)
      phase_directory: "phases/discovery/"   # Clean name, no sequence
      orchestrator_file: "phases/discovery/orchestrator.py"
      
    # Path configuration for generated code
    path_config:
      logical_id: "discovery"                # Used in code PHASE_ID constant
      use_sequence_in_path: false            # Don't use numbers in directory names
```

---

## Code Generation Template Update

```python
def _generate_phase_content(self, phase: PhaseConfig) -> str:
    """Generate phase with enhanced path configuration."""
    
    # Determine if using sequence-based or logical-only paths
    use_sequence = phase.get('path_config', {}).get('use_sequence_in_path', True)
    
    if use_sequence:
        path_config = f'''
# === PHASE IDENTITY ===
PHASE_ID = os.getenv('PHASE_ID', '{phase.phase_id}')
PHASE_SEQUENCE = int(os.getenv('PHASE_SEQUENCE', '{phase.sequence}'))
PHASE_DIR_NAME = f"phase_{{PHASE_SEQUENCE}}_{{PHASE_ID}}"

# === PROJECT STRUCTURE ===
PROJECT_ROOT = Path(os.getenv('PROJECT_ROOT', Path(__file__).parent.parent.parent)).resolve()
PHASE_DIR = PROJECT_ROOT / "phases" / PHASE_DIR_NAME
'''
    else:
        path_config = f'''
# === PHASE IDENTITY (Logical ID - stable) ===
PHASE_ID = os.getenv('PHASE_ID', '{phase.phase_id}')

# === PATH RESOLUTION (Via PathResolver) ===
try:
    from control_flow_engine.runtime import PathResolver
    PATH_RESOLVER = PathResolver.from_execution_context(__file__)
    PHASE_DIR = PATH_RESOLVER.resolve_phase_directory(PHASE_ID)
except:
    # Fallback
    PROJECT_ROOT = Path(os.getenv('PROJECT_ROOT', Path(__file__).parent.parent.parent)).resolve()
    PHASE_DIR = PROJECT_ROOT / "phases" / PHASE_ID
'''
    
    return f'''"""
Phase: {phase.name}
"""

# ============================================================================
# PATH CONFIGURATION
# ============================================================================

import os
from pathlib import Path

{path_config}

OUTPUTS_DIR = PHASE_DIR / "outputs"

# ============================================================================

from typing import Dict, Any
import logging
...
'''
```

---

## Comparison of Approaches

| Approach | Insertion | Deletion | Move | Code Changes | Dir Rename |
|----------|-----------|----------|------|--------------|------------|
| **Hardcoded paths** | ❌ Hard | ❌ Hard | ❌ Hard | ❌ Required | ✅ Required |
| **PROJECT_ROOT only** | ❌ Hard | ❌ Hard | ❌ Hard | ✅ None | ✅ Required |
| **Sequence variable** | ⚠️ Medium | ⚠️ Medium | ⚠️ Medium | ⚠️ Update var | ✅ Required |
| **PathResolver + Sequence** | ✅ Easy | ✅ Easy | ✅ Easy | ✅ None | ✅ Required |
| **Logical ID only** | ✅✅ Easiest | ✅✅ Easiest | ✅✅ Easiest | ✅ None | ✅ Not needed |

---

## Recommendation

**Use Option B: Logical ID Only** (no sequence numbers in directories)

```python
# Path configuration (clean and simple)
PHASE_ID = 'collection'
PHASE_DIR = PATH_RESOLVER.resolve_phase_directory(PHASE_ID)
```

```yaml
# control_flows.yml
phases:
  - phase_id: "discovery"
    sequence: 10
    phase_directory: "phases/discovery/"      # ← No numbers!
```

**Why:**
1. ✅ Insertions/deletions only update YAML
2. ✅ No directory renaming ever needed
3. ✅ Clean directory names
4. ✅ PathResolver handles all path logic
5. ✅ Sequence field exists only for ordering in YAML

**Migration Path:**
1. Add sequence variable to existing files (keep current names)
2. Make sequence overridable via environment
3. Gradually rename directories to remove numbers
4. Update control_flows.yml to match
5. Remove sequence from path calculation

---

## Implementation Checklist

- [ ] Add `sequence` field to control_flows.yml
- [ ] Update PathResolver to ignore sequence in paths
- [ ] Add PHASE_SEQUENCE variable to existing files
- [ ] Create migration script to rename directories
- [ ] Update generator to use logical IDs only
- [ ] Test insertion/deletion workflows
- [ ] Document new pattern in ARCHITECTURE.md

