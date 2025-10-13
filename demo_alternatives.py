#!/usr/bin/env python3
"""
Diagram Library Comparison Demo
Compare Mermaid.js vs Python alternatives for control flow visualization.
"""

import sys
import subprocess
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from control_flow_engine.visualizer.graphviz_generator import GraphvizFlowVisualizer, compare_with_mermaid
except ImportError:
    print("❌ Could not import GraphvizFlowVisualizer")
    print("   Make sure you're running from the control-flow directory")
    sys.exit(1)


def demo_graphviz_alternative():
    """Demonstrate Graphviz as a Mermaid alternative."""
    print("🎨 Python Diagram Library Alternatives to Mermaid")
    print("=" * 60)
    print()
    
    # Show the comparison
    compare_with_mermaid()
    print()
    
    # Find a control flow YAML file to demonstrate with
    spec_files = list(Path(".").glob("**/control_flows.yml"))
    
    if not spec_files:
        print("❌ No control_flows.yml files found to demonstrate with")
        return
        
    spec_file = spec_files[0]
    print(f"📄 Using specification: {spec_file}")
    print()
    
    # Create visualizer
    visualizer = GraphvizFlowVisualizer(spec_file)
    
    try:
        # Show DOT source code
        print("🔍 Generated Graphviz DOT Source (Combined Diagram):")
        print("-" * 50)
        dot_source = visualizer.get_graphviz_source('combined')
        print(dot_source[:500] + "..." if len(dot_source) > 500 else dot_source)
        print()
        
        # Try to generate diagrams if graphviz is installed
        try:
            import graphviz
            print("✅ Graphviz package available - generating sample diagrams...")
            
            output_dir = Path("demo_diagrams")
            visualizer.generate_diagrams(output_dir, ['svg'])
            
            print(f"\n📁 Sample diagrams generated in: {output_dir}")
            
        except ImportError:
            print("⚠️  Graphviz package not installed")
            print("   Install with: pip install graphviz")
            print("   Note: Also requires system Graphviz installation")
            
    except Exception as e:
        print(f"❌ Error demonstrating Graphviz: {e}")


def show_other_python_alternatives():
    """Show other Python diagramming alternatives."""
    print("\n🐍 Other Excellent Python Diagram Libraries")
    print("=" * 50)
    
    libraries = [
        {
            "name": "Diagrams",
            "description": "Create beautiful architecture diagrams with code",
            "install": "pip install diagrams",
            "best_for": "Cloud architecture, system design",
            "example": "from diagrams import Diagram\\nfrom diagrams.aws.compute import EC2"
        },
        {
            "name": "NetworkX + Matplotlib", 
            "description": "Network analysis and graph visualization",
            "install": "pip install networkx matplotlib",
            "best_for": "Network graphs, dependency analysis",
            "example": "import networkx as nx\\nG = nx.DiGraph()\\nG.add_edge('A', 'B')"
        },
        {
            "name": "Plotly Graph Objects",
            "description": "Interactive web-based diagrams",
            "install": "pip install plotly",
            "best_for": "Interactive dashboards, web applications", 
            "example": "import plotly.graph_objects as go\\nfig = go.Figure()"
        },
        {
            "name": "PyGraphviz",
            "description": "Python bindings for Graphviz",
            "install": "pip install pygraphviz",
            "best_for": "When you need full Graphviz power",
            "example": "import pygraphviz as pgv\\nG = pgv.AGraph()"
        },
        {
            "name": "Matplotlib + NetworkX",
            "description": "Scientific plotting with graph layouts",
            "install": "pip install matplotlib networkx",
            "best_for": "Scientific publications, data analysis",
            "example": "import matplotlib.pyplot as plt\\nimport networkx as nx"
        }
    ]
    
    for i, lib in enumerate(libraries, 1):
        print(f"{i}. **{lib['name']}**")
        print(f"   Description: {lib['description']}")
        print(f"   Install: `{lib['install']}`")
        print(f"   Best for: {lib['best_for']}")
        print(f"   Example: `{lib['example']}`")
        print()


def recommendation_summary():
    """Provide clear recommendations."""
    print("💡 **Recommendations for Control Flow System**")
    print("=" * 50)
    print()
    print("**Primary Recommendation: Graphviz**")
    print("• Perfect for flowcharts and process diagrams")
    print("• Professional publication-quality output")
    print("• Automatic layout algorithms")
    print("• Multiple output formats (SVG, PNG, PDF)")
    print("• No JavaScript dependencies")
    print("• Mature and battle-tested")
    print()
    print("**Alternative Options:**")
    print("• **Diagrams**: If you want beautiful pre-made icons")
    print("• **Plotly**: If you need interactive web diagrams")
    print("• **NetworkX**: If you need custom layout algorithms")
    print()
    print("**Migration Strategy:**")
    print("1. Keep existing Mermaid generator for compatibility")
    print("2. Add Graphviz generator as primary option")
    print("3. Use configuration to choose output format")
    print("4. Gradually phase out Mermaid if preferred")
    print()
    print("**Installation:**")
    print("```bash")
    print("# Python package")
    print("pip install graphviz")
    print()
    print("# System dependency (Ubuntu/Debian)")
    print("sudo apt install graphviz")
    print()
    print("# System dependency (macOS)")
    print("brew install graphviz")
    print("```")


def main():
    """Run the complete demonstration."""
    print("🚀 Control Flow Visualization Alternatives Demo")
    print("=" * 60)
    print()
    
    try:
        demo_graphviz_alternative()
        show_other_python_alternatives()
        recommendation_summary()
        
        print("\n✅ Demonstration completed!")
        print("\nNext steps:")
        print("1. Install graphviz: pip install graphviz")
        print("2. Test the GraphvizFlowVisualizer")
        print("3. Compare output quality with Mermaid")
        print("4. Decide on migration strategy")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()