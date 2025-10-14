# Phase Renumbering Quick Reference

## Script Location
```bash
/opt/openproject/external/control-flow/scripts/renumber_phases.py
```

## Quick Commands

### Insert Phase
```bash
python3 renumber_phases.py insert --at <pos> --name "<Name>" --id <id>

# Example
python3 renumber_phases.py insert --at 3 --name "Preprocessing" --id preprocessing
```

### Delete Phase
```bash
python3 renumber_phases.py delete --at <pos>

# Example
python3 renumber_phases.py delete --at 3
```

### Move Phase
```bash
python3 renumber_phases.py move --from <pos> --to <pos>

# Example
python3 renumber_phases.py move --from 2 --to 4
```

### Dry Run (Preview Only)
```bash
python3 renumber_phases.py --dry-run <operation> <args>

# Example
python3 renumber_phases.py --dry-run insert --at 3 --name "Test" --id test
```

## Typical Workflow

### 1. Insert New Phase
```bash
# Preview
python3 renumber_phases.py --dry-run insert --at 3 --name "Preprocessing" --id preprocessing

# Execute
python3 renumber_phases.py insert --at 3 --name "Preprocessing" --id preprocessing

# Generate code
python3 generator.py scaffold-phase --phase preprocessing

# Verify
python3 phases/phase_3_preprocessing/orchestrator_preprocessing.py --show-paths
```

### 2. Move Phase
```bash
# Preview
python3 renumber_phases.py --dry-run move --from 2 --to 4

# Execute
python3 renumber_phases.py move --from 2 --to 4

# Test
python3 phases/phases_orchestrator.py --start 1 --end 5
```

### 3. Delete Phase
```bash
# Preview
python3 renumber_phases.py --dry-run delete --at 3

# Execute (requires confirmation)
python3 renumber_phases.py delete --at 3
# Type: yes

# Archived to: archived_phases/
```

## What Gets Updated

- ✅ Directory names: `phase_N_id/` → `phase_M_id/`
- ✅ control_flows.yml: `sequence`, `phase_directory`, `orchestrator_file`
- ✅ Code constants: `PHASE_SEQUENCE` in orchestrator files
- ✅ All affected phases (not just target)

## Safety Features

- 🔍 **Dry-run mode** - Preview without changes
- 💾 **Archives** - Deleted phases saved to `archived_phases/`
- ✋ **Confirmation** - Delete requires typing "yes"
- ✅ **Clear output** - Progress indicators and warnings
- 🔄 **Git-friendly** - Can revert with `git reset --hard`

## Common Patterns

### Best Practice: Always Preview First
```bash
python3 renumber_phases.py --dry-run <operation> <args>
# Review output
python3 renumber_phases.py <operation> <args>
```

### Use with Version Control
```bash
git add -A && git commit -m "Before renumbering"
python3 renumber_phases.py <operation> <args>
git diff  # Review changes
git commit -m "After renumbering" # or git reset --hard if wrong
```

### Verify After Changes
```bash
python3 scripts/verify_phase_paths.py
python3 phases/phase_N_id/orchestrator_id.py --show-paths
python3 phases/phases_orchestrator.py --start 1 --end N
```

## Help

```bash
# General help
python3 renumber_phases.py --help

# Operation-specific help
python3 renumber_phases.py insert --help
python3 renumber_phases.py delete --help
python3 renumber_phases.py move --help
```

## Documentation

- Full Guide: `scripts/README_RENUMBER_PHASES.md`
- Design Doc: `docs/PATH_CONFIGURATION_WITH_NUMBERING.md`
- Implementation: `docs/RENUMBER_AUTOMATION_COMPLETE.md`
