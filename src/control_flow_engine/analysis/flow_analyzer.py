#!/usr/bin/env python3
"""
Simple Control Flow Tracker for Config Manager
Demonstrates the control flow tracking system before system-wide implementation.
"""

import os
import re
import yaml
from pathlib import Path
from typing import Dict, List, Set, Optional, Any


class ControlFlowAnalyzer:
    """Analyze and validate control flows for a single component."""

    def __init__(self, component_path: str):
        self.component_path = Path(component_path)
        self.control_flows_file = (
            self.component_path / "design_specs" / "control_flows.yml"
        )

    def parse_control_flows(self) -> Dict[str, Any]:
        """Parse the control_flows.yml file and extract structured data."""
        if not self.control_flows_file.exists():
            print(f"❌ No control_flows.yml found at {self.control_flows_file}")
            return {}

        try:
            with open(self.control_flows_file) as f:
                data = yaml.safe_load(f)

            if not data:
                print(f"❌ Empty or invalid YAML in {self.control_flows_file}")
                return {}

            return data

        except yaml.YAMLError as e:
            print(f"❌ Error parsing YAML file {self.control_flows_file}: {e}")
            return {}
        except Exception as e:
            print(f"❌ Error reading file {self.control_flows_file}: {e}")
            return {}

    def validate_flows(self) -> bool:
        """Validate that control flows make sense."""
        data = self.parse_control_flows()

        if not data:
            return False

        valid = True

        # Check that we have component info
        if "component" not in data:
            print("⚠️  No component information defined")
            valid = False

        # Check that we have at least one entry point
        if "entry_points" not in data or not data["entry_points"]:
            print("⚠️  No entry points defined")
            valid = False

        # Check that we have some flows
        if "flows" not in data or not data["flows"]:
            print("⚠️  No flows defined")
            valid = False

        return valid

    def generate_summary(self) -> str:
        """Generate a summary of the control flows."""
        data = self.parse_control_flows()

        if not data:
            return "❌ No control flows found"

        component = data.get("component", {})
        entry_points = data.get("entry_points", {})
        flows = data.get("flows", {})

        summary = (
            f"# Control Flow Summary: {component.get('name', 'Unknown Component')}\n\n"
        )

        if "description" in component:
            summary += f"**Description:** {component['description']}\n\n"

        summary += f"## Entry Points ({len(entry_points)})\n"
        for name, info in entry_points.items():
            status = info.get("status", "UNKNOWN")
            desc = info.get("description", "No description")
            summary += f"- **{name}** ({status}): {desc}\n"
        summary += "\n"

        summary += f"## Flows ({len(flows)})\n"
        for flow_name, flow_info in flows.items():
            desc = flow_info.get("description", "No description")
            steps = flow_info.get("steps", flow_info.get("phases", []))
            summary += f"- **{flow_name}**: {desc} ({len(steps)} steps)\n"
        summary += "\n"

        # Show implementation status
        impl_status = data.get("implementation_status", {})
        if impl_status:
            overall = impl_status.get("overall", "UNKNOWN")
            summary += f"## Implementation Status\n"
            summary += f"- **Overall:** {overall}\n"
            if "last_updated" in impl_status:
                summary += f"- **Last Updated:** {impl_status['last_updated']}\n"
            if "notes" in impl_status:
                summary += f"- **Notes:** {impl_status['notes']}\n"

        return summary

    def check_code_alignment(self) -> List[str]:
        """Check if control flows align with actual code structure."""
        issues = []
        flows = self.parse_control_flows()

        # Look for main.py and check CLI commands
        main_py = self.component_path / "src" / "openproject_config_manager" / "main.py"
        if main_py.exists():
            with open(main_py) as f:
                main_content = f.read()

            # Check for CLI commands
            cli_commands = re.findall(
                r"@cli\.command\(\)\s*[^def]*def\s+(\w+)", main_content
            )

            documented_entries = [
                entry.split("`")[1].split("(")[0]
                for entry in flows["entry_points"]
                if "`" in entry
            ]

            for cmd in cli_commands:
                if cmd not in documented_entries:
                    issues.append(
                        f"CLI command '{cmd}' not documented in control flows"
                    )

            for entry in documented_entries:
                if entry not in cli_commands and entry not in [
                    "cli",
                    "ConfigurationManager",
                    "run_full_process",
                ]:
                    issues.append(f"Documented entry point '{entry}' not found in code")

        return issues


def main():
    """Demo the control flow analyzer for config-manager."""
    print("🔍 Control Flow Analyzer - Config Manager Demo")
    print("=" * 50)

    config_manager_path = "/opt/openproject/external/config-manager"
    analyzer = ControlFlowAnalyzer(config_manager_path)

    # Check if control flows file exists
    if not analyzer.control_flows_file.exists():
        print(f"❌ CONTROL_FLOWS.md not found at {analyzer.control_flows_file}")
        return

    print(f"✅ Found CONTROL_FLOWS.md")

    # Validate flows
    print("\n📋 Validating Control Flows...")
    is_valid = analyzer.validate_flows()
    if is_valid:
        print("✅ Control flows validation passed")
    else:
        print("❌ Control flows validation failed")

    # Check code alignment
    print("\n🔍 Checking Code Alignment...")
    issues = analyzer.check_code_alignment()
    if not issues:
        print("✅ Control flows align with code structure")
    else:
        print("⚠️  Found alignment issues:")
        for issue in issues:
            print(f"   - {issue}")

    # Generate summary
    print("\n📊 Control Flow Summary:")
    print("-" * 30)
    summary = analyzer.generate_summary()
    print(summary)


if __name__ == "__main__":
    main()
