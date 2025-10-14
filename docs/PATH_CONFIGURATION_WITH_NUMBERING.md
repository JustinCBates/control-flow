# Path Configuration: Keeping Sequence Numbers with Flexibility

**Date:** October 14, 2025  
**Solution: Best of Both Worlds**

---

## Design Goal

**Keep numbered folders for visual ordering** while making insertions/moves/deletions manageable through:
1. Decoupling logical ID from physical sequence number
2. Using PathResolver as source of truth
3. Making sequence numbers overridable

---

## The Hybrid Solution

### Directory Structure (Keep Numbers!)

```
phases/
├── phase_1_discovery/          ✅ Keep numbering for visual order
├── phase_2_tui_mapping/
├── phase_3_collection/
├── phase_4_validation/
└── phase_5_export/
```

### Path Configuration Pattern

```python
# ============================================================================
# PATH CONFIGURATION
# ============================================================================

import os
from pathlib import Path

# === PHASE IDENTITY ===
# Logical ID: Stable identifier (never changes)
PHASE_ID = os.getenv('PHASE_ID', 'collection')

# Physical Sequence: Current position in execution order
# Can be overridden when phases are reordered
PHASE_SEQUENCE = int(os.getenv('PHASE_SEQUENCE', '3'))

# === DIRECTORY NAME CONSTRUCTION ===
# Computed from sequence + logical ID
# Override entire name if directory was manually renamed
PHASE_DIR_NAME = os.getenv('PHASE_DIR_NAME', f"phase_{PHASE_SEQUENCE}_{PHASE_ID}")

# === PROJECT STRUCTURE ===
PROJECT_ROOT = Path(os.getenv('PROJECT_ROOT', Path(__file__).parent.parent.parent)).resolve()
PHASES_ROOT = PROJECT_ROOT / "phases"

# === PATH RESOLUTION (Three-tier priority) ===
# 1. Explicit PHASE_DIR environment override (highest priority)
# 2. PathResolver from control_flows.yml (source of truth)
# 3. Computed from PHASE_DIR_NAME (fallback)

if os.getenv('PHASE_DIR'):
    # Explicit override
    PHASE_DIR = Path(os.getenv('PHASE_DIR')).resolve()
else:
    # Try PathResolver first (gets actual path from control_flows.yml)
    try:
        from control_flow_engine.runtime import PathResolver, PathResolutionError
        _resolver = PathResolver.from_execution_context(__file__)
        PHASE_DIR = _resolver.resolve_phase_directory(PHASE_ID)
    except (PathResolutionError, ImportError):
        # Fallback: construct from sequence + ID
        PHASE_DIR = (PHASES_ROOT / PHASE_DIR_NAME).resolve()

OUTPUTS_DIR = PHASE_DIR / "outputs"

# ============================================================================
```

---

## Workflow: Inserting a New Phase

### Scenario: Insert "preprocessing" between phase 2 and 3

**Before:**
```
phases/
├── phase_1_discovery/
├── phase_2_tui_mapping/
├── phase_3_collection/          ← Currently phase 3
├── phase_4_validation/
└── phase_5_export/
```

**After Insertion:**
```
phases/
├── phase_1_discovery/
├── phase_2_tui_mapping/
├── phase_3_preprocessing/        ← NEW (takes sequence 3)
├── phase_4_collection/           ← Was phase 3, now phase 4
├── phase_5_validation/           ← Was phase 4, now phase 5
└── phase_6_export/               ← Was phase 5, now phase 6
```

### Step-by-Step Process

#### Step 1: Update control_flows.yml

```yaml
phases:
  - phase_id: "discovery"
    sequence: 1
    phase_directory: "phases/phase_1_discovery/"
    
  - phase_id: "tui_mapping"
    sequence: 2
    phase_directory: "phases/phase_2_tui_mapping/"
    
  - phase_id: "preprocessing"        # ← NEW PHASE
    sequence: 3
    phase_directory: "phases/phase_3_preprocessing/"
    
  - phase_id: "collection"
    sequence: 4                      # ← Changed from 3
    phase_directory: "phases/phase_4_collection/"  # ← Changed
    
  - phase_id: "validation"
    sequence: 5                      # ← Changed from 4
    phase_directory: "phases/phase_5_validation/"  # ← Changed
    
  - phase_id: "export"
    sequence: 6                      # ← Changed from 5
    phase_directory: "phases/phase_6_export/"      # ← Changed
```

#### Step 2: Rename Physical Directories (Script-Assisted)

```bash
#!/bin/bash
# renumber_phases.sh - Automate directory renaming

# Rename in reverse order to avoid conflicts
mv phases/phase_5_export phases/phase_6_export
mv phases/phase_4_validation phases/phase_5_validation
mv phases/phase_3_collection phases/phase_4_collection

# Create new phase directory
mkdir -p phases/phase_3_preprocessing
# ... scaffold new phase files
```

#### Step 3: Update Phase Constants (One Line Per File)

**collection/orchestrator_collection.py:**
```python
# Old:
PHASE_SEQUENCE = int(os.getenv('PHASE_SEQUENCE', '3'))

# New:
PHASE_SEQUENCE = int(os.getenv('PHASE_SEQUENCE', '4'))  # Changed from 3
```

**validation/orchestrator_validation.py:**
```python
# Old:
PHASE_SEQUENCE = int(os.getenv('PHASE_SEQUENCE', '4'))

# New:
PHASE_SEQUENCE = int(os.getenv('PHASE_SEQUENCE', '5'))  # Changed from 4
```

**export/orchestrator_export.py:**
```python
# Old:
PHASE_SEQUENCE = int(os.getenv('PHASE_SEQUENCE', '5'))

# New:
PHASE_SEQUENCE = int(os.getenv('PHASE_SEQUENCE', '6'))  # Changed from 5
```

#### Step 4: Verify with --show-paths

```bash
# Check each phase reports correct paths
python3 phases/phase_4_collection/orchestrator_collection.py --show-paths
python3 phases/phase_5_validation/orchestrator_validation.py --show-paths
python3 phases/phase_6_export/orchestrator_export.py --show-paths
```

---

## Automation: Renumbering Script

Create a script to handle the mechanical parts:

```python
#!/usr/bin/env python3
"""
renumber_phases.py - Automated phase renumbering tool

Usage:
    # Insert new phase at position 3
    python3 renumber_phases.py insert --at 3 --name preprocessing
    
    # Delete phase 3
    python3 renumber_phases.py delete --at 3
    
    # Move phase 3 to position 5
    python3 renumber_phases.py move --from 3 --to 5
"""

import argparse
import shutil
import yaml
from pathlib import Path
import re


def load_control_flows(project_root: Path):
    """Load control_flows.yml"""
    spec_file = project_root / "design_specs" / "control_flows.yml"
    with open(spec_file) as f:
        return yaml.safe_load(f)


def save_control_flows(project_root: Path, spec):
    """Save control_flows.yml"""
    spec_file = project_root / "design_specs" / "control_flows.yml"
    with open(spec_file, 'w') as f:
        yaml.dump(spec, f, default_flow_style=False, sort_keys=False)


def update_phase_sequence_in_file(file_path: Path, old_seq: int, new_seq: int):
    """Update PHASE_SEQUENCE constant in a Python file"""
    content = file_path.read_text()
    
    # Match: PHASE_SEQUENCE = int(os.getenv('PHASE_SEQUENCE', '3'))
    pattern = rf"(PHASE_SEQUENCE\s*=\s*int\(os\.getenv\('PHASE_SEQUENCE',\s*')(\d+)('\)\))"
    
    def replacer(match):
        if int(match.group(2)) == old_seq:
            return f"{match.group(1)}{new_seq}{match.group(3)}"
        return match.group(0)
    
    new_content = re.sub(pattern, replacer, content)
    
    if new_content != content:
        file_path.write_text(new_content)
        return True
    return False


def rename_phase_directory(project_root: Path, old_num: int, new_num: int, phase_id: str):
    """Rename phase directory"""
    old_dir = project_root / "phases" / f"phase_{old_num}_{phase_id}"
    new_dir = project_root / "phases" / f"phase_{new_num}_{phase_id}"
    
    if old_dir.exists():
        print(f"  Renaming: {old_dir.name} → {new_dir.name}")
        shutil.move(str(old_dir), str(new_dir))
        return new_dir
    else:
        print(f"  Warning: {old_dir} does not exist")
        return None


def insert_phase(project_root: Path, position: int, phase_name: str):
    """Insert a new phase at the given position"""
    print(f"Inserting phase '{phase_name}' at position {position}")
    
    # Load spec
    spec = load_control_flows(project_root)
    flows = spec.get('flows', {})
    
    # Find the main flow
    main_flow = None
    for flow in flows.values():
        if 'phases' in flow:
            main_flow = flow
            break
    
    if not main_flow:
        print("Error: Could not find main flow")
        return
    
    phases = main_flow['phases']
    
    # Shift subsequent phases
    print(f"\nShifting phases {position} onwards...")
    
    # Rename directories in reverse order (to avoid conflicts)
    for i in range(len(phases) - 1, position - 1, -1):
        phase = phases[i]
        old_seq = i + 1
        new_seq = i + 2
        phase_id = phase['phase_id']
        
        # Rename directory
        new_dir = rename_phase_directory(project_root, old_seq, new_seq, phase_id)
        
        if new_dir:
            # Update control_flows.yml
            phase['sequence'] = new_seq
            phase['phase_directory'] = f"phases/phase_{new_seq}_{phase_id}/"
            
            # Update PHASE_SEQUENCE in orchestrator file
            orchestrator = new_dir / f"orchestrator_{phase_id}.py"
            if orchestrator.exists():
                if update_phase_sequence_in_file(orchestrator, old_seq, new_seq):
                    print(f"    Updated sequence in {orchestrator.name}")
    
    # Insert new phase placeholder
    print(f"\nCreating new phase '{phase_name}' at position {position}")
    new_phase_id = phase_name.lower().replace(' ', '_')
    new_dir = project_root / "phases" / f"phase_{position}_{new_phase_id}"
    new_dir.mkdir(parents=True, exist_ok=True)
    
    # Add to control_flows.yml
    new_phase_entry = {
        'phase_id': new_phase_id,
        'name': phase_name,
        'sequence': position,
        'status': 'PLANNED',
        'description': f'{phase_name} phase',
        'phase_directory': f'phases/phase_{position}_{new_phase_id}/',
        'implementation': {
            'phase_directory': f'phases/phase_{position}_{new_phase_id}/',
            'orchestrator_file': f'phases/phase_{position}_{new_phase_id}/orchestrator_{new_phase_id}.py'
        }
    }
    
    phases.insert(position - 1, new_phase_entry)
    
    # Save updated spec
    save_control_flows(project_root, spec)
    
    print(f"\n✅ Insertion complete!")
    print(f"   New phase directory: {new_dir}")
    print(f"   Updated control_flows.yml")
    print(f"\nNext steps:")
    print(f"   1. Scaffold new phase: python3 generator.py scaffold --phase {new_phase_id}")
    print(f"   2. Verify paths: python3 phases/phase_{position}_{new_phase_id}/orchestrator_{new_phase_id}.py --show-paths")


def main():
    parser = argparse.ArgumentParser(description="Phase renumbering automation")
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Insert command
    insert_parser = subparsers.add_parser('insert', help='Insert a new phase')
    insert_parser.add_argument('--at', type=int, required=True, help='Position to insert (1-based)')
    insert_parser.add_argument('--name', required=True, help='Phase name')
    insert_parser.add_argument('--project-root', default='.', help='Project root directory')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete a phase')
    delete_parser.add_argument('--at', type=int, required=True, help='Position to delete')
    delete_parser.add_argument('--project-root', default='.', help='Project root directory')
    
    # Move command
    move_parser = subparsers.add_parser('move', help='Move a phase')
    move_parser.add_argument('--from', dest='from_pos', type=int, required=True, help='Current position')
    move_parser.add_argument('--to', dest='to_pos', type=int, required=True, help='New position')
    move_parser.add_argument('--project-root', default='.', help='Project root directory')
    
    args = parser.parse_args()
    
    project_root = Path(args.project_root).resolve()
    
    if args.command == 'insert':
        insert_phase(project_root, args.at, args.name)
    elif args.command == 'delete':
        print("Delete functionality not yet implemented")
    elif args.command == 'move':
        print("Move functionality not yet implemented")
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
```

---

## Usage Examples

### Insert New Phase

```bash
# Insert preprocessing phase at position 3
python3 scripts/renumber_phases.py insert --at 3 --name "Preprocessing"

# Output:
# Inserting phase 'Preprocessing' at position 3
# 
# Shifting phases 3 onwards...
#   Renaming: phase_5_export → phase_6_export
#     Updated sequence in orchestrator_export.py
#   Renaming: phase_4_validation → phase_5_validation
#     Updated sequence in orchestrator_validation.py
#   Renaming: phase_3_collection → phase_4_collection
#     Updated sequence in orchestrator_collection.py
#
# Creating new phase 'Preprocessing' at position 3
#
# ✅ Insertion complete!
#    New phase directory: phases/phase_3_preprocessing
#    Updated control_flows.yml
```

### Manual Override During Transition

```bash
# If directories haven't been renamed yet, use environment override
PHASE_SEQUENCE=4 python3 phases/phase_3_collection/orchestrator_collection.py

# Or explicit directory override
PHASE_DIR=/opt/openproject/external/config-manager/phases/phase_4_collection \
    python3 phases/phase_4_collection/orchestrator_collection.py
```

---

## Path Configuration with Validation

Enhanced version that validates against PathResolver:

```python
# ============================================================================
# PATH CONFIGURATION WITH VALIDATION
# ============================================================================

import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# === PHASE IDENTITY ===
PHASE_ID = os.getenv('PHASE_ID', 'collection')
PHASE_SEQUENCE = int(os.getenv('PHASE_SEQUENCE', '3'))
PHASE_DIR_NAME = os.getenv('PHASE_DIR_NAME', f"phase_{PHASE_SEQUENCE}_{PHASE_ID}")

# === PROJECT STRUCTURE ===
PROJECT_ROOT = Path(os.getenv('PROJECT_ROOT', Path(__file__).parent.parent.parent)).resolve()
PHASES_ROOT = PROJECT_ROOT / "phases"

# === PATH RESOLUTION WITH VALIDATION ===
computed_path = PHASES_ROOT / PHASE_DIR_NAME

try:
    from control_flow_engine.runtime import PathResolver, PathResolutionError
    _resolver = PathResolver.from_execution_context(__file__)
    resolver_path = _resolver.resolve_phase_directory(PHASE_ID)
    
    # Validate: Does PathResolver path match our computed path?
    if resolver_path != computed_path:
        logger.warning(
            f"⚠️  Path mismatch detected for phase '{PHASE_ID}':\n"
            f"   Computed from sequence: {computed_path}\n"
            f"   From control_flows.yml: {resolver_path}\n"
            f"   Using control_flows.yml path (source of truth)"
        )
        PHASE_DIR = resolver_path
    else:
        PHASE_DIR = computed_path
        logger.debug(f"✅ Path validation passed: {PHASE_DIR}")
        
except (PathResolutionError, ImportError) as e:
    logger.debug(f"PathResolver unavailable ({e}), using computed path")
    PHASE_DIR = computed_path

OUTPUTS_DIR = PHASE_DIR / "outputs"

# ============================================================================
```

---

## Benefits of This Approach

✅ **Visual Ordering**: Numbered folders show execution sequence at a glance  
✅ **Manageable Insertions**: Script automates directory renaming  
✅ **Validation**: PathResolver checks computed paths against spec  
✅ **Override Capability**: Environment variables for testing/transitions  
✅ **Single Source of Truth**: control_flows.yml is authoritative  
✅ **Clear Errors**: Warns when paths don't match expectations  

---

## Summary

**Keep the folder numbering** for visual clarity, but make it manageable through:

1. **Path configuration constants** - Explicit PHASE_SEQUENCE variable
2. **Environment overrides** - Easy testing during transitions
3. **PathResolver validation** - Catches mismatches
4. **Automation script** - Handles mechanical renaming
5. **--show-paths flag** - Verify configuration

This gives you the best of both worlds: **numbered folders for clarity** and **manageable reordering through tooling**.

