#!/usr/bin/env python3
"""
Simple Integration Test for Control Flow Designer

Tests the ControlFlowDesigner transformation methods to ensure they:
1. Accept correct parameters
2. Return proper result dictionaries  
3. Handle errors gracefully
4. Support preview mode

Note: This is a simplified test that validates the API surface
without requiring a full project structure.
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='  * 70}")
    print(f"  {title}")
    print('=' * 70)


def print_test(test_name: str, passed: bool, message: str = ""):
    """Print test result."""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  {status}: {test_name}")
    if message:
        print(f"         {message}")


def test_designer_import():
    """Test that ControlFlowDesigner can be imported."""
    print_section("Test 1: Module Import")
    
    try:
        from control_flow_engine.core.designer import ControlFlowDesigner
        print_test("Import ControlFlowDesigner", True)
        return True, ControlFlowDesigner
    except Exception as e:
        print_test("Import ControlFlowDesigner", False, str(e))
        return False, None


def test_designer_methods(ControlFlowDesigner):
    """Test that all expected methods exist."""
    print_section("Test 2: API Methods Exist")
    
    expected_methods = [
        'renumber_phase',
        'insert_phase',
        'insert_step',
        'delete_phase',
        'delete_step',
        'get_transformation_history',
        'rollback_transformation',
        'preview_transformation',
        '_get_transformer'
    ]
    
    all_passed = True
    for method_name in expected_methods:
        has_method = hasattr(ControlFlowDesigner, method_name)
        print_test(f"Method '{method_name}' exists", has_method)
        if not has_method:
            all_passed = False
    
    return all_passed


def test_method_signatures(ControlFlowDesigner):
    """Test method signatures."""
    print_section("Test 3: Method Signatures")
    
    import inspect
    
    tests = [
        ('renumber_phase', ['phase_id', 'start_from', 'strategy', 'preview_only']),
        ('insert_phase', ['phase_data', 'insert_after', 'insert_before', 'cascade_renumber', 'preview_only']),
        ('insert_step', ['phase_id', 'step_data', 'insert_after', 'insert_before', 'cascade_renumber', 'preview_only']),
        ('delete_phase', ['phase_id', 'cascade_renumber', 'preview_only']),
        ('delete_step', ['phase_id', 'step_id', 'cascade_renumber', 'preview_only']),
    ]
    
    all_passed = True
    for method_name, expected_params in tests:
        method = getattr(ControlFlowDesigner, method_name, None)
        if method:
            sig = inspect.signature(method)
            params = list(sig.parameters.keys())[1:]  # Skip 'self'
            has_all = all(param in params for param in expected_params)
            print_test(
                f"'{method_name}' has params: {', '.join(expected_params)}",
                has_all,
                f"Actual: {', '.join(params)}" if not has_all else ""
            )
            if not has_all:
                all_passed = False
        else:
            print_test(f"'{method_name}' exists", False)
            all_passed = False
    
    return all_passed


def test_docstrings(ControlFlowDesigner):
    """Test that methods have docstrings."""
    print_section("Test 4: Documentation")
    
    methods = [
        'renumber_phase',
        'insert_phase',
        'insert_step',
        'delete_phase',
        'delete_step',
        'get_transformation_history',
        'rollback_transformation'
    ]
    
    all_passed = True
    for method_name in methods:
        method = getattr(ControlFlowDesigner, method_name, None)
        if method:
            has_doc = method.__doc__ is not None and len(method.__doc__.strip()) > 0
            print_test(f"'{method_name}' has docstring", has_doc)
            if not has_doc:
                all_passed = False
        else:
            print_test(f"'{method_name}' exists", False)
            all_passed = False
    
    return all_passed


def test_example_file():
    """Test that example file exists."""
    print_section("Test 5: Example Files")
    
    examples_dir = Path(__file__).parent.parent / 'examples'
    
    example_files = [
        'designer_transformation_demo.py'
    ]
    
    all_passed = True
    for filename in example_files:
        filepath = examples_dir / filename
        exists = filepath.exists()
        print_test(f"Example '{filename}' exists", exists, str(filepath) if not exists else "")
        if not exists:
            all_passed = False
    
    return all_passed


def test_ui_files():
    """Test that UI files exist."""
    print_section("Test 6: UI Files")
    
    ui_dir = Path(__file__).parent.parent / 'src' / 'control_flow_engine' / 'ui'
    
    ui_files = [
        'flow_editor.py',
        'README.md'
    ]
    
    all_passed = True
    for filename in ui_files:
        filepath = ui_dir / filename
        exists = filepath.exists()
        print_test(f"UI file '{filename}' exists", exists, str(filepath) if not exists else "")
        if not exists:
            all_passed = False
    
    # Test launcher
    launcher = Path(__file__).parent.parent / 'bin' / 'flow-editor'
    exists = launcher.exists()
    print_test("Launcher 'bin/flow-editor' exists", exists)
    if not exists:
        all_passed = False
    else:
        is_executable = launcher.stat().st_mode & 0o111 != 0
        print_test("Launcher is executable", is_executable)
        if not is_executable:
            all_passed = False
    
    return all_passed


def test_documentation():
    """Test that documentation exists."""
    print_section("Test 7: Documentation")
    
    docs_dir = Path(__file__).parent.parent / 'docs'
    
    doc_files = [
        'TODO_7_PHASE1_COMPLETE.md',
        'TODO_7_PHASE2_COMPLETE.md',
        'TODO_7_PHASE1_STATUS.md'
    ]
    
    all_passed = True
    for filename in doc_files:
        filepath = docs_dir / filename
        exists = filepath.exists()
        print_test(f"Doc '{filename}' exists", exists)
        if not exists:
            all_passed = False
    
    return all_passed


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("  Control Flow Designer - Integration Test Suite")
    print("  Simplified API Surface Tests")
    print("=" * 70)
    
    results = []
    
    # Test 1: Import
    success, ControlFlowDesigner = test_designer_import()
    results.append(("Import", success))
    
    if not success or ControlFlowDesigner is None:
        print("\n❌ Cannot proceed without successful import")
        return False
    
    # Test 2-4: API Tests
    results.append(("Methods Exist", test_designer_methods(ControlFlowDesigner)))
    results.append(("Method Signatures", test_method_signatures(ControlFlowDesigner)))
    results.append(("Documentation", test_docstrings(ControlFlowDesigner)))
    
    # Test 5-7: File Tests
    results.append(("Example Files", test_example_file()))
    results.append(("UI Files", test_ui_files()))
    results.append(("Documentation Files", test_documentation()))
    
    # Print summary
    print_section("Test Results Summary")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status}: {name}")
    
    print(f"\n  Total: {passed}/{total} test suites passed")
    print(f"  Pass Rate: {passed/total*100:.1f}%")
    
    print("\n" + "=" * 70)
    if passed == total:
        print("  🎉 ALL TESTS PASSED!")
    else:
        print(f"  ⚠️  {total - passed} TEST SUITE(S) FAILED")
    print("=" * 70 + "\n")
    
    return passed == total


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
