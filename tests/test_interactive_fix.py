#!/usr/bin/env python3
"""
Interactive Test: Arrow-Key Bug Fix

Run this script in VS Code integrated terminal to verify the fix works!
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from control_flow_engine.libraries.interactive_ui import UniversalMenu


def main():
    print("\n" + "=" * 70)
    print("🧪 ARROW-KEY BUG FIX TEST")
    print("=" * 70)
    
    menu = UniversalMenu()
    
    # Show detection
    print(f"\n✅ Detected UI Mode: {menu.ui_mode}")
    print(f"✅ VS Code Terminal: {menu.capabilities.is_vscode if menu.capabilities else 'unknown'}")
    
    if menu.ui_mode == 'numbered':
        print("\n📝 You should see NUMBERED menus (1, 2, 3...)")
        print("   This means the arrow-key bug is FIXED for VS Code!")
    else:
        print("\n📝 You should see ARROW-KEY navigation")
        print("   Your terminal supports questionary!")
    
    print("\n" + "=" * 70)
    
    # Test menu
    result = menu.select(
        "Does the menu work?",
        choices=[
            {'name': '✅ Yes, I can see and use it!', 'value': 'yes'},
            {'name': '❌ No, something is wrong', 'value': 'no'},
            {'name': '🚪 Exit test', 'value': 'exit'}
        ]
    )
    
    if result == 'yes':
        print("\n🎉 SUCCESS! The arrow-key bug is FIXED!")
        print("\nWhat worked:")
        print("  ✅ Menu appeared")
        print("  ✅ You could select an option")
        print("  ✅ No arrow keys needed in VS Code terminal")
        
        # Confirmation test
        again = menu.confirm("\nRun another test?", default=False)
        if again:
            test_more(menu)
        
    elif result == 'no':
        print("\n⚠️  Please report this issue:")
        print(f"   Mode: {menu.ui_mode}")
        print(f"   Terminal: {menu.capabilities.term_type if menu.capabilities else 'unknown'}")
    
    print("\n👋 Test complete!\n")


def test_more(menu):
    """Additional tests."""
    print("\n" + "=" * 70)
    print("ADDITIONAL TESTS")
    print("=" * 70)
    
    # Test text input
    name = menu.text("Enter your name (test text input):", default="Tester")
    print(f"\n✅ Text input works! Hello, {name}!")
    
    # Test confirmation
    happy = menu.confirm(f"Are you happy with the fix, {name}?", default=True)
    
    if happy:
        print("\n🎉 Excellent! The bug is fixed!")
    else:
        print("\n📝 Thanks for the feedback!")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Cancelled. Goodbye!")
