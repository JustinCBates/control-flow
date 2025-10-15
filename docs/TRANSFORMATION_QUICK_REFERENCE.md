# Transformation System - Quick Reference

**Quick commands and patterns for common transformation tasks**

## Common Operations

### Renumber a Step

```python
from control_flow_engine.core.transformation import ControlFlowTransformation

transformer = ControlFlowTransformation("specs/my_phase.yaml")
plan = transformer.plan_renumber(10, 15, 'step')
transformer.apply(plan, save=True)
```

### Insert a New Step

```python
new_step = {
    'step_id': 'validate',
    'name': 'Validate Input',
    'sequence': 25,
    'description': 'Validate inputs',
    'action': 'validate'
}

plan = transformer.plan_insert(new_step, 'step', cascade_renumber=True)
transformer.apply(plan, save=True, sync_directories=True, regenerate_orchestrators=True)
```

### Delete a Step

```python
plan = transformer.plan_delete(30, 'step', cascade_renumber=True)
transformer.apply(plan, save=True, sync_directories=True)
```

### Create New Phase from Scratch

```python
from control_flow_engine.core.transformation import scaffold_transformer

result = scaffold_transformer(
    spec_file=Path("specs/new_phase.yaml"),
    phase_data={
        'phase_id': 'deployment',
        'name': 'Deployment Phase',
        'sequence': 90,
        'initial_steps': [...]
    },
    create_directories=True
)
```

### Rollback Last Change

```python
transformer.rollback(steps=1, save=True, sync_directories=True)
```

### Full Workflow (Production)

```python
# Plan transformation
plan = transformer.plan_insert(new_element, 'step', cascade_renumber=True)

# Validate
validation = transformer.validate(plan)
if not validation.valid:
    print(f"Errors: {validation.errors}")
    exit(1)

# Preview
print(transformer.preview(plan))

# Apply with all features
transformer.apply(
    plan,
    save=True,
    sync_directories=True,
    update_code_paths=True,
    regenerate_orchestrators=True,
    project_base_path=Path(".")
)
```

## Command Patterns

| Task | Command |
|------|---------|
| Renumber without cascade | `plan_renumber(old, new, type, cascade_renumber=False)` |
| Renumber with cascade | `plan_renumber(old, new, type, cascade_renumber=True)` |
| Insert at end | `plan_insert(elem, type, cascade_renumber=False)` |
| Insert in middle | `plan_insert(elem, type, cascade_renumber=True)` |
| Delete at end | `plan_delete(seq, type, cascade_renumber=False)` |
| Delete in middle | `plan_delete(seq, type, cascade_renumber=True)` |
| Preview only | `preview(plan)` |
| Validate only | `validate(plan)` |
| Apply YAML only | `apply(plan, save=True)` |
| Apply + sync dirs | `apply(plan, save=True, sync_directories=True)` |
| Apply + full workflow | `apply(plan, save=True, sync_directories=True, update_code_paths=True, regenerate_orchestrators=True)` |

## apply() Parameters Quick Reference

```python
transformer.apply(
    plan,                           # Required: TransformationPlan
    save=True,                      # Save YAML changes
    sync_directories=True,          # Sync directory structure
    project_base_path=Path("."),   # Project root directory
    update_code_paths=True,         # Update Python imports
    regenerate_orchestrators=True,  # Regenerate orchestrator code
    flow_name="main_config_flow"   # Flow name for regeneration
)
```

## Validation Checks

```python
validation = transformer.validate(plan)

# Check if valid
if validation.valid:
    transformer.apply(plan)
else:
    # Print errors
    for error in validation.errors:
        print(f"ERROR: {error}")
    
    # Print warnings
    for warning in validation.warnings:
        print(f"WARNING: {warning}")
```

## History Operations

```python
# Get history
history = transformer.get_history(limit=10)

# Check rollback availability
if transformer.history_manager.can_rollback(1):
    transformer.rollback(steps=1)

# Get last N transformations
last_5 = transformer.get_history(limit=5)
for entry in last_5:
    print(f"{entry['timestamp']}: {entry['transformation_type']}")
```

## Error Handling

```python
try:
    plan = transformer.plan_renumber(10, 15, 'step')
    validation = transformer.validate(plan)
    
    if not validation.valid:
        raise ValueError(f"Validation failed: {validation.errors}")
    
    transformer.apply(plan, save=True)
    
except ValueError as e:
    print(f"Validation error: {e}")
except FileNotFoundError as e:
    print(f"File not found: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
    # Rollback if needed
    transformer.rollback(steps=1, save=True)
```

## Batch Operations

```python
# Multiple transformations
operations = [
    ('renumber', 10, 12, 'step'),
    ('renumber', 20, 22, 'step'),
    ('renumber', 30, 32, 'step')
]

for op_type, old_seq, new_seq, target_type in operations:
    plan = transformer.plan_renumber(old_seq, new_seq, target_type)
    if transformer.validate(plan).valid:
        transformer.apply(plan, save=True)

# Regenerate once at the end
transformer.apply(
    plan,
    regenerate_orchestrators=True,
    project_base_path=Path(".")
)
```

## scaffold_transformer Return Values

```python
result = scaffold_transformer(...)

# Access created files/directories
spec_file = result['spec_file']        # Path to YAML spec
created = result['created']             # 'phase' or 'step'
phase_dir = result.get('phase_dir')    # Phase directory (if created)
step_dir = result.get('step_dir')      # Step directory (if created)
history = result.get('history_file')   # History file (if initialized)
transformer = result['transformer']     # Transformer instance
```

## Best Practice Checklist

- [ ] Always validate before apply
- [ ] Use preview for complex transformations
- [ ] Enable sync_directories for production
- [ ] Enable update_code_paths after directory sync
- [ ] Enable regenerate_orchestrators after YAML changes
- [ ] Use cascade_renumber when inserting in middle
- [ ] Test with dry run first
- [ ] Backup specs before major changes
- [ ] Check history before rollback
- [ ] Handle validation errors properly

## Common Mistakes to Avoid

❌ **DON'T**: Apply without validation
```python
# BAD
plan = transformer.plan_renumber(10, 15, 'step')
transformer.apply(plan)  # May fail
```

✅ **DO**: Validate first
```python
# GOOD
plan = transformer.plan_renumber(10, 15, 'step')
if transformer.validate(plan).valid:
    transformer.apply(plan)
```

❌ **DON'T**: Forget cascade_renumber when inserting
```python
# BAD - Creates duplicate sequences
plan = transformer.plan_insert(new_step, 'step')
```

✅ **DO**: Use cascade_renumber
```python
# GOOD
plan = transformer.plan_insert(new_step, 'step', cascade_renumber=True)
```

❌ **DON'T**: Forget to sync after YAML changes
```python
# BAD - YAML and directories out of sync
transformer.apply(plan, save=True)
```

✅ **DO**: Sync everything
```python
# GOOD
transformer.apply(
    plan,
    save=True,
    sync_directories=True,
    update_code_paths=True,
    regenerate_orchestrators=True
)
```

## Troubleshooting Quick Fixes

| Problem | Quick Fix |
|---------|-----------|
| Validation fails | Check `validation.errors` |
| Directories not synced | Set `sync_directories=True` |
| Imports broken | Set `update_code_paths=True` |
| Orchestrators outdated | Set `regenerate_orchestrators=True` |
| Can't rollback | Check `can_rollback()` first |
| History empty | Apply at least one transformation |

## See Also

- [Complete Documentation](TRANSFORMATION_SYSTEM.md)
- [Examples](examples/)
- [API Reference](TRANSFORMATION_SYSTEM.md#api-reference)

---

**Quick Reference Version**: 1.0  
**Last Updated**: October 15, 2025
