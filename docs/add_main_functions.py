#!/usr/bin/env python3
"""
Add main() function to phase orchestrators and step files.
Makes all files runnable standalone for testing.
"""

import sys
from pathlib import Path
import re

# Phase orchestrator template
PHASE_MAIN_TEMPLATE = '''

def main():
    """Standalone entry point for testing {phase_name}."""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="{phase_description}")
    parser.add_argument('--output-dir', help='Output directory for results', default='{default_output}')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    {extra_args}
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Setup paths
    project_root = Path(__file__).parent.parent.parent
    
    # Create phase instance
    phase = {phase_class}(project_root=project_root)
    
    try:
        # Build context from CLI args
        context = {{}}
        {context_setup}
        
        # Execute phase
        result = phase.execute(context)
        
        print("\\n" + "=" * 70)
        print("✅ {phase_name} COMPLETE")
        print("=" * 70)
        print(f"\\n📊 Results:")
        for key, value in result.items():
            if isinstance(value, (str, int, bool)):
                print(f"  • {{key}}: {{value}}")
        print("\\n✅ Ready for next phase")
        
        return 0
        
    except Exception as e:
        print(f"\\n❌ {phase_name} failed: {{e}}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
'''

# Step main template
STEP_MAIN_TEMPLATE = '''

def main():
    """Standalone entry point for testing this step."""
    import argparse
    import sys
    import json
    
    parser = argparse.ArgumentParser(description="{step_description}")
    {step_args}
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Setup paths
    phase_dir = Path(__file__).parent.parent
    
    try:
        # Build context from CLI args
        context = {{}}
        {context_setup}
        
        # Execute step
        result = {execute_func}(context, phase_dir)
        
        print("\\n" + "=" * 70)
        print(f"✅ Step completed: {{result.get('status', 'unknown')}}")
        print("=" * 70)
        print(f"\\n📊 Results:")
        for key, value in result.items():
            if key not in ['step', 'status'] and isinstance(value, (str, int, bool)):
                print(f"  • {{key}}: {{value}}")
        
        return 0
        
    except Exception as e:
        print(f"\\n❌ Step failed: {{e}}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
'''

def add_imports_fix(file_path: Path):
    """Add conditional import handling for __main__ execution."""
    content = file_path.read_text()
    
    # Check if already has the fix
    if "if __name__ == '__main__':" in content and "sys.path.insert" in content:
        return False  # Already fixed
    
    # Find relative imports
    relative_imports = re.findall(r'from \.([\w.]+) import ([\w, ]+)', content)
    
    if not relative_imports:
        return False  # No relative imports to fix
    
    # Build the import fix
    import_section_start = content.find('from pathlib import Path')
    if import_section_start == -1:
        return False
    
    # Find where imports end
    lines = content.split('\\n')
    import_end_line = 0
    for i, line in enumerate(lines):
        if line.startswith('from') or line.startswith('import'):
            import_end_line = i
    
    # Create conditional imports
    standard_imports = []
    conditional_imports = []
    
    for line in lines[:import_end_line + 1]:
        if line.startswith('from .'):
            # Convert to conditional
            module_path = re.search(r'from \\.([\\.\\w]+) import', line)
            if module_path:
                rel_path = module_path.group(1)
                # Get phase name from file path
                phase_name = str(file_path.parent.name)
                abs_import = line.replace('from .', f'from phases.{phase_name}.')
                conditional_imports.append(f"    {abs_import}")
        elif line.startswith(('from', 'import')):
            standard_imports.append(line)
    
    # Build new import section
    new_imports = '\\n'.join(standard_imports)
    new_imports += "\\nimport sys\\n\\n"
    new_imports += "# Handle both relative imports (when called by parent) and absolute imports (when run standalone)\\n"
    new_imports += "if __name__ == '__main__':\\n"
    new_imports += "    # Running standalone - use absolute imports\\n"
    new_imports += "    sys.path.insert(0, str(Path(__file__).parent.parent.parent))\\n"
    new_imports += '\\n'.join(conditional_imports) + "\\n"
    new_imports += "else:\\n"
    new_imports += "    # Running as module - use relative imports\\n"
    
    for line in lines[:import_end_line + 1]:
        if line.startswith('from .'):
            new_imports += f"    {line}\\n"
    
    return new_imports

print("This script provides templates for adding main() functions.")
print("Apply manually to each file based on its specific needs.")
