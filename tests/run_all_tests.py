#!/usr/bin/env python3
"""
Test Runner for Investment Portfolio Tracker
Runs all test suites and provides comprehensive validation
"""

import sys
import os
import unittest
import subprocess
import time

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

def run_test_suite(test_name, test_file, description):
    """Run a specific test suite"""
    print(f"\n{'='*60}")
    print(f"🧪 {test_name}")
    print(f"{'='*60}")
    print(f"📝 {description}")
    print("-" * 60)
    
    try:
        # Run the test file
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✅ Test PASSED")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print("❌ Test FAILED")
            if result.stderr:
                print("Error output:")
                print(result.stderr)
            if result.stdout:
                print("Standard output:")
                print(result.stdout)
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Test TIMED OUT (>120s)")
        return False
    except Exception as e:
        print(f"💥 Test CRASHED: {e}")
        return False

def run_unittest_suite(test_module, description):
    """Run unittest-based test suite"""
    print(f"\n{'='*60}")
    print(f"🔬 {test_module.__name__}")
    print(f"{'='*60}")
    print(f"📝 {description}")
    print("-" * 60)
    
    try:
        # Create test loader and suite
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(test_module)
        
        # Run tests with verbose output
        runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
        result = runner.run(suite)
        
        if result.wasSuccessful():
            print("✅ All unit tests PASSED")
            return True
        else:
            print(f"❌ {len(result.failures)} failures, {len(result.errors)} errors")
            return False
            
    except Exception as e:
        print(f"💥 Unit test suite CRASHED: {e}")
        return False

def main():
    """Main test runner"""
    print("🚀 Investment Portfolio Tracker - Complete Test Suite")
    print("=" * 65)
    print("Running comprehensive validation of all components...")
    
    # Change to tests directory
    test_dir = os.path.dirname(os.path.abspath(__file__))
    original_dir = os.getcwd()
    os.chdir(test_dir)
    
    results = []
    start_time = time.time()
    
    try:
        # Test 1: Backend Unit Tests
        print("\n🔧 BACKEND VALIDATION")
        success = run_test_suite(
            "Backend Functionality Test",
            "test_backend.py",
            "Tests core backend functionality: database, assets, transactions, pricing"
        )
        results.append(("Backend Tests", success))
        
        # Test 2: GUI Import Tests  
        print("\n🎨 GUI VALIDATION")
        success = run_test_suite(
            "GUI Import & Compatibility Test", 
            "test_gui_imports.py",
            "Tests GUI dependencies, imports, and QColor fix validation"
        )
        results.append(("GUI Tests", success))
        
        # Test 3: Comprehensive Integration Test
        print("\n📊 INTEGRATION VALIDATION")
        success = run_test_suite(
            "Comprehensive Portfolio Test",
            "test_comprehensive.py", 
            "Creates realistic portfolio with multi-currency assets and analytics"
        )
        results.append(("Integration Tests", success))
        
        # Test 4: Unit Tests (if available)
        try:
            print("\n🔬 UNIT TEST VALIDATION")
            import test_backend
            success = run_unittest_suite(
                test_backend,
                "Automated unit tests for backend components"
            )
            results.append(("Unit Tests", success))
        except ImportError:
            print("ℹ️  Unit tests not available (normal for demo mode)")
        
    finally:
        os.chdir(original_dir)
    
    # Summary Report
    elapsed_time = time.time() - start_time
    print(f"\n{'='*65}")
    print("📋 TEST SUMMARY REPORT")
    print(f"{'='*65}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"⏱️  Total execution time: {elapsed_time:.1f} seconds")
    print(f"📊 Test suites completed: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {total - passed}")
    print("-" * 65)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:<25} {status}")
    
    # Overall result
    if passed == total:
        print(f"\n🎉 ALL TESTS PASSED! System ready for production use.")
        print("🚀 You can now safely run the GUI application:")
        print("   python demo.py")
        print("   python example/gui/gui.py")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test suite(s) failed. Please review and fix issues.")
        print("🔧 Check dependencies and imports before running the GUI.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
