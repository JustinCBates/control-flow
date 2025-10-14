# Phase Renumbering Automation Tool

## Overview

The `renumber_phases.py` script automates the mechanical aspects of managing phase sequences when inserting, deleting, or moving phases in a control flow project.

## What It Does

When you reorganize phases, this script handles:

1. **Directory renaming** - Renames `phase_N_id/` directories to maintain sequential numbering
2. **control_flows.yml updates** - Updates `sequence`, `phase_directory`, and `orchestrator_file` fields
3. **Code constant updates** - Updates `PHASE_SEQUENCE` constants in orchestrator files
4. **Validation** - Checks for conflicts and validates operations before execution

## Operations

### Insert a New Phase

Inserts a new phase at a specified position and shifts all subsequent phases forward.

```bash
python3 renumber_phases.py insert --at <position> --name "<Display Name>" --id <phase_id>
```

**Example:**
```bash
# Insert preprocessing phase at position 3
cd /opt/openproject/external/config-manager
python3 ../control-flow/scripts/renumber_phases.py insert \
  --at 3 \
  --name "Preprocessing Phase" \
  --id preprocessing
```

**What happens:**
- Phases 3, 4, 5... are shifted to 4, 5, 6...
- New directory created: `phases/phase_3_preprocessing/`
- Subdirectories created: `outputs/`, `tests/`
- Entry added to `control_flows.yml`
- All orchestrator files updated with new `PHASE_SEQUENCE` values

**Next steps after insertion:**
1. Generate scaffolding: `python3 generator.py scaffold-phase --phase preprocessing`
2. Implement phase logic
3. Test: `python3 phases/phase_3_preprocessing/orchestrator_preprocessing.py --show-paths`

---

### Delete a Phase

Removes a phase and shifts all subsequent phases backward.

```bash
python3 renumber_phases.py delete --at <position>
```

**Example:**
```bash
# Delete phase 3
cd /opt/openproject/external/config-manager
python3 ../control-flow/scripts/renumber_phases.py delete --at 3
```

**What happens:**
- Confirmation prompt (requires typing "yes")
- Phase 3 removed from `control_flows.yml`
- Phases 4, 5, 6... shifted to 3, 4, 5...
- Deleted directory archived to `archived_phases/phase_3_<id>_deleted/`
- All orchestrator files updated with new `PHASE_SEQUENCE` values

**Safety:**
- Requires explicit confirmation (type "yes")
- Archives deleted phase (doesn't permanently delete)
- Can be skipped in dry-run mode

---

### Move a Phase

Moves a phase from one position to another.

```bash
python3 renumber_phases.py move --from <current_position> --to <new_position>
```

**Example:**
```bash
# Move phase 2 to position 4
cd /opt/openproject/external/config-manager
python3 ../control-flow/scripts/renumber_phases.py move --from 2 --to 4
```

**What happens:**
- Source phase moved to temporary location
- Intermediate phases shifted to fill the gap (or make room)
- Source phase moved to final position
- All affected orchestrator files updated with new `PHASE_SEQUENCE` values
- `control_flows.yml` updated with new ordering

**Forward move (e.g., 2→4):**
- Phase 2 → temp
- Phase 3 → 2
- Phase 4 → 3
- temp → 4

**Backward move (e.g., 4→2):**
- Phase 4 → temp
- Phase 3 → 4
- Phase 2 → 3
- temp → 2

---

## Options

### --dry-run

Test what would happen without making actual changes.

```bash
python3 renumber_phases.py --dry-run insert --at 3 --name "Test" --id test
```

**Output:**
- Shows all operations that would be performed
- Labels each action with `[DRY RUN]`
- Does not modify files or directories
- Useful for previewing complex operations

### --project-root

Specify the project root directory (default: current directory).

```bash
python3 renumber_phases.py --project-root /path/to/project insert ...
```

**When to use:**
- Running from a different directory
- Scripting automation
- Testing with different projects

---

## Requirements

### Project Structure

The script expects:

```
project-root/
  design_specs/
    control_flows.yml      # Must exist
  phases/
    phase_1_discovery/
    phase_2_tui_mapping/
    phase_3_collection/
    ...
```

### control_flows.yml Format

The script looks for phases under a flow's `phases` key:

```yaml
flows:
  main_flow:
    phases:
      - phase_id: discovery
        sequence: 1
        implementation:
          phase_directory: phases/phase_1_discovery/
          orchestrator_file: phases/phase_1_discovery/orchestrator_discovery.py
      - phase_id: tui_mapping
        sequence: 2
        ...
```

### Orchestrator File Format

The script updates `PHASE_SEQUENCE` constants in orchestrator files:

```python
# PATH CONFIGURATION
PHASE_SEQUENCE = int(os.getenv('PHASE_SEQUENCE', '3'))
PHASE_ID = 'collection'
```

---

## Error Handling

### Position Out of Range

```
❌ Error: Position 10 is out of range (1-5)
```

**Solution:** Check current phase count and use valid position.

### Directory Already Exists

```
⚠️  Warning: phase_4_preprocessing already exists
```

**Solution:** 
- Check for naming conflicts
- Use different `--id`
- Manually remove conflicting directory

### control_flows.yml Not Found

```
❌ Error: control_flows.yml not found at /path/to/design_specs/control_flows.yml
```

**Solution:**
- Verify project structure
- Use `--project-root` to specify correct path

---

## Workflow Examples

### Example 1: Insert New Phase Between Existing Phases

**Scenario:** Add validation phase between collection (3) and export (4)

```bash
# Dry run first
python3 renumber_phases.py --dry-run insert \
  --at 4 \
  --name "Data Validation" \
  --id validation

# Review output, then execute
python3 renumber_phases.py insert \
  --at 4 \
  --name "Data Validation" \
  --id validation

# Generate scaffolding
python3 generator.py scaffold-phase --phase validation

# Verify paths
python3 scripts/verify_phase_paths.py
```

**Result:**
```
Before:  1:discovery  2:tui_mapping  3:collection  4:export
After:   1:discovery  2:tui_mapping  3:collection  4:validation  5:export
```

### Example 2: Reorganize Phase Order

**Scenario:** Move TUI mapping (2) to after collection (3)

```bash
# Dry run
python3 renumber_phases.py --dry-run move --from 2 --to 3

# Execute
python3 renumber_phases.py move --from 2 --to 3

# Test full pipeline
python3 phases/phases_orchestrator.py --start 1 --end 4
```

**Result:**
```
Before:  1:discovery  2:tui_mapping  3:collection  4:validation
After:   1:discovery  2:collection   3:tui_mapping  4:validation
```

### Example 3: Remove Deprecated Phase

**Scenario:** Remove preprocessing phase (2) that's no longer needed

```bash
# Dry run
python3 renumber_phases.py --dry-run delete --at 2

# Execute (requires confirmation)
python3 renumber_phases.py delete --at 2
# Type: yes

# Verify
python3 phases/phases_orchestrator.py --list-phases
```

**Result:**
```
Before:  1:discovery  2:preprocessing  3:collection  4:validation
After:   1:discovery  2:collection     3:validation

Archived: archived_phases/phase_2_preprocessing_deleted/
```

---

## Integration with Other Tools

### With Path Configuration Pattern

After renumbering, all paths are automatically updated:

```python
# Generated code uses PHASE_SEQUENCE variable
PHASE_SEQUENCE = int(os.getenv('PHASE_SEQUENCE', '3'))  # Updated by script
PHASE_ID = 'collection'  # Stable identifier

# PathResolver validates against control_flows.yml
resolver = PathResolver.from_execution_context(__file__)
output_dir = resolver.resolve_phase_output_dir(PHASE_ID)
```

### With --show-paths Flag

Verify path configuration after renumbering:

```bash
python3 phases/phase_3_collection/orchestrator_collection.py --show-paths
```

**Output:**
```
📍 Path Configuration:
   PHASE_SEQUENCE: 3
   PHASE_ID: collection
   PROJECT_ROOT: /opt/openproject/external/config-manager
   PHASE_DIR: phases/phase_3_collection
   OUTPUT_DIR: phases/phase_3_collection/outputs
   
✅ PathResolver validation: PASSED
```

### With Generator

After inserting a new phase, use the generator:

```bash
# Insert phase
python3 renumber_phases.py insert --at 3 --name "Preprocessing" --id preprocessing

# Generate scaffolding
python3 generator.py scaffold-phase --phase preprocessing

# Generates:
#   - orchestrator_preprocessing.py (with correct PHASE_SEQUENCE=3)
#   - step_1_preprocess/preprocess.py
#   - tests/test_preprocessing.py
```

---

## Best Practices

### 1. Always Dry Run First

```bash
# Preview changes
python3 renumber_phases.py --dry-run insert --at 3 --name "Test" --id test

# Review output carefully

# Execute if everything looks correct
python3 renumber_phases.py insert --at 3 --name "Test" --id test
```

### 2. Use Version Control

```bash
# Commit before making changes
git add -A
git commit -m "Before renumbering: current phase state"

# Run renumber operation
python3 renumber_phases.py move --from 2 --to 4

# Review changes
git diff

# Commit if successful, revert if not
git commit -m "Moved tui_mapping phase from 2 to 4"
# OR
git reset --hard HEAD  # if something went wrong
```

### 3. Verify After Operations

```bash
# After any renumber operation
python3 scripts/verify_phase_paths.py

# Test affected phases
python3 phases/phase_3_collection/orchestrator_collection.py --show-paths

# Run full pipeline
python3 phases/phases_orchestrator.py --start 1 --end 5
```

### 4. Use Descriptive Phase IDs

```bash
# Good
--id preprocessing
--id data_validation
--id schema_export

# Avoid
--id phase3
--id new_phase
--id temp
```

### 5. Keep Archived Phases

The script archives deleted phases to `archived_phases/`. Don't delete these immediately:

- Useful for reference
- Can be restored if needed
- Contains working code that might be reused

Clean up old archives periodically (e.g., after major releases).

---

## Troubleshooting

### Operation Fails Mid-Execution

**Symptoms:** Script crashes partway through, phases in inconsistent state

**Solution:**
```bash
# If using git
git reset --hard HEAD

# If not using git
# Manually restore from backup or re-run operation
python3 renumber_phases.py <operation> ...
```

### PHASE_SEQUENCE Not Updated in Orchestrator

**Symptoms:** Directory renamed but code still has old sequence number

**Solution:**
```bash
# Check orchestrator file format
cat phases/phase_3_collection/orchestrator_collection.py | grep PHASE_SEQUENCE

# Should match pattern:
# PHASE_SEQUENCE = int(os.getenv('PHASE_SEQUENCE', '3'))

# If not, manually update or regenerate
python3 generator.py scaffold-phase --phase collection
```

### control_flows.yml Malformed After Operation

**Symptoms:** YAML syntax errors or missing fields

**Solution:**
```bash
# Validate YAML
python3 -c "import yaml; yaml.safe_load(open('design_specs/control_flows.yml'))"

# If errors, restore from git
git checkout design_specs/control_flows.yml

# Re-run operation
python3 renumber_phases.py <operation> ...
```

---

## Limitations

1. **Single Flow Support:** Currently supports projects with one main flow. Multi-flow projects require manual updates.

2. **Orchestrator Pattern Required:** Assumes orchestrator files follow naming convention: `orchestrator_{phase_id}.py`

3. **No Step Renumbering:** Only handles phase-level renumbering. Step sequences within phases are not affected.

4. **Manual Generator Run:** After insertion, you must manually run the generator to create phase scaffolding.

---

## Future Enhancements

- [ ] Multi-flow project support
- [ ] Automatic generator invocation after insertion
- [ ] Step-level renumbering within phases
- [ ] Batch operations (insert multiple phases)
- [ ] Undo/rollback functionality
- [ ] Interactive mode with phase selection menu
- [ ] Automatic backup creation before operations
- [ ] Integration with CI/CD workflows

---

## Support

For issues or questions:
1. Check this README
2. Review examples in `control-flow/docs/PATH_CONFIGURATION_WITH_NUMBERING.md`
3. Run with `--dry-run` to preview changes
4. Check git history for recent changes
5. Contact the development team

---

## Related Documentation

- [Path Configuration Pattern](../docs/PATH_CONFIGURATION_WITH_NUMBERING.md)
- [Path Resolver Implementation](../docs/PATH_RESOLVER_IMPLEMENTATION_COMPLETE.md)
- [Control Flow Generator](../docs/GENERATOR_USAGE.md)
