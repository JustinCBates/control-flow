#!/usr/bin/env python3
"""
Control Flow Visualizer - Mermaid Generator
Parses CONTROL_FLOWS_SPEC.md and generates Mermaid diagrams.
"""

import re
import yaml
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class Phase:
    id: str
    name: str
    status: str
    description: str
    artifacts_produced: List[str]
    artifacts_consumed: List[str]


@dataclass
class Artifact:
    name: str
    description: str
    producers: List[str]
    consumers: List[str]
    lifecycle: str


class ControlFlowVisualizer:
    def __init__(self, spec_file: Path):
        self.spec_file = spec_file
        self.phases = {}
        self.artifacts = {}
        
    def parse_spec(self):
        """Parse the CONTROL_FLOWS_SPEC.md file."""
        with open(self.spec_file, 'r') as f:
            content = f.read()
        
        # Extract YAML blocks
        yaml_blocks = re.findall(r'```yaml\n(.*?)\n```', content, re.DOTALL)
        
        for block in yaml_blocks:
            try:
                data = yaml.safe_load(block)
                if isinstance(data, dict):
                    self._parse_yaml_block(data)
            except yaml.YAMLError as e:
                print(f"Error parsing YAML block: {e}")
    
    def _parse_yaml_block(self, data: Dict[str, Any]):
        """Parse individual YAML blocks for phases and artifacts."""
        for key, value in data.items():
            if isinstance(value, dict):
                if 'phases' in value:  # Flow definition
                    self._parse_phases(value['phases'])
                elif 'description' in value and 'producers' in value:  # Artifact
                    self._parse_artifact(key, value)
    
    def _parse_phases(self, phases: List[Dict[str, Any]]):
        """Parse phase definitions."""
        for phase_data in phases:
            phase = Phase(
                id=phase_data.get('phase_id', ''),
                name=phase_data.get('name', ''),
                status=phase_data.get('status', 'NOT_IMPLEMENTED'),
                description=phase_data.get('description', ''),
                artifacts_produced=phase_data.get('artifacts_produced', []),
                artifacts_consumed=phase_data.get('artifacts_consumed', [])
            )
            self.phases[phase.id] = phase
    
    def _parse_artifact(self, name: str, data: Dict[str, Any]):
        """Parse artifact definitions."""
        artifact = Artifact(
            name=name,
            description=data.get('description', ''),
            producers=data.get('producers', []),
            consumers=data.get('consumers', []),
            lifecycle=data.get('lifecycle', 'unknown')
        )
        self.artifacts[name] = artifact
    
    def generate_high_level_flow(self) -> str:
        """Generate high-level Mermaid flowchart."""
        mermaid = ["graph TB"]
        
        # Add phase nodes
        phase_nodes = []
        for phase_id, phase in self.phases.items():
            status_icon = "✅" if phase.status == "IMPLEMENTED" else "⏳"
            node_label = f"{status_icon} {phase.name}"
            mermaid.append(f'    {phase_id.upper()}["{node_label}"]')
            phase_nodes.append(phase_id.upper())
        
        # Add phase connections (linear flow)
        for i in range(len(phase_nodes) - 1):
            mermaid.append(f"    {phase_nodes[i]} --> {phase_nodes[i+1]}")
        
        # Add styling
        mermaid.extend([
            "",
            "    %% Styling",
            "    classDef implemented fill:#c8e6c9,stroke:#4caf50",
            "    classDef pending fill:#fff3e0,stroke:#ff9800",
            ""
        ])
        
        # Apply styles
        implemented = [p_id.upper() for p_id, p in self.phases.items() if p.status == "IMPLEMENTED"]
        pending = [p_id.upper() for p_id, p in self.phases.items() if p.status != "IMPLEMENTED"]
        
        if implemented:
            mermaid.append(f"    class {','.join(implemented)} implemented")
        if pending:
            mermaid.append(f"    class {','.join(pending)} pending")
        
        return "\n".join(mermaid)
    
    def generate_artifact_flow(self) -> str:
        """Generate detailed artifact flow diagram."""
        mermaid = ["graph LR"]
        
        # Add phases
        for phase_id, phase in self.phases.items():
            mermaid.append(f'    {phase_id.upper()}["{phase.name}"]')
        
        # Add artifacts as nodes
        for artifact_name, artifact in self.artifacts.items():
            safe_name = artifact_name.replace('_', '').upper()
            mermaid.append(f'    {safe_name}["{artifact_name}"]')
        
        # Add artifact production relationships
        for phase_id, phase in self.phases.items():
            for artifact in phase.artifacts_produced:
                if artifact in self.artifacts:
                    safe_artifact = artifact.replace('_', '').upper()
                    mermaid.append(f"    {phase_id.upper()} --> |produces| {safe_artifact}")
        
        # Add artifact consumption relationships  
        for phase_id, phase in self.phases.items():
            for artifact in phase.artifacts_consumed:
                if artifact in self.artifacts:
                    safe_artifact = artifact.replace('_', '').upper()
                    mermaid.append(f"    {safe_artifact} --> |consumed by| {phase_id.upper()}")
        
        # Add styling
        mermaid.extend([
            "",
            "    %% Styling",
            "    classDef phase fill:#e3f2fd,stroke:#2196f3",
            "    classDef artifact fill:#f3e5f5,stroke:#9c27b0",
            ""
        ])
        
        # Apply styles
        phase_nodes = [p.upper() for p in self.phases.keys()]
        artifact_nodes = [a.replace('_', '').upper() for a in self.artifacts.keys()]
        
        if phase_nodes:
            mermaid.append(f"    class {','.join(phase_nodes)} phase")
        if artifact_nodes:
            mermaid.append(f"    class {','.join(artifact_nodes)} artifact")
        
        return "\n".join(mermaid)
    
    def generate_state_diagram(self) -> str:
        """Generate state transition diagram."""
        mermaid = ["stateDiagram-v2", "    [*] --> discovery"]
        
        # Add state transitions
        phase_ids = list(self.phases.keys())
        for i in range(len(phase_ids) - 1):
            current = phase_ids[i]
            next_phase = phase_ids[i + 1]
            mermaid.append(f"    {current} --> {next_phase}")
        
        # Add final state
        if phase_ids:
            mermaid.append(f"    {phase_ids[-1]} --> [*]")
        
        # Add state descriptions
        for phase_id, phase in self.phases.items():
            status_icon = "✅" if phase.status == "IMPLEMENTED" else "⏳"
            description = f"{status_icon} {phase.name}<br/>{phase.description[:50]}..."
            mermaid.append(f'    {phase_id}: {description}')
        
        return "\n".join(mermaid)
    
    def generate_all_diagrams(self) -> Dict[str, str]:
        """Generate all diagram types."""
        self.parse_spec()
        
        return {
            "high_level": self.generate_high_level_flow(),
            "artifact_flow": self.generate_artifact_flow(), 
            "state_diagram": self.generate_state_diagram()
        }


def main():
    """Generate Mermaid diagrams from control flow specification."""
    spec_file = Path(__file__).parent / "CONTROL_FLOWS_SPEC.md"
    
    if not spec_file.exists():
        print(f"Error: {spec_file} not found")
        return
    
    visualizer = ControlFlowVisualizer(spec_file)
    diagrams = visualizer.generate_all_diagrams()
    
    # Write diagrams to files
    output_dir = Path(__file__).parent / "generated_diagrams"
    output_dir.mkdir(exist_ok=True)
    
    for diagram_type, content in diagrams.items():
        output_file = output_dir / f"{diagram_type}_flow.mmd"
        with open(output_file, 'w') as f:
            f.write(content)
        print(f"Generated: {output_file}")
    
    # Also create a combined markdown file
    combined_md = output_dir / "control_flow_diagrams.md"
    with open(combined_md, 'w') as f:
        f.write("# Control Flow Diagrams\n\n")
        
        f.write("## High-Level Flow\n")
        f.write("```mermaid\n")
        f.write(diagrams["high_level"])
        f.write("\n```\n\n")
        
        f.write("## Artifact Flow\n")
        f.write("```mermaid\n") 
        f.write(diagrams["artifact_flow"])
        f.write("\n```\n\n")
        
        f.write("## State Transitions\n")
        f.write("```mermaid\n")
        f.write(diagrams["state_diagram"])
        f.write("\n```\n")
    
    print(f"Combined diagrams: {combined_md}")


if __name__ == "__main__":
    main()