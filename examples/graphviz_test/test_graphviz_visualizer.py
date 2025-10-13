#!/usr/bin/env python3
"""
Test the Graphviz flow visualizer with a sample control flow spec.
"""

from pathlib import Path
from src.control_flow_engine.visualizer.graphviz_generator import GraphvizFlowVisualizer

def test_visualizer():
    """Test diagram generation with Graphviz."""
    print("🎨 Testing Graphviz Flow Visualizer")
    print("=" * 50)
    print()
    
    # Create visualizer
    spec_file = Path(__file__).parent / "test_flow_spec.yml"
    if not spec_file.exists():
        print(f"❌ Error: {spec_file} not found")
        return False
        
    visualizer = GraphvizFlowVisualizer(spec_file)
    
    # Parse the spec
    print("📖 Parsing control flow specification...")
    visualizer.parse_yaml_spec()
    print(f"   ✅ Found {len(visualizer.phases)} phases")
    print(f"   ✅ Found {len(visualizer.artifacts)} artifacts")
    print()
    
    # List phases
    print("📋 Phases:")
    for phase_id, phase in visualizer.phases.items():
        status_icon = {
            'completed': '✅',
            'in_progress': '🔄',
            'pending': '⏳',
            'blocked': '🚫'
        }.get(phase.status, '❓')
        print(f"   {status_icon} {phase.name} ({phase.status})")
    print()
    
    # List artifacts
    print("💾 Artifacts:")
    for artifact_name, artifact in visualizer.artifacts.items():
        print(f"   📦 {artifact_name}")
        print(f"      Producers: {', '.join(artifact.producers)}")
        print(f"      Consumers: {', '.join(artifact.consumers) if artifact.consumers else 'None'}")
    print()
    
    # Generate diagrams
    output_dir = Path(__file__).parent / "test_output"
    print(f"🎨 Generating diagrams in {output_dir}...")
    
    try:
        visualizer.generate_diagrams(output_dir, formats=['svg', 'png', 'pdf'])
        print()
        print("✅ SUCCESS: All diagrams generated!")
        print()
        print(f"📂 Output directory: {output_dir}")
        print("   You can view the diagrams:")
        print(f"   - {output_dir}/phase_flow.svg")
        print(f"   - {output_dir}/artifact_flow.svg")
        print(f"   - {output_dir}/combined_flow.svg")
        return True
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_visualizer()
    exit(0 if success else 1)
