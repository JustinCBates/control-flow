#!/usr/bin/env python3
"""
Demo: Interactive UI Library with Terminal Compatibility

Demonstrates the UniversalMenu system that solves the
"arrow keys don't work in VS Code terminal" bug.

This demo works in:
- Standard terminals (uses questionary with arrow keys)
- VS Code integrated terminal (uses numbered menus)
- Limited terminals (uses numbered menus)
- Non-TTY environments (uses basic input)
"""

import sys
from pathlib import Path

# Add library to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from control_flow_engine.libraries.interactive_ui import UniversalMenu, TerminalCapabilities


def demo_terminal_detection():
    """Demo 1: Terminal Capability Detection"""
    print("\n" + "=" * 70)
    print("DEMO 1: Terminal Capability Detection")
    print("=" * 70)
    
    caps = TerminalCapabilities()
    print(f"\nDetected Capabilities:")
    print(f"  Terminal Type: {caps.term_type}")
    print(f"  Terminal Program: {caps.term_program}")
    print(f"  Is VS Code: {caps.is_vscode}")
    print(f"  Is TTY: {caps.is_tty}")
    print(f"  Has Questionary: {caps.has_questionary}")
    print(f"  Supports Arrow Keys: {caps.supports_arrow_keys}")
    print(f"  Recommended UI Mode: {caps.get_ui_mode()}")
    print(f"\n  {caps}")
    
    input("\nPress Enter to continue...")


def demo_simple_menu():
    """Demo 2: Simple Menu Selection"""
    print("\n" + "=" * 70)
    print("DEMO 2: Simple Menu Selection")
    print("=" * 70)
    
    menu = UniversalMenu()
    
    print(f"\nUsing UI Mode: {menu.ui_mode}")
    print("(Automatically adapts to your terminal)\n")
    
    result = menu.select(
        "What is your favorite programming language?",
        choices=[
            {'name': '🐍 Python', 'value': 'python'},
            {'name': '🦀 Rust', 'value': 'rust'},
            {'name': '📜 JavaScript', 'value': 'javascript'},
            {'name': '☕ Java', 'value': 'java'},
            {'name': '💎 Ruby', 'value': 'ruby'}
        ]
    )
    
    if result:
        print(f"\n✅ You selected: {result}")
    else:
        print("\n❌ Selection cancelled")
    
    input("\nPress Enter to continue...")


def demo_confirmation():
    """Demo 3: Confirmation Dialog"""
    print("\n" + "=" * 70)
    print("DEMO 3: Confirmation Dialog")
    print("=" * 70)
    
    menu = UniversalMenu()
    
    confirmed = menu.confirm(
        "Do you want to continue?",
        default=True
    )
    
    if confirmed:
        print("\n✅ Confirmed!")
    else:
        print("\n❌ Not confirmed")
    
    input("\nPress Enter to continue...")


def demo_text_input():
    """Demo 4: Text Input with Validation"""
    print("\n" + "=" * 70)
    print("DEMO 4: Text Input with Validation")
    print("=" * 70)
    
    menu = UniversalMenu()
    
    # Simple text input
    name = menu.text(
        "Enter your name",
        default="User"
    )
    print(f"\n✅ Hello, {name}!")
    
    # Text input with validation
    age = menu.text(
        "Enter your age (must be a number)",
        validate=lambda x: x.isdigit() or "Must be a number"
    )
    print(f"✅ Age: {age}")
    
    input("\nPress Enter to continue...")


def demo_nested_menus():
    """Demo 5: Nested Menu Navigation"""
    print("\n" + "=" * 70)
    print("DEMO 5: Nested Menu Navigation")
    print("=" * 70)
    
    menu = UniversalMenu()
    
    while True:
        action = menu.select(
            "Main Menu - Choose an action:",
            choices=[
                {'name': '📋 View Options', 'value': 'view'},
                {'name': '➕ Add Item', 'value': 'add'},
                {'name': '🗑️  Delete Item', 'value': 'delete'},
                {'name': '⚙️  Settings', 'value': 'settings'},
                {'name': '🚪 Exit', 'value': 'exit'}
            ]
        )
        
        if not action or action == 'exit':
            print("\n👋 Goodbye!")
            break
        
        if action == 'view':
            print("\n📋 Viewing options...")
            input("Press Enter to continue...")
        
        elif action == 'add':
            item_name = menu.text("Enter item name:")
            if item_name:
                print(f"\n✅ Added: {item_name}")
            input("Press Enter to continue...")
        
        elif action == 'delete':
            confirm = menu.confirm("Are you sure you want to delete?", default=False)
            if confirm:
                print("\n✅ Deleted!")
            else:
                print("\n❌ Cancelled")
            input("Press Enter to continue...")
        
        elif action == 'settings':
            setting = menu.select(
                "Settings - Choose option:",
                choices=[
                    {'name': '🎨 Theme', 'value': 'theme'},
                    {'name': '🔔 Notifications', 'value': 'notifications'},
                    {'name': '⬅️  Back', 'value': 'back'}
                ]
            )
            if setting and setting != 'back':
                print(f"\n⚙️  Configuring: {setting}")
            input("Press Enter to continue...")


def demo_mode_comparison():
    """Demo 6: Compare Different Modes"""
    print("\n" + "=" * 70)
    print("DEMO 6: Mode Comparison")
    print("=" * 70)
    
    print("\nThis demo shows how the same code works in different modes.")
    
    # Try numbered mode
    print("\n--- Numbered Mode ---")
    numbered_menu = UniversalMenu(force_mode='numbered')
    result1 = numbered_menu.select(
        "Choose a color:",
        choices=[
            {'name': '🔴 Red', 'value': 'red'},
            {'name': '🟢 Green', 'value': 'green'},
            {'name': '🔵 Blue', 'value': 'blue'}
        ]
    )
    print(f"Selected: {result1}")
    
    # Try questionary mode (if available)
    caps = TerminalCapabilities()
    if caps.has_questionary:
        print("\n--- Questionary Mode (if your terminal supports it) ---")
        questionary_menu = UniversalMenu(force_mode='questionary')
        try:
            result2 = questionary_menu.select(
                "Choose a color:",
                choices=[
                    {'name': '🔴 Red', 'value': 'red'},
                    {'name': '🟢 Green', 'value': 'green'},
                    {'name': '🔵 Blue', 'value': 'blue'}
                ]
            )
            print(f"Selected: {result2}")
        except Exception as e:
            print(f"Questionary mode failed (expected in limited terminals): {e}")
    
    input("\nPress Enter to continue...")


def main():
    """Run all demos."""
    print("\n" + "=" * 70)
    print("INTERACTIVE UI LIBRARY DEMO")
    print("Solving: 'Arrow Keys Don't Work in VS Code Terminal'")
    print("=" * 70)
    
    demos = [
        ("Terminal Detection", demo_terminal_detection),
        ("Simple Menu", demo_simple_menu),
        ("Confirmation", demo_confirmation),
        ("Text Input", demo_text_input),
        ("Nested Menus", demo_nested_menus),
        ("Mode Comparison", demo_mode_comparison)
    ]
    
    menu = UniversalMenu()
    
    while True:
        print("\n" + "=" * 70)
        print("SELECT A DEMO")
        print("=" * 70)
        
        choices = [{'name': f"{i}. {name}", 'value': i} 
                   for i, (name, _) in enumerate(demos, 1)]
        choices.append({'name': '0. Exit', 'value': 0})
        
        selection = menu.select(
            "Choose a demo to run:",
            choices=choices
        )
        
        if selection == 0 or selection is None:
            print("\n👋 Goodbye!")
            break
        
        if 1 <= selection <= len(demos):
            name, demo_func = demos[selection - 1]
            demo_func()
    
    print("\n" + "=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("✅ Same code works in VS Code terminal AND standard terminals")
    print("✅ Automatic fallback to numbered menus when arrow keys don't work")
    print("✅ Consistent API across different terminal types")
    print("✅ No more 'arrow keys don't work' bug!")
    print("\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted. Goodbye!")
        sys.exit(0)
