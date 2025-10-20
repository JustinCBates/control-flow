#!/usr/bin/env python3
"""
Interactive Terminal UI for Control Flow Editing.

This module provides a menu-driven interface for editing control flow
specifications using the ControlFlowDesigner transformation API.

Features:
- Browse phases and steps visually
- Renumber, insert, and delete operations
- Preview changes before applying
- View transformation history and rollback
- User-friendly error handling
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

try:
    import questionary
    from questionary import Style
except ImportError:
    print("Error: questionary not installed. Run: pip install questionary")
    sys.exit(1)

from control_flow_engine.core.designer import ControlFlowDesigner
from control_flow_engine.core.engine import ControlFlowManager


# Custom style for the TUI
custom_style = Style([
    ('qmark', 'fg:#673ab7 bold'),       # Question mark
    ('question', 'bold'),                # Question text
    ('answer', 'fg:#f44336 bold'),      # User's answer
    ('pointer', 'fg:#673ab7 bold'),     # Pointer in selections
    ('highlighted', 'fg:#673ab7 bold'), # Highlighted choice
    ('selected', 'fg:#cc5454'),         # Selected choice
    ('separator', 'fg:#cc5454'),        # Separator
    ('instruction', ''),                 # Instructions
    ('text', ''),                        # Plain text
    ('disabled', 'fg:#858585 italic')   # Disabled choices
])


@dataclass
class FlowElement:
    """Represents a phase or step in the flow."""
    element_type: str  # 'phase' or 'step'
    element_id: str
    name: str
    sequence: int
    parent_id: Optional[str] = None  # For steps, the parent phase_id
    

class ControlFlowEditor:
    """Interactive terminal UI for editing control flows."""
    
    def __init__(self, project_root: str):
        """
        Initialize the flow editor.
        
        Args:
            project_root: Path to the project root directory
        """
        self.project_root = Path(project_root)
        
        # Look for control_flows.yml in common locations
        possible_spec_locations = [
            self.project_root / "design_specs" / "control_flows.yml",
            self.project_root / "specs" / "control_flows.yml",
            self.project_root / "control_flows.yml",
            self.project_root / "design_specs" / "control_flows.yaml",
            self.project_root / "specs" / "control_flows.yaml",
            self.project_root / "control_flows.yaml",
        ]
        
        self.spec_file = None
        for spec_path in possible_spec_locations:
            if spec_path.exists():
                self.spec_file = spec_path
                print(f"✅ Found spec file: {spec_path}")
                break
        
        if not self.spec_file:
            print(f"❌ Error: Could not find control_flows.yml in:")
            for loc in possible_spec_locations[:3]:
                print(f"   - {loc}")
            print(f"\nPlease create a control_flows.yml file in one of these locations.")
            sys.exit(1)
        
        self.designer = ControlFlowDesigner(spec_file=self.spec_file, project_root=self.project_root)
        self.manager = ControlFlowManager(spec_file=self.spec_file)
        
        # Load the specification
        try:
            self.manager.load_specification()
        except Exception as e:
            print(f"❌ Error loading specification: {e}")
            sys.exit(1)
        
    def run(self):
        """Run the interactive editor."""
        self._print_header()
        
        while True:
            try:
                action = self._main_menu()
                
                if action == 'quit':
                    self._print_goodbye()
                    break
                elif action == 'browse':
                    self._browse_flow()
                elif action == 'renumber':
                    self._renumber_menu()
                elif action == 'insert':
                    self._insert_menu()
                elif action == 'move':
                    self._move_menu()
                elif action == 'delete':
                    self._delete_menu()
                elif action == 'history':
                    self._view_history()
                elif action == 'rollback':
                    self._rollback_menu()
                    
            except KeyboardInterrupt:
                print("\n\n⚠️  Operation cancelled by user.")
                input("\nPress Enter to continue...")
                continue
            except Exception as e:
                # Clear any questionary UI artifacts
                print("\n" + "=" * 70)
                print("❌ ERROR OCCURRED")
                print("=" * 70)
                print(f"Error: {str(e)}")
                print(f"Type: {type(e).__name__}")
                
                # Print traceback for debugging
                import traceback
                print("\nTraceback:")
                traceback.print_exc()
                
                print("\n" + "=" * 70)
                input("\nPress Enter to return to main menu...")
                
                # Re-print header to clean up terminal
                self._print_header()
                continue
    
    def _print_header(self):
        """Print the application header."""
        print("\n" + "=" * 70)
        print("  Control Flow Editor - Interactive Transformation Tool")
        print("=" * 70)
        print(f"  Project: {self.project_root.name}")
        print(f"  Spec File: {self.spec_file.name}")
        print("=" * 70 + "\n")
    
    def _print_goodbye(self):
        """Print goodbye message."""
        print("\n" + "=" * 70)
        print("  Thank you for using Control Flow Editor!")
        print("=" * 70 + "\n")
    
    def _main_menu(self) -> str:
        """
        Show the main menu and get user selection.
        
        Returns:
            Selected action
        """
        choices = [
            {'name': '📋 Browse Flow Structure', 'value': 'browse'},
            {'name': '🔢 Renumber Sequences', 'value': 'renumber'},
            {'name': '➕ Insert Phase/Step', 'value': 'insert'},
            {'name': '� Move/Reorder/Swap', 'value': 'move'},
            {'name': '�🗑️  Delete Phase/Step', 'value': 'delete'},
            {'name': '📜 View History', 'value': 'history'},
            {'name': '↩️  Rollback Changes', 'value': 'rollback'},
            questionary.Separator(),
            {'name': '🚪 Exit', 'value': 'quit'}
        ]
        
        return questionary.select(
            "What would you like to do?",
            choices=choices,
            style=custom_style
        ).ask()
    
    def _browse_flow(self):
        """Display the flow structure."""
        try:
            print("\n" + "=" * 70)
            print("  Current Flow Structure")
            print("=" * 70 + "\n")
            
            spec = self.manager.get_specification()
            
            # Check if we have phases directly in spec or under flows
            phases_dict = spec.get('phases', {})
            
            if not phases_dict:
                # Try alternate structure: flows -> phases
                flows = spec.get('flows', {})
                if flows:
                    # Get first flow or main flow
                    flow_name = 'main_deployment_flow' if 'main_deployment_flow' in flows else list(flows.keys())[0]
                    phases_dict = flows.get(flow_name, {}).get('phases', {})
            
            if not phases_dict:
                print("⚠️  No phases found in specification.")
                input("\nPress Enter to continue...")
                return
            
            # Convert dict to list and sort by sequence
            phases_list = []
            for phase_id, phase_data in phases_dict.items():
                phase_info = {
                    'phase_id': phase_id,
                    'sequence': phase_data.get('sequence', 0),
                    'name': phase_data.get('name', 'Unnamed Phase'),
                    'description': phase_data.get('description', ''),
                    'steps': phase_data.get('steps', []),
                    'status': phase_data.get('status', 'unknown')
                }
                phases_list.append(phase_info)
            
            sorted_phases = sorted(phases_list, key=lambda p: p['sequence'])
            
            for phase in sorted_phases:
                phase_seq = phase['sequence']
                phase_id = phase['phase_id']
                phase_name = phase['name']
                phase_status = phase['status']
                
                print(f"[{phase_seq}] {phase_name}")
                print(f"    ID: {phase_id}")
                print(f"    Status: {phase_status}")
                print(f"    Description: {phase['description']}")
                
                # Show steps if any
                steps = phase['steps']
                if steps:
                    sorted_steps = sorted(steps, key=lambda s: s.get('sequence', 0))
                    for step in sorted_steps:
                        step_seq = step.get('sequence', '?')
                        step_name = step.get('name', 'Unnamed Step')
                        step_status = step.get('status', 'unknown')
                        print(f"      [{step_seq}] {step_name} ({step_status})")
                        
                        # Show units if any
                        units = step.get('units', [])
                        if units:
                            print(f"          Units: {', '.join(units)}")
                else:
                    print("      (no steps)")
                print()
            
            input("\nPress Enter to continue...")
            
        except Exception as e:
            print(f"\n❌ Error displaying flow structure: {e}")
            import traceback
            traceback.print_exc()
            input("\nPress Enter to continue...")

    
    def _renumber_menu(self):
        """Renumber phases or steps."""
        print("\n" + "=" * 70)
        print("  Renumber Sequences")
        print("=" * 70 + "\n")
        
        # Get phases for selection
        spec = self.manager.get_specification()
        flow = spec.get('flows', {}).get(self.manager.flow_name, {})
        phases = flow.get('phases', [])
        
        if not phases:
            print("⚠️  No phases found.")
            return
        
        # Ask what to renumber
        scope_choices = [
            {'name': 'All phases', 'value': 'all_phases'},
            {'name': 'Steps within a specific phase', 'value': 'phase_steps'}
        ]
        
        scope = questionary.select(
            "What would you like to renumber?",
            choices=scope_choices,
            style=custom_style
        ).ask()
        
        phase_id = None
        
        if scope == 'phase_steps':
            # Select which phase
            phase_choices = [
                {
                    'name': f"[{p.get('sequence', '?')}] {p.get('name', 'Unnamed')} (ID: {p.get('phase_id')})",
                    'value': p.get('phase_id')
                }
                for p in sorted(phases, key=lambda p: p.get('sequence', 0))
            ]
            
            phase_id = questionary.select(
                "Select phase:",
                choices=phase_choices,
                style=custom_style
            ).ask()
        
        # Ask for starting number
        start_from = questionary.text(
            "Starting sequence number:",
            default="1",
            validate=lambda x: x.isdigit() or "Must be a number"
        ).ask()
        
        start_from = int(start_from)
        
        # Ask for strategy
        strategy = questionary.select(
            "Renumbering strategy:",
            choices=[
                {'name': 'Compact (remove all gaps)', 'value': 'compact'},
                {'name': 'Minimal (preserve relative spacing)', 'value': 'minimal'}
            ],
            style=custom_style,
            default='compact'
        ).ask()
        
        # Preview first
        print("\n⏳ Generating preview...")
        result = self.designer.renumber_phase(
            phase_id=phase_id,
            start_from=start_from,
            strategy=strategy,
            preview_only=True
        )
        
        if not result['success']:
            print(f"\n❌ Error: {result['message']}")
            if 'errors' in result:
                for error in result['errors']:
                    print(f"   - {error}")
            return
        
        print("\n" + "-" * 70)
        print("  Preview:")
        print("-" * 70)
        print(result.get('preview', 'No preview available'))
        print("-" * 70)
        
        # Ask to apply
        if questionary.confirm(
            "Apply this renumbering?",
            default=False,
            style=custom_style
        ).ask():
            print("\n⏳ Applying changes...")
            result = self.designer.renumber_phase(
                phase_id=phase_id,
                start_from=start_from,
                strategy=strategy,
                preview_only=False
            )
            
            if result['success']:
                print(f"\n✅ {result['message']}")
                if 'warnings' in result and result['warnings']:
                    print("\n⚠️  Warnings:")
                    for warning in result['warnings']:
                        print(f"   - {warning}")
            else:
                print(f"\n❌ Error: {result['message']}")
        else:
            print("\n❌ Cancelled.")
        
        input("\nPress Enter to continue...")
    
    def _insert_menu(self):
        """Insert a new phase or step."""
        print("\n" + "=" * 70)
        print("  Insert Phase or Step")
        print("=" * 70 + "\n")
        
        # Ask what to insert
        insert_type = questionary.select(
            "What would you like to insert?",
            choices=[
                {'name': 'Phase', 'value': 'phase'},
                {'name': 'Step', 'value': 'step'}
            ],
            style=custom_style
        ).ask()
        
        if insert_type == 'phase':
            self._insert_phase()
        else:
            self._insert_step()
    
    def _insert_phase(self):
        """Insert a new phase."""
        # Get basic info
        phase_id = questionary.text(
            "Phase ID (e.g., 'deployment'):",
            validate=lambda x: len(x) > 0 or "ID cannot be empty"
        ).ask()
        
        name = questionary.text(
            "Phase Name:",
            validate=lambda x: len(x) > 0 or "Name cannot be empty"
        ).ask()
        
        description = questionary.text(
            "Description (optional):",
            default=""
        ).ask()
        
        # Get position
        spec = self.manager.get_specification()
        flow = spec.get('flows', {}).get(self.manager.flow_name, {})
        phases = flow.get('phases', [])
        
        position_choices = [{'name': 'At end', 'value': 'end'}]
        
        if phases:
            sorted_phases = sorted(phases, key=lambda p: p.get('sequence', 0))
            for phase in sorted_phases:
                phase_name = phase.get('name', 'Unnamed')
                pid = phase.get('phase_id')
                position_choices.append({
                    'name': f"After '{phase_name}'",
                    'value': f"after:{pid}"
                })
                position_choices.append({
                    'name': f"Before '{phase_name}'",
                    'value': f"before:{pid}"
                })
        
        position = questionary.select(
            "Position:",
            choices=position_choices,
            style=custom_style
        ).ask()
        
        # Parse position
        insert_after = None
        insert_before = None
        
        if position.startswith('after:'):
            insert_after = position.split(':', 1)[1]
        elif position.startswith('before:'):
            insert_before = position.split(':', 1)[1]
        
        # Cascade renumber?
        cascade = questionary.confirm(
            "Cascade renumber subsequent phases?",
            default=True,
            style=custom_style
        ).ask()
        
        # Build phase data
        phase_data = {
            'phase_id': phase_id,
            'name': name
        }
        if description:
            phase_data['description'] = description
        
        # Preview
        print("\n⏳ Generating preview...")
        result = self.designer.insert_phase(
            phase_data=phase_data,
            insert_after=insert_after,
            insert_before=insert_before,
            cascade_renumber=cascade,
            preview_only=True
        )
        
        if not result['success']:
            print(f"\n❌ Error: {result['message']}")
            return
        
        print("\n" + "-" * 70)
        print("  Preview:")
        print("-" * 70)
        print(result.get('preview', 'No preview available'))
        print("-" * 70)
        
        # Apply?
        if questionary.confirm(
            "Insert this phase?",
            default=False,
            style=custom_style
        ).ask():
            print("\n⏳ Inserting phase...")
            result = self.designer.insert_phase(
                phase_data=phase_data,
                insert_after=insert_after,
                insert_before=insert_before,
                cascade_renumber=cascade,
                preview_only=False
            )
            
            if result['success']:
                print(f"\n✅ {result['message']}")
            else:
                print(f"\n❌ Error: {result['message']}")
        else:
            print("\n❌ Cancelled.")
        
        input("\nPress Enter to continue...")
    
    def _insert_step(self):
        """Insert a new step."""
        # Select phase
        spec = self.manager.get_specification()
        flow = spec.get('flows', {}).get(self.manager.flow_name, {})
        phases = flow.get('phases', [])
        
        if not phases:
            print("⚠️  No phases found. Create a phase first.")
            return
        
        phase_choices = [
            {
                'name': f"[{p.get('sequence', '?')}] {p.get('name', 'Unnamed')} (ID: {p.get('phase_id')})",
                'value': p.get('phase_id')
            }
            for p in sorted(phases, key=lambda p: p.get('sequence', 0))
        ]
        
        phase_id = questionary.select(
            "Select phase to insert step into:",
            choices=phase_choices,
            style=custom_style
        ).ask()
        
        # Get step info
        step_id = questionary.text(
            "Step ID (e.g., 'code_review'):",
            validate=lambda x: len(x) > 0 or "ID cannot be empty"
        ).ask()
        
        name = questionary.text(
            "Step Name:",
            validate=lambda x: len(x) > 0 or "Name cannot be empty"
        ).ask()
        
        description = questionary.text(
            "Description (optional):",
            default=""
        ).ask()
        
        # Get position within phase
        target_phase = next((p for p in phases if p.get('phase_id') == phase_id), None)
        steps = target_phase.get('steps', []) if target_phase else []
        
        position_choices = [{'name': 'At end', 'value': 'end'}]
        
        if steps:
            sorted_steps = sorted(steps, key=lambda s: s.get('sequence', 0))
            for step in sorted_steps:
                step_name = step.get('name', 'Unnamed')
                sid = step.get('step_id')
                position_choices.append({
                    'name': f"After '{step_name}'",
                    'value': f"after:{sid}"
                })
                position_choices.append({
                    'name': f"Before '{step_name}'",
                    'value': f"before:{sid}"
                })
        
        position = questionary.select(
            "Position:",
            choices=position_choices,
            style=custom_style
        ).ask()
        
        # Parse position
        insert_after = None
        insert_before = None
        
        if position.startswith('after:'):
            insert_after = position.split(':', 1)[1]
        elif position.startswith('before:'):
            insert_before = position.split(':', 1)[1]
        
        # Cascade renumber?
        cascade = questionary.confirm(
            "Cascade renumber subsequent steps?",
            default=True,
            style=custom_style
        ).ask()
        
        # Build step data
        step_data = {
            'step_id': step_id,
            'name': name
        }
        if description:
            step_data['description'] = description
        
        # Preview
        print("\n⏳ Generating preview...")
        result = self.designer.insert_step(
            phase_id=phase_id,
            step_data=step_data,
            insert_after=insert_after,
            insert_before=insert_before,
            cascade_renumber=cascade,
            preview_only=True
        )
        
        if not result['success']:
            print(f"\n❌ Error: {result['message']}")
            return
        
        print("\n" + "-" * 70)
        print("  Preview:")
        print("-" * 70)
        print(result.get('preview', 'No preview available'))
        print("-" * 70)
        
        # Apply?
        if questionary.confirm(
            "Insert this step?",
            default=False,
            style=custom_style
        ).ask():
            print("\n⏳ Inserting step...")
            result = self.designer.insert_step(
                phase_id=phase_id,
                step_data=step_data,
                insert_after=insert_after,
                insert_before=insert_before,
                cascade_renumber=cascade,
                preview_only=False
            )
            
            if result['success']:
                print(f"\n✅ {result['message']}")
            else:
                print(f"\n❌ Error: {result['message']}")
        else:
            print("\n❌ Cancelled.")
        
        input("\nPress Enter to continue...")
    
    def _move_menu(self):
        """Move, swap, or reorder phases/steps."""
        print("\n" + "=" * 70)
        print("  Move / Swap / Reorder")
        print("=" * 70 + "\n")
        
        # Ask what operation to perform
        operation = questionary.select(
            "What operation would you like to perform?",
            choices=[
                {'name': 'Move Phase', 'value': 'move_phase'},
                {'name': 'Move Step', 'value': 'move_step'},
                {'name': 'Swap Phases', 'value': 'swap_phases'},
                {'name': 'Swap Steps', 'value': 'swap_steps'},
                {'name': 'Reorder Phases (batch)', 'value': 'reorder_phases'},
                {'name': 'Reorder Steps (batch)', 'value': 'reorder_steps'}
            ],
            style=custom_style
        ).ask()
        
        if operation == 'move_phase':
            self._move_phase()
        elif operation == 'move_step':
            self._move_step()
        elif operation == 'swap_phases':
            self._swap_phases()
        elif operation == 'swap_steps':
            self._swap_steps()
        elif operation == 'reorder_phases':
            self._reorder_phases()
        elif operation == 'reorder_steps':
            self._reorder_steps()
    
    def _move_phase(self):
        """Move a phase to a new position."""
        spec = self.manager.get_specification()
        flow = spec.get('flows', {}).get(self.manager.flow_name, {})
        phases = flow.get('phases', [])
        
        if not phases:
            print("\n⚠️  No phases found.")
            input("\nPress Enter to continue...")
            return
        
        sorted_phases = sorted(phases, key=lambda p: p.get('sequence', 0))
        
        # Display current order
        print("\nCurrent Phase Order:")
        for phase in sorted_phases:
            print(f"  [{phase['sequence']}] {phase['name']} ({phase['phase_id']})")
        
        # Ask which phase to move
        from_seq = questionary.text(
            "\nEnter sequence number of phase to move:",
            validate=lambda x: x.isdigit() and int(x) > 0 or "Must be a positive number"
        ).ask()
        from_seq = int(from_seq)
        
        # Ask where to move it
        to_seq = questionary.text(
            f"Move phase from [{from_seq}] to which sequence?",
            validate=lambda x: x.isdigit() and int(x) > 0 or "Must be a positive number"
        ).ask()
        to_seq = int(to_seq)
        
        if from_seq == to_seq:
            print("\n⚠️  Source and target are the same. Nothing to do.")
            input("\nPress Enter to continue...")
            return
        
        # Preview
        print("\n" + "=" * 70)
        print("  Preview Changes")
        print("=" * 70)
        
        preview_result = self.designer.move_phase(
            from_sequence=from_seq,
            to_sequence=to_seq,
            preview_only=True
        )
        
        if not preview_result['success']:
            print(f"\n❌ Error: {preview_result['message']}")
            input("\nPress Enter to continue...")
            return
        
        print("\nSequence Changes:")
        for old_seq, new_seq in sorted(preview_result['mappings'].items()):
            if old_seq != new_seq:
                print(f"  [{old_seq}] → [{new_seq}]")
        
        # Confirm
        confirm = questionary.confirm(
            "\nApply these changes?",
            default=False,
            style=custom_style
        ).ask()
        
        if confirm:
            result = self.designer.move_phase(
                from_sequence=from_seq,
                to_sequence=to_seq,
                preview_only=False
            )
            
            if result['success']:
                print(f"\n✅ {result['message']}")
            else:
                print(f"\n❌ Error: {result['message']}")
        else:
            print("\n❌ Cancelled.")
        
        input("\nPress Enter to continue...")
    
    def _move_step(self):
        """Move a step to a new position within its phase."""
        spec = self.manager.get_specification()
        flow = spec.get('flows', {}).get(self.manager.flow_name, {})
        phases = flow.get('phases', [])
        
        if not phases:
            print("\n⚠️  No phases found.")
            input("\nPress Enter to continue...")
            return
        
        sorted_phases = sorted(phases, key=lambda p: p.get('sequence', 0))
        
        phase_choices = []
        for phase in sorted_phases:
            steps_count = len(phase.get('steps', []))
            phase_choices.append({
                'name': f"{phase['name']} ({steps_count} steps)",
                'value': phase['phase_id']
            })
        
        phase_id = questionary.select(
            "Select phase containing the step:",
            choices=phase_choices,
            style=custom_style
        ).ask()
        
        # Find the phase
        target_phase = None
        for phase in phases:
            if phase['phase_id'] == phase_id:
                target_phase = phase
                break
        
        if not target_phase:
            print("\n❌ Phase not found.")
            input("\nPress Enter to continue...")
            return
        
        steps = target_phase.get('steps', [])
        if len(steps) < 2:
            print("\n⚠️  Phase must have at least 2 steps to move.")
            input("\nPress Enter to continue...")
            return
        
        sorted_steps = sorted(steps, key=lambda s: s.get('sequence', 0))
        
        # Display current order
        print(f"\nCurrent Step Order in '{target_phase['name']}':")
        for step in sorted_steps:
            print(f"  [{step['sequence']}] {step['name']} ({step['step_id']})")
        
        # Ask which step to move
        from_seq = questionary.text(
            "\nEnter sequence number of step to move:",
            validate=lambda x: x.isdigit() and int(x) > 0 or "Must be a positive number"
        ).ask()
        from_seq = int(from_seq)
        
        # Ask where to move it
        to_seq = questionary.text(
            f"Move step from [{from_seq}] to which sequence?",
            validate=lambda x: x.isdigit() and int(x) > 0 or "Must be a positive number"
        ).ask()
        to_seq = int(to_seq)
        
        if from_seq == to_seq:
            print("\n⚠️  Source and target are the same. Nothing to do.")
            input("\nPress Enter to continue...")
            return
        
        # Preview
        print("\n" + "=" * 70)
        print("  Preview Changes")
        print("=" * 70)
        
        preview_result = self.designer.move_step(
            phase_id=phase_id,
            from_sequence=from_seq,
            to_sequence=to_seq,
            preview_only=True
        )
        
        if not preview_result['success']:
            print(f"\n❌ Error: {preview_result['message']}")
            input("\nPress Enter to continue...")
            return
        
        print("\nSequence Changes:")
        for old_seq, new_seq in sorted(preview_result['mappings'].items()):
            if old_seq != new_seq:
                print(f"  [{old_seq}] → [{new_seq}]")
        
        # Confirm
        confirm = questionary.confirm(
            "\nApply these changes?",
            default=False,
            style=custom_style
        ).ask()
        
        if confirm:
            result = self.designer.move_step(
                phase_id=phase_id,
                from_sequence=from_seq,
                to_sequence=to_seq,
                preview_only=False
            )
            
            if result['success']:
                print(f"\n✅ {result['message']}")
            else:
                print(f"\n❌ Error: {result['message']}")
        else:
            print("\n❌ Cancelled.")
        
        input("\nPress Enter to continue...")
    
    def _swap_phases(self):
        """Swap two phases."""
        spec = self.manager.get_specification()
        flow = spec.get('flows', {}).get(self.manager.flow_name, {})
        phases = flow.get('phases', [])
        
        if len(phases) < 2:
            print("\n⚠️  Need at least 2 phases to swap.")
            input("\nPress Enter to continue...")
            return
        
        sorted_phases = sorted(phases, key=lambda p: p.get('sequence', 0))
        
        # Display current order
        print("\nCurrent Phase Order:")
        for phase in sorted_phases:
            print(f"  [{phase['sequence']}] {phase['name']} ({phase['phase_id']})")
        
        # Ask which phases to swap
        seq_a = questionary.text(
            "\nEnter sequence number of first phase:",
            validate=lambda x: x.isdigit() and int(x) > 0 or "Must be a positive number"
        ).ask()
        seq_a = int(seq_a)
        
        seq_b = questionary.text(
            "Enter sequence number of second phase:",
            validate=lambda x: x.isdigit() and int(x) > 0 or "Must be a positive number"
        ).ask()
        seq_b = int(seq_b)
        
        if seq_a == seq_b:
            print("\n⚠️  Cannot swap a phase with itself.")
            input("\nPress Enter to continue...")
            return
        
        # Preview
        print("\n" + "=" * 70)
        print("  Preview Changes")
        print("=" * 70)
        
        preview_result = self.designer.swap_phases(
            sequence_a=seq_a,
            sequence_b=seq_b,
            preview_only=True
        )
        
        if not preview_result['success']:
            print(f"\n❌ Error: {preview_result['message']}")
            input("\nPress Enter to continue...")
            return
        
        print("\nSwap:")
        print(f"  Phase at [{seq_a}] ↔ Phase at [{seq_b}]")
        
        # Confirm
        confirm = questionary.confirm(
            "\nApply this swap?",
            default=False,
            style=custom_style
        ).ask()
        
        if confirm:
            result = self.designer.swap_phases(
                sequence_a=seq_a,
                sequence_b=seq_b,
                preview_only=False
            )
            
            if result['success']:
                print(f"\n✅ {result['message']}")
            else:
                print(f"\n❌ Error: {result['message']}")
        else:
            print("\n❌ Cancelled.")
        
        input("\nPress Enter to continue...")
    
    def _swap_steps(self):
        """Swap two steps within a phase."""
        spec = self.manager.get_specification()
        flow = spec.get('flows', {}).get(self.manager.flow_name, {})
        phases = flow.get('phases', [])
        
        if not phases:
            print("\n⚠️  No phases found.")
            input("\nPress Enter to continue...")
            return
        
        sorted_phases = sorted(phases, key=lambda p: p.get('sequence', 0))
        
        phase_choices = []
        for phase in sorted_phases:
            steps_count = len(phase.get('steps', []))
            phase_choices.append({
                'name': f"{phase['name']} ({steps_count} steps)",
                'value': phase['phase_id']
            })
        
        phase_id = questionary.select(
            "Select phase containing the steps:",
            choices=phase_choices,
            style=custom_style
        ).ask()
        
        # Find the phase
        target_phase = None
        for phase in phases:
            if phase['phase_id'] == phase_id:
                target_phase = phase
                break
        
        if not target_phase:
            print("\n❌ Phase not found.")
            input("\nPress Enter to continue...")
            return
        
        steps = target_phase.get('steps', [])
        if len(steps) < 2:
            print("\n⚠️  Need at least 2 steps to swap.")
            input("\nPress Enter to continue...")
            return
        
        sorted_steps = sorted(steps, key=lambda s: s.get('sequence', 0))
        
        # Display current order
        print(f"\nCurrent Step Order in '{target_phase['name']}':")
        for step in sorted_steps:
            print(f"  [{step['sequence']}] {step['name']} ({step['step_id']})")
        
        # Ask which steps to swap
        seq_a = questionary.text(
            "\nEnter sequence number of first step:",
            validate=lambda x: x.isdigit() and int(x) > 0 or "Must be a positive number"
        ).ask()
        seq_a = int(seq_a)
        
        seq_b = questionary.text(
            "Enter sequence number of second step:",
            validate=lambda x: x.isdigit() and int(x) > 0 or "Must be a positive number"
        ).ask()
        seq_b = int(seq_b)
        
        if seq_a == seq_b:
            print("\n⚠️  Cannot swap a step with itself.")
            input("\nPress Enter to continue...")
            return
        
        # Preview
        print("\n" + "=" * 70)
        print("  Preview Changes")
        print("=" * 70)
        
        preview_result = self.designer.swap_steps(
            phase_id=phase_id,
            sequence_a=seq_a,
            sequence_b=seq_b,
            preview_only=True
        )
        
        if not preview_result['success']:
            print(f"\n❌ Error: {preview_result['message']}")
            input("\nPress Enter to continue...")
            return
        
        print("\nSwap:")
        print(f"  Step at [{seq_a}] ↔ Step at [{seq_b}]")
        
        # Confirm
        confirm = questionary.confirm(
            "\nApply this swap?",
            default=False,
            style=custom_style
        ).ask()
        
        if confirm:
            result = self.designer.swap_steps(
                phase_id=phase_id,
                sequence_a=seq_a,
                sequence_b=seq_b,
                preview_only=False
            )
            
            if result['success']:
                print(f"\n✅ {result['message']}")
            else:
                print(f"\n❌ Error: {result['message']}")
        else:
            print("\n❌ Cancelled.")
        
        input("\nPress Enter to continue...")
    
    def _reorder_phases(self):
        """Batch reorder phases."""
        spec = self.manager.get_specification()
        flow = spec.get('flows', {}).get(self.manager.flow_name, {})
        phases = flow.get('phases', [])
        
        if len(phases) < 2:
            print("\n⚠️  Need at least 2 phases to reorder.")
            input("\nPress Enter to continue...")
            return
        
        sorted_phases = sorted(phases, key=lambda p: p.get('sequence', 0))
        
        # Display current order
        print("\nCurrent Phase Order:")
        for i, phase in enumerate(sorted_phases, 1):
            print(f"  {i}. [{phase['sequence']}] {phase['name']} ({phase['phase_id']})")
        
        print("\n" + "=" * 70)
        print("Enter new order as comma-separated list of sequence numbers.")
        print("Example: 3,1,2 means phase at [3] becomes first, [1] second, [2] third")
        print("=" * 70)
        
        new_order_input = questionary.text(
            "\nEnter new order:",
            validate=lambda x: all(s.strip().isdigit() for s in x.split(',')) or "Must be comma-separated numbers"
        ).ask()
        
        # Parse the new order
        new_order_list = [int(s.strip()) for s in new_order_input.split(',')]
        
        # Validate completeness
        current_sequences = sorted([p['sequence'] for p in phases])
        if sorted(new_order_list) != current_sequences:
            print(f"\n❌ Error: New order must include all sequences: {current_sequences}")
            input("\nPress Enter to continue...")
            return
        
        # Build the mapping (old_seq -> new_seq)
        new_order_map = {}
        for new_position, old_sequence in enumerate(new_order_list, 1):
            new_order_map[old_sequence] = new_position
        
        # Preview
        print("\n" + "=" * 70)
        print("  Preview Changes")
        print("=" * 70)
        
        preview_result = self.designer.reorder_phases(
            new_order=new_order_map,
            preview_only=True
        )
        
        if not preview_result['success']:
            print(f"\n❌ Error: {preview_result['message']}")
            input("\nPress Enter to continue...")
            return
        
        print("\nSequence Changes:")
        for old_seq, new_seq in sorted(preview_result['mappings'].items()):
            if old_seq != new_seq:
                print(f"  [{old_seq}] → [{new_seq}]")
        
        # Confirm
        confirm = questionary.confirm(
            "\nApply these changes?",
            default=False,
            style=custom_style
        ).ask()
        
        if confirm:
            result = self.designer.reorder_phases(
                new_order=new_order_map,
                preview_only=False
            )
            
            if result['success']:
                print(f"\n✅ {result['message']}")
            else:
                print(f"\n❌ Error: {result['message']}")
        else:
            print("\n❌ Cancelled.")
        
        input("\nPress Enter to continue...")
    
    def _reorder_steps(self):
        """Batch reorder steps within a phase."""
        spec = self.manager.get_specification()
        flow = spec.get('flows', {}).get(self.manager.flow_name, {})
        phases = flow.get('phases', [])
        
        if not phases:
            print("\n⚠️  No phases found.")
            input("\nPress Enter to continue...")
            return
        
        sorted_phases = sorted(phases, key=lambda p: p.get('sequence', 0))
        
        phase_choices = []
        for phase in sorted_phases:
            steps_count = len(phase.get('steps', []))
            phase_choices.append({
                'name': f"{phase['name']} ({steps_count} steps)",
                'value': phase['phase_id']
            })
        
        phase_id = questionary.select(
            "Select phase containing the steps:",
            choices=phase_choices,
            style=custom_style
        ).ask()
        
        # Find the phase
        target_phase = None
        for phase in phases:
            if phase['phase_id'] == phase_id:
                target_phase = phase
                break
        
        if not target_phase:
            print("\n❌ Phase not found.")
            input("\nPress Enter to continue...")
            return
        
        steps = target_phase.get('steps', [])
        if len(steps) < 2:
            print("\n⚠️  Need at least 2 steps to reorder.")
            input("\nPress Enter to continue...")
            return
        
        sorted_steps = sorted(steps, key=lambda s: s.get('sequence', 0))
        
        # Display current order
        print(f"\nCurrent Step Order in '{target_phase['name']}':")
        for i, step in enumerate(sorted_steps, 1):
            print(f"  {i}. [{step['sequence']}] {step['name']} ({step['step_id']})")
        
        print("\n" + "=" * 70)
        print("Enter new order as comma-separated list of sequence numbers.")
        print("Example: 3,1,2 means step at [3] becomes first, [1] second, [2] third")
        print("=" * 70)
        
        new_order_input = questionary.text(
            "\nEnter new order:",
            validate=lambda x: all(s.strip().isdigit() for s in x.split(',')) or "Must be comma-separated numbers"
        ).ask()
        
        # Parse the new order
        new_order_list = [int(s.strip()) for s in new_order_input.split(',')]
        
        # Validate completeness
        current_sequences = sorted([s['sequence'] for s in steps])
        if sorted(new_order_list) != current_sequences:
            print(f"\n❌ Error: New order must include all sequences: {current_sequences}")
            input("\nPress Enter to continue...")
            return
        
        # Build the mapping (old_seq -> new_seq)
        new_order_map = {}
        for new_position, old_sequence in enumerate(new_order_list, 1):
            new_order_map[old_sequence] = new_position
        
        # Preview
        print("\n" + "=" * 70)
        print("  Preview Changes")
        print("=" * 70)
        
        preview_result = self.designer.reorder_steps(
            phase_id=phase_id,
            new_order=new_order_map,
            preview_only=True
        )
        
        if not preview_result['success']:
            print(f"\n❌ Error: {preview_result['message']}")
            input("\nPress Enter to continue...")
            return
        
        print("\nSequence Changes:")
        for old_seq, new_seq in sorted(preview_result['mappings'].items()):
            if old_seq != new_seq:
                print(f"  [{old_seq}] → [{new_seq}]")
        
        # Confirm
        confirm = questionary.confirm(
            "\nApply these changes?",
            default=False,
            style=custom_style
        ).ask()
        
        if confirm:
            result = self.designer.reorder_steps(
                phase_id=phase_id,
                new_order=new_order_map,
                preview_only=False
            )
            
            if result['success']:
                print(f"\n✅ {result['message']}")
            else:
                print(f"\n❌ Error: {result['message']}")
        else:
            print("\n❌ Cancelled.")
        
        input("\nPress Enter to continue...")
    
    def _delete_menu(self):
        """Delete a phase or step."""
        print("\n" + "=" * 70)
        print("  Delete Phase or Step")
        print("=" * 70 + "\n")
        
        # Ask what to delete
        delete_type = questionary.select(
            "What would you like to delete?",
            choices=[
                {'name': 'Phase', 'value': 'phase'},
                {'name': 'Step', 'value': 'step'}
            ],
            style=custom_style
        ).ask()
        
        if delete_type == 'phase':
            self._delete_phase()
        else:
            self._delete_step()
    
    def _delete_phase(self):
        """Delete a phase."""
        spec = self.manager.get_specification()
        flow = spec.get('flows', {}).get(self.manager.flow_name, {})
        phases = flow.get('phases', [])
        
        if not phases:
            print("⚠️  No phases to delete.")
            return
        
        # Select phase
        phase_choices = [
            {
                'name': f"[{p.get('sequence', '?')}] {p.get('name', 'Unnamed')} (ID: {p.get('phase_id')})",
                'value': p.get('phase_id')
            }
            for p in sorted(phases, key=lambda p: p.get('sequence', 0))
        ]
        
        phase_id = questionary.select(
            "Select phase to delete:",
            choices=phase_choices,
            style=custom_style
        ).ask()
        
        # Cascade renumber?
        cascade = questionary.confirm(
            "Cascade renumber remaining phases?",
            default=True,
            style=custom_style
        ).ask()
        
        # Preview
        print("\n⏳ Generating preview...")
        result = self.designer.delete_phase(
            phase_id=phase_id,
            cascade_renumber=cascade,
            preview_only=True
        )
        
        if not result['success']:
            print(f"\n❌ Error: {result['message']}")
            return
        
        print("\n" + "-" * 70)
        print("  Preview:")
        print("-" * 70)
        print(result.get('preview', 'No preview available'))
        print("-" * 70)
        
        # Confirm deletion
        if questionary.confirm(
            f"⚠️  Delete phase '{phase_id}'? This cannot be undone!",
            default=False,
            style=custom_style
        ).ask():
            print("\n⏳ Deleting phase...")
            result = self.designer.delete_phase(
                phase_id=phase_id,
                cascade_renumber=cascade,
                preview_only=False
            )
            
            if result['success']:
                print(f"\n✅ {result['message']}")
            else:
                print(f"\n❌ Error: {result['message']}")
        else:
            print("\n❌ Cancelled.")
        
        input("\nPress Enter to continue...")
    
    def _delete_step(self):
        """Delete a step."""
        # Select phase
        spec = self.manager.get_specification()
        flow = spec.get('flows', {}).get(self.manager.flow_name, {})
        phases = flow.get('phases', [])
        
        if not phases:
            print("⚠️  No phases found.")
            return
        
        phase_choices = [
            {
                'name': f"[{p.get('sequence', '?')}] {p.get('name', 'Unnamed')} (ID: {p.get('phase_id')})",
                'value': p.get('phase_id')
            }
            for p in sorted(phases, key=lambda p: p.get('sequence', 0))
        ]
        
        phase_id = questionary.select(
            "Select phase containing the step:",
            choices=phase_choices,
            style=custom_style
        ).ask()
        
        # Get steps in phase
        target_phase = next((p for p in phases if p.get('phase_id') == phase_id), None)
        steps = target_phase.get('steps', []) if target_phase else []
        
        if not steps:
            print(f"⚠️  No steps in phase '{phase_id}'.")
            return
        
        # Select step
        step_choices = [
            {
                'name': f"[{s.get('sequence', '?')}] {s.get('name', 'Unnamed')} (ID: {s.get('step_id')})",
                'value': s.get('step_id')
            }
            for s in sorted(steps, key=lambda s: s.get('sequence', 0))
        ]
        
        step_id = questionary.select(
            "Select step to delete:",
            choices=step_choices,
            style=custom_style
        ).ask()
        
        # Cascade renumber?
        cascade = questionary.confirm(
            "Cascade renumber remaining steps?",
            default=True,
            style=custom_style
        ).ask()
        
        # Preview
        print("\n⏳ Generating preview...")
        result = self.designer.delete_step(
            phase_id=phase_id,
            step_id=step_id,
            cascade_renumber=cascade,
            preview_only=True
        )
        
        if not result['success']:
            print(f"\n❌ Error: {result['message']}")
            return
        
        print("\n" + "-" * 70)
        print("  Preview:")
        print("-" * 70)
        print(result.get('preview', 'No preview available'))
        print("-" * 70)
        
        # Confirm deletion
        if questionary.confirm(
            f"⚠️  Delete step '{step_id}'? This cannot be undone!",
            default=False,
            style=custom_style
        ).ask():
            print("\n⏳ Deleting step...")
            result = self.designer.delete_step(
                phase_id=phase_id,
                step_id=step_id,
                cascade_renumber=cascade,
                preview_only=False
            )
            
            if result['success']:
                print(f"\n✅ {result['message']}")
            else:
                print(f"\n❌ Error: {result['message']}")
        else:
            print("\n❌ Cancelled.")
        
        input("\nPress Enter to continue...")
    
    def _view_history(self):
        """View transformation history."""
        print("\n" + "=" * 70)
        print("  Transformation History")
        print("=" * 70 + "\n")
        
        result = self.designer.get_transformation_history(limit=20)
        
        if not result['success']:
            print(f"❌ Error: {result['message']}")
            input("\nPress Enter to continue...")
            return
        
        history = result.get('history', [])
        
        if not history:
            print("📋 No transformation history found.")
        else:
            print(f"📋 Showing last {len(history)} transformations:\n")
            for i, entry in enumerate(history, 1):
                timestamp = entry.get('timestamp', 'Unknown')
                trans_type = entry.get('type', 'unknown')
                description = entry.get('description', 'No description')
                print(f"{i}. [{timestamp}] {trans_type}: {description}")
        
        input("\nPress Enter to continue...")
    
    def _rollback_menu(self):
        """Rollback transformations."""
        print("\n" + "=" * 70)
        print("  Rollback Transformations")
        print("=" * 70 + "\n")
        
        # Get history first
        result = self.designer.get_transformation_history(limit=10)
        
        if not result['success'] or not result.get('history'):
            print("📋 No transformation history to rollback.")
            input("\nPress Enter to continue...")
            return
        
        history = result['history']
        print(f"📋 Last {len(history)} transformations:\n")
        for i, entry in enumerate(history, 1):
            timestamp = entry.get('timestamp', 'Unknown')
            trans_type = entry.get('type', 'unknown')
            description = entry.get('description', 'No description')
            print(f"{i}. [{timestamp}] {trans_type}: {description}")
        
        # Ask how many to rollback
        steps = questionary.text(
            "\nHow many transformations to rollback?",
            default="1",
            validate=lambda x: x.isdigit() and int(x) > 0 and int(x) <= len(history) or f"Must be 1-{len(history)}"
        ).ask()
        
        steps = int(steps)
        
        # Preview rollback
        print("\n⏳ Generating rollback preview...")
        result = self.designer.rollback_transformation(
            steps=steps,
            preview_only=True
        )
        
        if not result['success']:
            print(f"\n❌ Error: {result['message']}")
            input("\nPress Enter to continue...")
            return
        
        print("\n" + "-" * 70)
        print("  Rollback Preview:")
        print("-" * 70)
        print(result.get('preview', 'No preview available'))
        print("-" * 70)
        
        # Confirm rollback
        if questionary.confirm(
            f"⚠️  Rollback {steps} transformation(s)?",
            default=False,
            style=custom_style
        ).ask():
            print("\n⏳ Rolling back...")
            result = self.designer.rollback_transformation(
                steps=steps,
                preview_only=False
            )
            
            if result['success']:
                print(f"\n✅ {result['message']}")
            else:
                print(f"\n❌ Error: {result['message']}")
        else:
            print("\n❌ Cancelled.")
        
        input("\nPress Enter to continue...")


def main():
    """Main entry point for the flow editor."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Interactive Control Flow Editor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /path/to/project
  %(prog)s .
        """
    )
    parser.add_argument(
        'project_root',
        help='Path to the project root directory'
    )
    
    args = parser.parse_args()
    
    # Validate project root
    project_root = Path(args.project_root).resolve()
    if not project_root.exists():
        print(f"❌ Error: Project root does not exist: {project_root}")
        sys.exit(1)
    
    # Run the editor
    try:
        editor = ControlFlowEditor(str(project_root))
        editor.run()
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
