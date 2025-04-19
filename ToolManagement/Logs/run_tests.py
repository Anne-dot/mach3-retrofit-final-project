"""
Simple test runner that generates Confluence-friendly output.

This script runs all tests in the UnitTests directory and generates
a formatted report that can be directly pasted into Confluence.
"""

import unittest
import os
import sys
import datetime
import time

def run_tests():
    """Run all test files and return the test result object."""
    # Determine the test directory relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    if os.path.exists(os.path.join(script_dir, 'UnitTests')):
        test_dir = os.path.join(script_dir, 'UnitTests')
    else:
        test_dir = script_dir
    
    # Find and load all test modules
    test_suite = unittest.defaultTestLoader.discover(
        test_dir, pattern='test_*.py'
    )
    
    # Run the tests
    start_time = time.time()
    result = unittest.TextTestRunner(verbosity=2).run(test_suite)
    run_time = time.time() - start_time
    
    return result, run_time

def generate_confluence_report(result, run_time):
    """Generate a report in Confluence-friendly format."""
    now = datetime.datetime.now()
    
    # Count tests by file
    test_files = {}
    for test in result.failures + result.errors:
        test_name = test[0].id().split('.')
        file_name = test_name[0]
        if file_name not in test_files:
            test_files[file_name] = {'total': 0, 'failed': 0}
        test_files[file_name]['total'] += 1
        test_files[file_name]['failed'] += 1
    
    for test in result._tests:
        for test_case in test._tests:
            for tc in getattr(test_case, '_tests', [test_case]):
                test_name = tc.id().split('.')
                if len(test_name) >= 1:
                    file_name = test_name[0]
                    if file_name not in test_files:
                        test_files[file_name] = {'total': 0, 'failed': 0}
                    test_files[file_name]['total'] += 1
    
    # Generate report
    report = f"""
h1. Test Results - {now.strftime('%Y-%m-%d %H:%M')}

h2. Summary

|| Status || {'*FAILED*' if result.failures or result.errors else 'PASSED'} ||
|| Tests Run || {result.testsRun} ||
|| Failures || {len(result.failures)} ||
|| Errors || {len(result.errors)} ||
|| Time || {run_time:.2f} seconds ||

h2. Results by Test File

|| Test File || Status || Pass/Total ||
"""
    
    for file_name, counts in test_files.items():
        passed = counts['total'] - counts['failed']
        status = "✅ PASSED" if passed == counts['total'] else "❌ FAILED"
        report += f"| {file_name} | {status} | {passed}/{counts['total']} |\n"
    
    if result.failures or result.errors:
        report += "\nh2. Failures and Errors\n\n"
        
        if result.failures:
            report += "h3. Failures\n\n"
            for failure in result.failures:
                report += f"h4. {failure[0].id()}\n"
                report += "{{code}}\n"
                report += str(failure[1])
                report += "\n{{code}}\n\n"
        
        if result.errors:
            report += "h3. Errors\n\n"
            for error in result.errors:
                report += f"h4. {error[0].id()}\n"
                report += "{{code}}\n"
                report += str(error[1])
                report += "\n{{code}}\n\n"
    
    return report

def main():
    """Run tests and generate report."""
    result, run_time = run_tests()
    report = generate_confluence_report(result, run_time)
    
    # Print report to console
    print(report)
    
    # Save report to file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(script_dir, '..', 'Logs')
    os.makedirs(log_dir, exist_ok=True)
    
    report_file = os.path.join(
        log_dir, 
        f"test_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.txt"
    )
    
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"\nReport saved to: {report_file}")
    
    # Return exit code based on test result
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(main())
