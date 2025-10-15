# Documentation Index

Complete index of all active documentation for the Control Flow Engine and Transformation System.

## 📚 Active Documentation (6 files)

### Core Documents

| Document | Description | Audience | Lines |
|----------|-------------|----------|-------|
| **[README.md](../README.md)** | Project overview, features, quick start | Everyone | ~200 |
| **[TRANSFORMATION_SYSTEM.md](TRANSFORMATION_SYSTEM.md)** | Complete transformation API reference | Developers | 1,050 |
| [TRANSFORMATION_QUICK_REFERENCE.md](TRANSFORMATION_QUICK_REFERENCE.md) | Quick commands and patterns | Developers | 300 |
| [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) | Executive summary and metrics | Managers/Architects | 450 |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | Development guidelines | Contributors | TBD |
| [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) | This index | Everyone | 250 |

### Additional Documentation (in this directory)

| Document | Description |
|----------|-------------|
| [ARCHITECTURE_OUTPUT_DIRECTORIES.md](ARCHITECTURE_OUTPUT_DIRECTORIES.md) | **NEW**: Runtime output directory structure |
| [architecture.md](architecture.md) | System architecture overview |
| [visualization_guide.md](visualization_guide.md) | How to generate diagrams |
| [visualizer_usage.md](visualizer_usage.md) | Visualizer API and examples |
| [RUNNABLE_CODE_PATTERN.md](RUNNABLE_CODE_PATTERN.md) | Design principles |
| [RUNNABLE_PATTERN_COMPLETE.md](RUNNABLE_PATTERN_COMPLETE.md) | Implementation guide |
| [PHASE2_IMPLEMENTATION_COMPLETE.md](PHASE2_IMPLEMENTATION_COMPLETE.md) | Greenfield workflow |

## 🗄️ Archived Documentation

All historical completion documents and analysis files have been moved to `archive/old_completion_docs/`:
- All TODO_X_COMPLETE.md files (consolidated into TRANSFORMATION_SYSTEM.md)
- All feature-specific completion docs (ROLLBACK_COMPLETE.md, etc.)
- All analysis documents (TODO_6_ANALYSIS.md, SCAFFOLDER_SCOPE_CREEP_ANALYSIS.md, etc.)
- All old refactoring docs (PHASE_1_*.md, etc.)
- All scaffolding examples and specs

**Rationale**: All information consolidated into TRANSFORMATION_SYSTEM.md for single source of truth.

## Examples

### Code Examples

| File | Description | Lines |
|------|-------------|-------|
| [examples/transformation_example.py](examples/transformation_example.py) | Basic transformation operations | ~400 |
| [examples/directory_sync_example.py](examples/directory_sync_example.py) | Directory synchronization | ~350 |
| [examples/transformation_history_example.py](examples/transformation_history_example.py) | History tracking | ~300 |
| [examples/rollback_example.py](examples/rollback_example.py) | Rollback operations | ~420 |
| [examples/scaffold_transformer_example.py](examples/scaffold_transformer_example.py) | Zero-point creation | ~540 |
| [examples/transformation_with_regeneration_example.py](examples/transformation_with_regeneration_example.py) | Integrated workflow | ~460 |

## Implementation Files

### Core System

| File | Description | Lines |
|------|-------------|-------|
| [src/control_flow_engine/core/transformation.py](src/control_flow_engine/core/transformation.py) | Main transformation system | ~2,600 |
| [src/control_flow_engine/core/transformation_regenerator_bridge.py](src/control_flow_engine/core/transformation_regenerator_bridge.py) | Orchestrator integration | ~260 |

## Quick Navigation

### By Use Case

**I want to...**

- **Get started quickly** → [README.md](README.md)
- **Learn the complete transformation API** → [TRANSFORMATION_SYSTEM.md](TRANSFORMATION_SYSTEM.md)
- **Find a quick command** → [TRANSFORMATION_QUICK_REFERENCE.md](TRANSFORMATION_QUICK_REFERENCE.md)
- **See implementation metrics** → [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
- **See code examples** → [examples/](examples/)
- **Understand architecture** → [docs/architecture.md](docs/architecture.md)
- **Generate diagrams** → [docs/visualization_guide.md](docs/visualization_guide.md)
- **Contribute** → [CONTRIBUTING.md](CONTRIBUTING.md)

### By Audience

**Developers**
1. [README.md](README.md) - Quick start
2. [TRANSFORMATION_SYSTEM.md](TRANSFORMATION_SYSTEM.md) - Complete API reference
3. [TRANSFORMATION_QUICK_REFERENCE.md](TRANSFORMATION_QUICK_REFERENCE.md) - Common patterns
4. [examples/](examples/) - Code examples

**Architects**
1. [TRANSFORMATION_SYSTEM.md#architecture](TRANSFORMATION_SYSTEM.md#architecture) - System design
2. [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Metrics and decisions
3. [docs/architecture.md](docs/architecture.md) - Overall architecture
4. [docs/RUNNABLE_CODE_PATTERN.md](docs/RUNNABLE_CODE_PATTERN.md) - Design patterns

**Project Managers**
1. [README.md](README.md) - Feature overview
2. [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Status and metrics
3. [TRANSFORMATION_SYSTEM.md#overview](TRANSFORMATION_SYSTEM.md#overview) - Benefits

**QA/Testing**
1. [examples/](examples/) - Test scenarios
2. [TRANSFORMATION_SYSTEM.md#troubleshooting](TRANSFORMATION_SYSTEM.md#troubleshooting) - Known issues
3. [TRANSFORMATION_QUICK_REFERENCE.md](TRANSFORMATION_QUICK_REFERENCE.md) - Test patterns

## Documentation Statistics

### Active Documentation
- **Core Docs**: 6 markdown files (~2,250 lines)
- **Subdirectory Docs**: ~6 additional files in docs/
- **Examples**: ~2,470 lines of code
- **Implementation**: ~2,860 lines
- **Total Active**: ~7,580 lines

### Archived Documentation
- **Completion Docs**: 10+ files moved to archive/
- **Analysis Docs**: Multiple files consolidated
- **Old Specs**: Historical documents preserved
- **Total Archived**: ~190,000+ lines

### Coverage
- ✅ All features documented in TRANSFORMATION_SYSTEM.md
- ✅ All APIs documented
- ✅ All examples provided
- ✅ Quick reference for common tasks
- ✅ Troubleshooting guide
- ✅ Integration patterns
- ✅ Best practices
- ✅ Single source of truth established

## Contributing

When adding new documentation:

1. **Update this index** with clear description
2. **Link from README** if user-facing
3. **Cross-reference** related docs
4. **Keep focused** - avoid duplication
5. **Archive old docs** rather than delete

## Recent Updates

| Date | Change | Rationale |
|------|--------|-----------|
| 2025-10-15 | Moved 10+ completion docs to archive/ | Consolidated into TRANSFORMATION_SYSTEM.md |
| 2025-10-15 | Created TRANSFORMATION_SYSTEM.md | Single source of truth |
| 2025-10-15 | Created TRANSFORMATION_QUICK_REFERENCE.md | Developer productivity |
| 2025-10-15 | Created IMPLEMENTATION_SUMMARY.md | Executive overview |
| 2025-10-15 | Reorganized DOCUMENTATION_INDEX.md | Clearer structure |

---

**Last Updated**: October 15, 2025  
**Maintained By**: Control Flow Engine Team
