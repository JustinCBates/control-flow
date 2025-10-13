#!/usr/bin/env python3
"""Command-line interface for Control Flow Engine."""

import click
import sys
from pathlib import Path

# Add the src directory to Python path for local development
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from control_flow_engine.core.engine import FlowEngine
    from control_flow_engine.visualizer.mermaid_generator import FlowVisualizer
    from control_flow_engine.analysis.flow_analyzer import FlowAnalyzer
except ImportError as e:
    click.echo(f"❌ Import error: {e}")
    click.echo("💡 Make sure to install the package: pip install -e .")
    sys.exit(1)


@click.group()
@click.version_option(version="0.1.0")
def main():
    """OpenProject Control Flow Engine CLI."""
    pass


@main.command()
@click.argument('spec_file', type=click.Path(exists=True))
def validate(spec_file):
    """Validate a control flow specification."""
    try:
        # For now, just check if file exists and has content
        spec_path = Path(spec_file)
        if spec_path.stat().st_size == 0:
            click.echo("❌ Specification file is empty")
            raise click.Abort()
        
        with open(spec_path, 'r') as f:
            content = f.read()
            if 'main_config_flow' in content or 'flow_id' in content:
                click.echo("✅ Flow specification appears valid")
            else:
                click.echo("⚠️  Warning: No recognizable flow patterns found")
                
    except Exception as e:
        click.echo(f"❌ Validation failed: {e}")
        raise click.Abort()


@main.command()
@click.argument('spec_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output directory')
@click.option('--format', type=click.Choice(['mermaid', 'html', 'all']), default='all')
def visualize(spec_file, output, format):
    """Generate visualizations from flow specification."""
    try:
        # Import and run the existing visualizer
        from control_flow_engine.visualizer.mermaid_generator import ControlFlowVisualizer
        
        spec_path = Path(spec_file)
        output_dir = Path(output) if output else spec_path.parent / "flow_diagrams"
        output_dir.mkdir(exist_ok=True)
        
        visualizer = ControlFlowVisualizer(spec_path)
        
        if format in ['mermaid', 'all']:
            diagrams = visualizer.generate_all_diagrams()
            for name, content in diagrams.items():
                diagram_file = output_dir / f"{name}.mmd"
                diagram_file.write_text(content)
                click.echo(f"📊 Generated: {diagram_file}")
        
        if format in ['html', 'all']:
            # Copy the HTML interface
            html_template = Path(__file__).parent.parent / "visualizer" / "templates" / "interface.html"
            if html_template.exists():
                html_file = output_dir / "visualizer.html"
                import shutil
                shutil.copy2(html_template, html_file)
                click.echo(f"🌐 Generated: {html_file}")
            else:
                click.echo("⚠️  HTML template not found")
        
        click.echo(f"✅ Visualizations generated in: {output_dir}")
        
    except Exception as e:
        click.echo(f"❌ Visualization failed: {e}")
        raise click.Abort()


@main.command()
@click.argument('spec_file', type=click.Path(exists=True))
@click.option('--port', '-p', default=8000, help='Port for web server')
def serve(spec_file, port):
    """Serve interactive flow visualizer."""
    try:
        # Use the existing web server
        from control_flow_engine.visualizer.web_server import main as serve_main
        import sys
        
        # Temporarily override sys.argv for the server
        original_argv = sys.argv
        sys.argv = ['serve_visualizer.py']
        
        click.echo(f"🌐 Starting visualizer server for: {spec_file}")
        click.echo(f"📍 Server will run on: http://localhost:{port}")
        
        # Import and modify the server to use our spec file
        serve_main()
        
    except Exception as e:
        click.echo(f"❌ Server failed to start: {e}")
        raise click.Abort()
    finally:
        sys.argv = original_argv


@main.command()
@click.argument('spec_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Analysis report file')
def analyze(spec_file, output):
    """Analyze flow complexity and dependencies."""
    try:
        spec_path = Path(spec_file)
        
        # Basic analysis for now
        with open(spec_path, 'r') as f:
            content = f.read()
        
        # Count basic metrics
        phases = content.count('phase_id:')
        artifacts = content.count('artifacts_produced:') + content.count('artifacts_consumed:')
        flows = content.count('flow_id:')
        
        report = {
            "file": str(spec_path),
            "summary": {
                "total_phases": phases,
                "total_artifacts": artifacts,
                "total_flows": flows,
                "file_size": spec_path.stat().st_size,
                "complexity_score": phases + artifacts * 0.5 + flows * 2
            }
        }
        
        if output:
            import json
            with open(output, 'w') as f:
                json.dump(report, f, indent=2)
            click.echo(f"📋 Analysis report saved: {output}")
        else:
            click.echo("📋 Flow Analysis Report:")
            click.echo(f"  File: {spec_path}")
            click.echo(f"  Phases: {report['summary']['total_phases']}")
            click.echo(f"  Artifacts: {report['summary']['total_artifacts']}")
            click.echo(f"  Flows: {report['summary']['total_flows']}")
            click.echo(f"  Complexity Score: {report['summary']['complexity_score']:.1f}")
        
    except Exception as e:
        click.echo(f"❌ Analysis failed: {e}")
        raise click.Abort()


@main.command()
def info():
    """Show engine information and status."""
    click.echo("🔄 OpenProject Control Flow Engine v0.1.0")
    click.echo("📍 Location: external/control-flow/")
    click.echo("🎯 Purpose: Unified control flow management and visualization")
    click.echo("")
    click.echo("Available commands:")
    click.echo("  validate  - Validate flow specifications")
    click.echo("  visualize - Generate diagrams and visualizations")
    click.echo("  serve     - Start interactive web interface")
    click.echo("  analyze   - Analyze flow complexity")
    click.echo("  info      - Show this information")


if __name__ == "__main__":
    main()