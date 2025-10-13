# Control Flow Management System

This directory contains all control flow related files for the config-manager component.

## Files

### Documentation
- **`CONTROL_FLOWS.md`** - Current control flow documentation (generated/maintained)
- **`CONTROL_FLOWS_SPEC.md`** - Design-first specification (YAML-based, AI-friendly)

### Tools
- **`analyze_control_flows.py`** - Analyzer and validator for control flows
- **`control_flow_manager.py`** - Design-first flow manager with AI communication
- **`smart_flow_updater.py`** - Smart updater that preserves manual changes
- **`demo_development_communication.py`** - Demo of development workflow

## Usage

### For Development
```bash
# Analyze current flows
cd control_flows
python analyze_control_flows.py

# Apply planned changes
python control_flow_manager.py

# Smart update with preservation
python smart_flow_updater.py

# See development workflow demo
python demo_development_communication.py
```

### For AI Communication
Edit `CONTROL_FLOWS_SPEC.md` and use natural language like:
- "Insert security validation after input validation"
- "Add error recovery before export"
- "Move final review to be after validation"

## Design-First Workflow
1. Update `CONTROL_FLOWS_SPEC.md` with planned changes
2. Run `control_flow_manager.py` to apply changes
3. Generate mock implementations and tests
4. Implement actual functionality
5. Update status to IMPLEMENTED

## System Benefits
- 🎯 **Design-first**: Spec flows before implementing
- 📝 **AI Communication**: Natural language → precise changes
- 🔄 **Iterative**: Support for gradual implementation
- 📊 **Status Tracking**: Clear implementation status
- 🛡️ **Smart Updates**: Preserve manual changes during updates

---

*Note: This documentation has been consolidated into the unified control-flow engine package.*