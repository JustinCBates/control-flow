#!/usr/bin/env python3
"""
Demonstrate how control_flows.yml works with the Graphviz visualizer.
This shows how to parse and visualize the config-manager control flow.
"""

from pathlib import Path
import yaml

def explain_control_flows_yml():
    """Explain the structure and purpose of control_flows.yml"""
    
    print("=" * 80)
    print("HOW CONTROL_FLOWS.YML WORKS")
    print("=" * 80)
    print()
    
    print("📋 PURPOSE:")
    print("   control_flows.yml is a design-first specification that documents:")
    print("   - What the component does (flows and phases)")
    print("   - Current implementation status (IMPLEMENTED, PLANNED, etc.)")
    print("   - Data flow (artifacts produced and consumed)")
    print("   - Decision points and configuration options")
    print()
    
    print("🏗️ STRUCTURE:")
    print()
    print("   1. COMPONENT INFO")
    print("      - Basic metadata about the component")
    print("      - Name, description, version")
    print()
    
    print("   2. ENTRY POINTS")
    print("      - CLI commands or API endpoints")
    print("      - Status tracking (IMPLEMENTED, PLANNED, etc.)")
    print("      - Links to flows they trigger")
    print()
    
    print("   3. FLOWS")
    print("      - High-level process descriptions")
    print("      - Broken into phases or steps")
    print("      - Each phase has:")
    print("        * Unique ID")
    print("        * Name and description")
    print("        * Implementation status")
    print("        * Artifacts it produces")
    print("        * Artifacts it consumes")
    print()
    
    print("   4. ARTIFACTS")
    print("      - Data products created/used by phases")
    print("      - File formats (YAML, JSON, etc.)")
    print("      - Help track data flow through system")
    print()
    
    print("   5. DECISION POINTS")
    print("      - Configuration options")
    print("      - Conditional behavior")
    print("      - Default choices")
    print()
    
    print("   6. IMPLEMENTATION STATUS")
    print("      - Overall completion tracking")
    print("      - Last update timestamp")
    print("      - Development notes")
    print()

def parse_and_display_config_manager_flow():
    """Parse the config-manager control flow and display key information"""
    
    spec_file = Path(__file__).parent.parent.parent / "config-manager" / "design_specs" / "control_flows.yml"
    
    if not spec_file.exists():
        print(f"❌ Spec file not found: {spec_file}")
        return
    
    print("=" * 80)
    print("CONFIG-MANAGER CONTROL FLOW")
    print("=" * 80)
    print()
    
    with open(spec_file, 'r') as f:
        spec = yaml.safe_load(f)
    
    # Display component info
    component = spec.get('component', {})
    print(f"📦 COMPONENT: {component.get('name')}")
    print(f"   Description: {component.get('description')}")
    print(f"   Version: {component.get('version')}")
    print()
    
    # Display entry points
    print("🚪 ENTRY POINTS:")
    entry_points = spec.get('entry_points', {})
    for cmd, details in entry_points.items():
        if isinstance(details, dict):
            status = details.get('status', 'UNKNOWN')
            status_icon = "✅" if status == "IMPLEMENTED" else "⏳"
            desc = details.get('description', '')
            print(f"   {status_icon} {cmd}: {desc} ({status})")
    print()
    
    # Display main flow
    flows = spec.get('flows', {})
    main_flow = flows.get('main_config_flow', {})
    
    print("🔄 MAIN CONFIGURATION FLOW:")
    print(f"   {main_flow.get('description')}")
    print()
    
    phases = main_flow.get('phases', [])
    print(f"   {len(phases)} Phases:")
    for i, phase in enumerate(phases, 1):
        status = phase.get('status', 'UNKNOWN')
        status_icon = "✅" if status == "IMPLEMENTED" else "⏳"
        print(f"   {i}. {status_icon} {phase.get('name')} ({status})")
        print(f"      {phase.get('description')}")
        
        # Show data flow
        produces = phase.get('artifacts_produced', [])
        consumes = phase.get('artifacts_consumed', [])
        
        if consumes:
            print(f"      📥 Consumes: {', '.join(consumes)}")
        if produces:
            print(f"      📤 Produces: {', '.join(produces)}")
        print()
    
    # Display artifacts
    artifacts = spec.get('artifacts', {})
    print(f"💾 ARTIFACTS ({len(artifacts)} total):")
    for name, details in artifacts.items():
        format_type = details.get('format', 'Unknown')
        desc = details.get('description', '')
        print(f"   📦 {name} ({format_type})")
        print(f"      {desc}")
    print()
    
    # Display decision points
    decisions = spec.get('decision_points', {})
    print(f"🔀 DECISION POINTS ({len(decisions)} total):")
    for name, details in decisions.items():
        default = details.get('default', 'None')
        options = details.get('options', [])
        print(f"   • {name}")
        print(f"     Options: {', '.join(options)}")
        print(f"     Default: {default}")
    print()
    
    # Display status
    status = spec.get('implementation_status', {})
    overall = status.get('overall', 'UNKNOWN')
    last_updated = status.get('last_updated', 'Unknown')
    notes = status.get('notes', '')
    
    print(f"📊 IMPLEMENTATION STATUS:")
    status_icon = "✅" if overall == "IMPLEMENTED" else "⏳"
    print(f"   {status_icon} Overall: {overall}")
    print(f"   📅 Last Updated: {last_updated}")
    print(f"   📝 Notes: {notes}")
    print()

def demonstrate_visualization():
    """Show how this can be visualized with Graphviz"""
    
    print("=" * 80)
    print("VISUALIZATION WITH GRAPHVIZ")
    print("=" * 80)
    print()
    
    # Convert to format compatible with GraphvizFlowVisualizer
    spec_file = Path(__file__).parent.parent.parent / "config-manager" / "design_specs" / "control_flows.yml"
    
    if not spec_file.exists():
        print(f"❌ Cannot create visualization - spec file not found")
        return
    
    with open(spec_file, 'r') as f:
        spec = yaml.safe_load(f)
    
    # Extract main flow phases
    flows = spec.get('flows', {})
    main_flow = flows.get('main_config_flow', {})
    phases = main_flow.get('phases', [])
    artifacts_spec = spec.get('artifacts', {})
    
    print("📊 To visualize this control flow:")
    print()
    print("   1. The GraphvizFlowVisualizer can parse YAML specs")
    print("   2. It generates 3 types of diagrams:")
    print("      • Phase Flow - Shows execution sequence")
    print("      • Artifact Flow - Shows data dependencies")
    print("      • Combined Flow - Shows both together")
    print()
    print("   3. Each diagram can be exported as:")
    print("      • SVG (web-friendly)")
    print("      • PNG (documentation)")
    print("      • PDF (publication)")
    print()
    print(f"   For this flow, you would see:")
    print(f"   • {len(phases)} phase nodes")
    print(f"   • {len(artifacts_spec)} artifact nodes")
    print(f"   • Arrows showing data flow")
    print(f"   • Color coding by status (green=done, yellow=in-progress)")
    print()
    
    print("💡 BENEFITS:")
    print("   ✅ Design-first: Plan before coding")
    print("   ✅ Documentation: Always up to date")
    print("   ✅ Communication: Visual + structured")
    print("   ✅ Tracking: Implementation status visible")
    print("   ✅ Analysis: Find gaps and dependencies")
    print()

def main():
    """Run the demonstration"""
    
    print()
    explain_control_flows_yml()
    print()
    input("Press Enter to see config-manager flow details...")
    print()
    parse_and_display_config_manager_flow()
    print()
    input("Press Enter to see visualization info...")
    print()
    demonstrate_visualization()
    print()
    print("=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print()
    print("1. View the actual file:")
    print("   cat external/config-manager/design_specs/control_flows.yml")
    print()
    print("2. Create a visualization (coming soon - needs conversion):")
    print("   cd external/control-flow")
    print("   python3 -m src.control_flow_engine.visualizer.graphviz_generator \\")
    print("       ../config-manager/design_specs/control_flows.yml \\")
    print("       --output-dir diagrams")
    print()
    print("3. Edit and update the flow:")
    print("   - Change status as you implement features")
    print("   - Add new phases as design evolves")
    print("   - Update artifacts when data model changes")
    print()

if __name__ == "__main__":
    main()
