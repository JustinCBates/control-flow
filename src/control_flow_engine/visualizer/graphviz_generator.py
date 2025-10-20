#!/usr/bin/env python3
"""
Control Flow Visualizer - Graphviz Generator
Alternative to Mermaid using Graphviz for professional diagram generation.
"""

import yaml
import graphviz
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class Phase:
    id: str
    name: str
    status: str
    description: str
    artifacts_produced: List[str]
    artifacts_consumed: List[str]
    dependencies: List[str] = None


@dataclass
class Artifact:
    name: str
    description: str
    producers: List[str]
    consumers: List[str]
    lifecycle: str


class GraphvizFlowVisualizer:
    """Professional flowchart generator using Graphviz."""

    def __init__(self, spec_file: Path):
        self.spec_file = spec_file
        self.phases = {}
        self.artifacts = {}
        self.flow_data = None

    def parse_yaml_spec(self) -> Dict[str, Any]:
        """Parse YAML control flow specification."""
        with open(self.spec_file) as f:
            self.flow_data = yaml.safe_load(f)

        # Extract phases
        if "phases" in self.flow_data:
            for phase_data in self.flow_data["phases"]:
                phase = Phase(
                    id=phase_data.get("id", ""),
                    name=phase_data.get("name", ""),
                    status=phase_data.get("status", "pending"),
                    description=phase_data.get("description", ""),
                    artifacts_produced=phase_data.get("artifacts_produced", []),
                    artifacts_consumed=phase_data.get("artifacts_consumed", []),
                    dependencies=phase_data.get("dependencies", []),
                )
                self.phases[phase.id] = phase

        # Extract artifacts
        if "artifacts" in self.flow_data:
            for artifact_data in self.flow_data["artifacts"]:
                artifact = Artifact(
                    name=artifact_data.get("name", ""),
                    description=artifact_data.get("description", ""),
                    producers=artifact_data.get("producers", []),
                    consumers=artifact_data.get("consumers", []),
                    lifecycle=artifact_data.get("lifecycle", "persistent"),
                )
                self.artifacts[artifact.name] = artifact

        return self.flow_data

    def create_phase_flow_diagram(self, output_format: str = "svg") -> graphviz.Digraph:
        """Create a professional phase flow diagram."""
        dot = graphviz.Digraph(comment="Control Flow Phases")
        dot.attr(rankdir="TB", size="12,8")
        dot.attr("node", shape="box", style="rounded,filled", fontname="Arial")
        dot.attr("edge", fontname="Arial", fontsize="10")

        # Color scheme for different statuses
        status_colors = {
            "completed": "#90EE90",  # Light green
            "in_progress": "#FFE4B5",  # Moccasin
            "pending": "#E6E6FA",  # Lavender
            "blocked": "#FFB6C1",  # Light pink
            "cancelled": "#D3D3D3",  # Light gray
        }

        # Add phase nodes
        for phase_id, phase in self.phases.items():
            color = status_colors.get(phase.status, "#E6E6FA")
            label = f"{phase.name}\\n({phase.status})"
            if phase.description:
                # Truncate long descriptions
                desc = (
                    phase.description[:50] + "..."
                    if len(phase.description) > 50
                    else phase.description
                )
                label += f"\\n{desc}"

            dot.node(phase_id, label, fillcolor=color)

        # Add dependencies as edges
        for phase_id, phase in self.phases.items():
            if phase.dependencies:
                for dep in phase.dependencies:
                    if dep in self.phases:
                        dot.edge(dep, phase_id, label="depends on")

        return dot

    def create_artifact_flow_diagram(
        self, output_format: str = "svg"
    ) -> graphviz.Digraph:
        """Create an artifact flow diagram showing data dependencies."""
        dot = graphviz.Digraph(comment="Artifact Flow")
        dot.attr(rankdir="LR", size="14,10")
        dot.attr("node", fontname="Arial")
        dot.attr("edge", fontname="Arial", fontsize="10")

        # Add artifact nodes (diamond shape)
        for artifact_name, artifact in self.artifacts.items():
            label = artifact_name
            if artifact.description:
                desc = (
                    artifact.description[:30] + "..."
                    if len(artifact.description) > 30
                    else artifact.description
                )
                label += f"\\n{desc}"

            dot.node(
                f"artifact_{artifact_name}",
                label,
                shape="diamond",
                style="filled",
                fillcolor="#F0F8FF",
            )

        # Add phase nodes
        for phase_id, phase in self.phases.items():
            dot.node(
                f"phase_{phase_id}",
                phase.name,
                shape="box",
                style="rounded,filled",
                fillcolor="#E6E6FA",
            )

        # Add edges for artifact production/consumption
        for artifact_name, artifact in self.artifacts.items():
            artifact_node = f"artifact_{artifact_name}"

            # Producers -> Artifact
            for producer in artifact.producers:
                if producer in self.phases:
                    dot.edge(
                        f"phase_{producer}",
                        artifact_node,
                        label="produces",
                        color="green",
                    )

            # Artifact -> Consumers
            for consumer in artifact.consumers:
                if consumer in self.phases:
                    dot.edge(
                        artifact_node,
                        f"phase_{consumer}",
                        label="consumed by",
                        color="blue",
                    )

        return dot

    def create_combined_diagram(self, output_format: str = "svg") -> graphviz.Digraph:
        """Create a comprehensive diagram showing both phases and artifacts."""
        dot = graphviz.Digraph(comment="Complete Control Flow")
        dot.attr(rankdir="TB", size="16,12", compound="true")
        dot.attr("node", fontname="Arial")
        dot.attr("edge", fontname="Arial", fontsize="10")

        # Create subgraph for phases
        with dot.subgraph(name="cluster_phases") as phases_cluster:
            phases_cluster.attr(
                label="Execution Phases", style="rounded", bgcolor="#F5F5F5"
            )

            status_colors = {
                "completed": "#90EE90",
                "in_progress": "#FFE4B5",
                "pending": "#E6E6FA",
                "blocked": "#FFB6C1",
                "cancelled": "#D3D3D3",
            }

            for phase_id, phase in self.phases.items():
                color = status_colors.get(phase.status, "#E6E6FA")
                label = f"{phase.name}\\n({phase.status})"
                phases_cluster.node(
                    phase_id,
                    label,
                    shape="box",
                    style="rounded,filled",
                    fillcolor=color,
                )

        # Create subgraph for artifacts
        with dot.subgraph(name="cluster_artifacts") as artifacts_cluster:
            artifacts_cluster.attr(
                label="Data Artifacts", style="rounded", bgcolor="#F0F8FF"
            )

            for artifact_name, artifact in self.artifacts.items():
                label = artifact_name
                artifacts_cluster.node(
                    f"artifact_{artifact_name}",
                    label,
                    shape="diamond",
                    style="filled",
                    fillcolor="#87CEEB",
                )

        # Add dependency edges
        for phase_id, phase in self.phases.items():
            if phase.dependencies:
                for dep in phase.dependencies:
                    if dep in self.phases:
                        dot.edge(dep, phase_id, style="bold", color="red")

        # Add artifact edges
        for artifact_name, artifact in self.artifacts.items():
            artifact_node = f"artifact_{artifact_name}"

            for producer in artifact.producers:
                if producer in self.phases:
                    dot.edge(producer, artifact_node, color="green", style="dashed")

            for consumer in artifact.consumers:
                if consumer in self.phases:
                    dot.edge(artifact_node, consumer, color="blue", style="dashed")

        return dot

    def generate_diagrams(self, output_dir: Path, formats: List[str] = ["svg", "png"]):
        """Generate all diagram types in specified formats."""
        output_dir.mkdir(exist_ok=True)

        # Parse the specification
        self.parse_yaml_spec()

        # Generate phase flow diagram
        phase_diagram = self.create_phase_flow_diagram()
        for fmt in formats:
            phase_diagram.render(output_dir / f"phase_flow", format=fmt, cleanup=True)

        # Generate artifact flow diagram
        artifact_diagram = self.create_artifact_flow_diagram()
        for fmt in formats:
            artifact_diagram.render(
                output_dir / f"artifact_flow", format=fmt, cleanup=True
            )

        # Generate combined diagram
        combined_diagram = self.create_combined_diagram()
        for fmt in formats:
            combined_diagram.render(
                output_dir / f"combined_flow", format=fmt, cleanup=True
            )

        print(f"✅ Generated diagrams in {output_dir}")
        for fmt in formats:
            print(f"   - phase_flow.{fmt}")
            print(f"   - artifact_flow.{fmt}")
            print(f"   - combined_flow.{fmt}")

    def get_graphviz_source(self, diagram_type: str = "combined") -> str:
        """Get the raw Graphviz DOT source code."""
        self.parse_yaml_spec()

        if diagram_type == "phases":
            return self.create_phase_flow_diagram().source
        elif diagram_type == "artifacts":
            return self.create_artifact_flow_diagram().source
        else:
            return self.create_combined_diagram().source


def compare_with_mermaid():
    """Show advantages of Graphviz over Mermaid."""
    print("🎨 Graphviz vs Mermaid Comparison")
    print("=" * 50)
    print()
    print("Graphviz Advantages:")
    print("✅ Better automatic layout algorithms")
    print("✅ Professional publication-quality output")
    print("✅ More output formats (SVG, PNG, PDF, PS, etc.)")
    print("✅ Better handling of complex diagrams")
    print("✅ Subgraph clustering capabilities")
    print("✅ No JavaScript dependency for rendering")
    print("✅ Mature and stable (30+ years of development)")
    print()
    print("Mermaid Advantages:")
    print("• Web-native (JavaScript)")
    print("• Live editing in browsers")
    print("• Simple text-based syntax")
    print()
    print("Recommendation: Use Graphviz for production control flow diagrams")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate control flow diagrams with Graphviz"
    )
    parser.add_argument("spec_file", help="Path to YAML control flow specification")
    parser.add_argument("--output-dir", default="diagrams", help="Output directory")
    parser.add_argument(
        "--formats", nargs="+", default=["svg", "png"], help="Output formats"
    )
    parser.add_argument(
        "--type",
        choices=["phases", "artifacts", "combined"],
        default="combined",
        help="Diagram type",
    )
    parser.add_argument(
        "--show-source", action="store_true", help="Show Graphviz DOT source"
    )
    parser.add_argument(
        "--compare", action="store_true", help="Show comparison with Mermaid"
    )

    args = parser.parse_args()

    if args.compare:
        compare_with_mermaid()
        exit(0)

    visualizer = GraphvizFlowVisualizer(Path(args.spec_file))

    if args.show_source:
        print(visualizer.get_graphviz_source(args.type))
    else:
        visualizer.generate_diagrams(Path(args.output_dir), args.formats)
