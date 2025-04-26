"""
Simple test runner that generates Markdown-friendly output.

This script runs all tests in the UnitTests directory and generates
a formatted report that can be directly pasted into documentation tools.
"""

import unittest
import os
import sys
import datetime
import time

def run_tests():
    """Run all test files from UnitTests directory and return the test result object."""
    # Determine the test directory relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Specifically target the UnitTests directory
    test_dir = os.path.join(script_dir, 'UnitTests')
    
    if not os.path.exists(test_dir):
        print(f"ERROR: UnitTests directory not found at {test_dir}")
        return unittest.TestResult(), 0
    
    # Import ezdxf before running tests to avoid import errors
    try:
        import ezdxf
        print(f"Successfully imported ezdxf version {ezdxf.__version__}")
    except ImportError:
        print("WARNING: ezdxf module not found. DXF tests may fail.")
    
    # Find and load all test modules in the UnitTests directory only
    test_suite = unittest.defaultTestLoader.discover(
        test_dir, pattern='test_*.py'
    )
    
    # Run the tests
    start_time = time.time()
    result = unittest.TextTestRunner(verbosity=2).run(test_suite)
    run_time = time.time() - start_time
    
    return result, run_time

def generate_markdown_report(result, run_time):
    """Generate a report in Markdown format."""
    now = datetime.datetime.now()
    
    # Count tests by file
    test_files = {}
    
    # Process failures
    for test, _ in result.failures:
        test_name = test.id().split('.')
        file_name = test_name[0]
        if file_name not in test_files:
            test_files[file_name] = {'total': 0, 'failed': 0}
        test_files[file_name]['total'] += 1
        test_files[file_name]['failed'] += 1
    
    # Process errors
    for test, _ in result.errors:
        test_name = test.id().split('.')
        file_name = test_name[0]
        if file_name not in test_files:
            test_files[file_name] = {'total': 0, 'failed': 0}
        test_files[file_name]['total'] += 1
        test_files[file_name]['failed'] += 1
    
    # We need to account for total number of tests
    # Since we have the total testsRun count but not individual successful tests,
    # we'll estimate total counts for each file
    
    total_failures_and_errors = sum(info['total'] for info in test_files.values())
    
    # If we have any test files from failures/errors
    if test_files and total_failures_and_errors < result.testsRun:
        # Add successful tests to first file or create a placeholder
        # This is an approximation since we don't have the actual successful test details
        if test_files:
            first_file = next(iter(test_files))
            test_files[first_file]['total'] += (result.testsRun - total_failures_and_errors)
        else:
            test_files['tests'] = {'total': result.testsRun, 'failed': 0}
    
    # Generate report
    report = f"""
### Test Results - {now.strftime('%Y-%m-%d %H:%M')}

#### Summary

| Metric | Value |
|--------|-------|
| Status | {'**FAILED**' if result.failures or result.errors else 'PASSED'} |
| Tests Run | {result.testsRun} |
| Failures | {len(result.failures)} |
| Errors | {len(result.errors)} |
| Time | {run_time:.2f} seconds |

"""
    
    # Only show the file table if we have test file data
    if test_files:
        report += "## Results by Test File\n\n"
        report += "| Test File | Status | Pass/Total |\n"
        report += "|-----------|--------|------------|\n"
        
        for file_name, counts in test_files.items():
            passed = counts['total'] - counts['failed']
            status = "PASSED" if passed == counts['total'] else "FAILED"
            report += f"| {file_name} | {status} | {passed}/{counts['total']} |\n"
    
    if result.failures or result.errors:
        report += "\n## Failures and Errors\n\n"
        
        if result.failures:
            report += "### Failures\n\n"
            for failure in result.failures:
                report += f"#### {failure[0].id()}\n"
                report += "```\n"
                report += str(failure[1])
                report += "\n```\n\n"
        
        if result.errors:
            report += "### Errors\n\n"
            for error in result.errors:
                report += f"#### {error[0].id()}\n"
                report += "```\n"
                report += str(error[1])
                report += "\n```\n\n"
    
    return report

def main():
    """Run tests and generate report."""
    result, run_time = run_tests()
    report = generate_markdown_report(result, run_time)
    
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
