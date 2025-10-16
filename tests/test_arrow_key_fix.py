#!/usr/bin/env python3
"""
Test Script: Arrow-Key Bug Fix

This script demonstrates that the UniversalMenu library solves
the "arrow keys don't work in VS Code terminal" bug.

It creates a simple menu that:
1. Works with arrow keys in standard terminals (questionary)
2. Falls back to numbered menu in VS Code terminal
3. Shows terminal detection info

Run this in VS Code integrated terminal to verify the fix!
"""

import sys
from pathlib import Path

# Add library to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from control_flow_engine.libraries.interactive_ui import UniversalMenu


def main():
    print("\n" + "=" * 70)
    print("TESTING: Arrow-Key Bug Fix")
    print("=" * 70)
    
    # Create menu with auto-detection
    menu = UniversalMenu()
    
    # Show terminal info
    print("\n📊 Terminal Detection Results:")
    print("=" * 70)
    menu.print_info()
    
    print("\n🎯 Expected Behavior:")
    print("-" * 70)
    if menu.ui_mode == 'questionary':
        print("✅ Full Terminal Detected")
        print("   - You should see arrow-key navigation")
        print("   - Use ↑↓ arrows to select, Enter to confirm")
    elif menu.ui_mode == 'numbered':
        print("✅ Limited Terminal Detected (VS Code / Limited)")
        print("   - You should see numbered options")
        print("   - Type the number and press Enter")
    else:
        print("✅ Basic Terminal Detected")
        print("   - Simple text input mode")
    print("=" * 70)
    
    # Test 1: Simple menu
    print("\n\n" + "=" * 70)
    print("TEST 1: Simple Menu Selection")
    print("=" * 70)
    
    result = menu.select(
        "What would you like to test?",
        choices=[
            {'name': '🧪 Run more tests', 'value': 'more'},
            {'name': '📋 View terminal info again', 'value': 'info'},
            {'name': '✅ Confirm bug is fixed', 'value': 'confirm'},
            {'name': '🚪 Exit', 'value': 'exit'}
        ]
    )
    
    if result == 'more':
        run_more_tests(menu)
    elif result == 'info':
        menu.print_info()
        input("\nPress Enter to continue...")
    elif result == 'confirm':
        confirm_fix(menu)
    elif result == 'exit':
        print("\n👋 Goodbye!")
        return
    
    # Test 2: Confirmation
    print("\n\n" + "=" * 70)
    print("TEST 2: Confirmation Dialog")
    print("=" * 70)
    
    confirmed = menu.confirm(
        "Does the menu work correctly in VS Code terminal?",
        default=True
    )
    
    if confirmed:
        print("\n✅ Great! The bug is fixed!")
        print("\n📝 What worked:")
        if menu.ui_mode == 'numbered':
            print("   - Numbered menu appeared (no arrow keys needed)")
            print("   - You typed a number to select")
            print("   - This works in VS Code terminal!")
        else:
            print("   - Arrow key navigation worked")
            print("   - questionary mode is functioning")
        
        print("\n🎉 Bug Status: FIXED!")
    else:
        print("\n⚠️  There might still be an issue. Please report:")
        print(f"   - UI Mode: {menu.ui_mode}")
        print(f"   - Terminal: {menu.capabilities.term_type if menu.capabilities else 'unknown'}")
    
    # Final test
    print("\n\n" + "=" * 70)
    print("TEST 3: Text Input")
    print("=" * 70)
    
    feedback = menu.text(
        "Any feedback on the fix? (optional)",
        default="Works great!"
    )
    
    print(f"\n💬 Feedback: {feedback}")
    
    print("\n\n" + "=" * 70)
    print("TESTS COMPLETE")
    print("=" * 70)
    print("\n✅ If you could see and interact with the menus, the bug is fixed!")
    print("✅ The same code works in both VS Code AND standard terminals!")
    print("\n")


def run_more_tests(menu: UniversalMenu):
    """Run additional tests."""
    print("\n" + "=" * 70)
    print("ADDITIONAL TESTS")
    print("=" * 70)
    
    # Test nested menus
    print("\nTest: Nested Menu Navigation")
    
    while True:
        choice = menu.select(
            "Nested Menu - Choose an option:",
            choices=[
                {'name': '1️⃣  First option', 'value': '1'},
                {'name': '2️⃣  Second option', 'value': '2'},
                {'name': '3️⃣  Third option', 'value': '3'},
                {'name': '⬅️  Back to main tests', 'value': 'back'}
            ]
        )
        
        if choice == 'back':
            break
        else:
            print(f"\n✅ Selected: {choice}")
            again = menu.confirm("Try another option?", default=True)
            if not again:
                break


def confirm_fix(menu: UniversalMenu):
    """Confirm the bug is fixed."""
    print("\n" + "=" * 70)
    print("BUG FIX VERIFICATION")
    print("=" * 70)
    
    print("\n📋 Original Bug Report:")
    print("-" * 70)
    print("Issue: Arrow keys don't work in VS Code terminal")
    print("Impact: Users cannot navigate questionary menus")
    print("Tool: flow-editor.py was unusable in VS Code")
    print("-" * 70)
    
    print("\n🔧 Solution Implemented:")
    print("-" * 70)
    print("Library: UniversalMenu (interactive_ui)")
    print("Feature: Automatic terminal detection")
    print("Fallback: Numbered menus when arrow keys unavailable")
    print("Result: Same code works everywhere!")
    print("-" * 70)
    
    print("\n✅ Verification Questions:")
    
    q1 = menu.confirm(
        "Did you see a menu (either arrows or numbers)?",
        default=True
    )
    
    if not q1:
        print("⚠️  Menu didn't appear. Please check terminal setup.")
        return
    
    q2 = menu.confirm(
        "Were you able to select an option?",
        default=True
    )
    
    if not q2:
        print("⚠️  Selection didn't work. Please report this issue.")
        return
    
    q3 = menu.confirm(
        "Did it work without arrow keys (if in VS Code)?",
        default=True
    )
    
    if q3:
        print("\n" + "=" * 70)
        print("🎉 BUG FIX CONFIRMED!")
        print("=" * 70)
        print("\n✅ The arrow-key bug is FIXED!")
        print("✅ flow-editor will now work in VS Code terminal")
        print("✅ tui-form-designer can use the same fix")
        print("\n")
    else:
        print("\n⚠️  Might need more investigation.")
        print(f"Mode used: {menu.ui_mode}")
    
    input("\nPress Enter to continue...")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted. Goodbye!")
        sys.exit(0)
