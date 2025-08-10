#!/usr/bin/env python3
"""
Comprehensive test runner for the Personalized Learning Path Generator backend
"""

import pytest
import sys
import os
import argparse
from pathlib import Path


def run_tests(test_type=None, verbose=False, coverage=False, performance=False):
    """Run tests with various options"""
    # Add the backend directory to Python path
    backend_dir = Path(__file__).parent
    sys.path.insert(0, str(backend_dir))
    
    # Build pytest arguments
    args = []
    
    # Set test directory
    test_dir = backend_dir / 'tests'
    args.append(str(test_dir))
    
    # Verbosity
    if verbose:
        args.extend(['-v', '--tb=short'])
    else:
        args.extend(['-q'])
    
    # Coverage
    if coverage:
        args.extend([
            '--cov=app',
            '--cov-report=html:htmlcov',
            '--cov-report=term-missing',
            '--cov-fail-under=80'
        ])
    
    # Test type filtering
    if test_type:
        if test_type == 'unit':
            args.extend(['-m', 'not integration and not performance'])
        elif test_type == 'integration':
            args.extend(['-m', 'integration'])
        elif test_type == 'performance':
            args.extend(['-m', 'performance'])
        elif test_type == 'api':
            args.extend(['-m', 'api'])
        elif test_type == 'database':
            args.extend(['-m', 'database'])
    
    # Performance tests
    if performance:
        args.extend(['-m', 'performance'])
    
    # Additional pytest options
    args.extend([
        '--strict-markers',
        '--disable-warnings',
        '--color=yes'
    ])
    
    # Run tests
    exit_code = pytest.main(args)
    return exit_code


def run_specific_test_file(test_file, verbose=False):
    """Run a specific test file"""
    backend_dir = Path(__file__).parent
    sys.path.insert(0, str(backend_dir))
    
    test_path = backend_dir / 'tests' / test_file
    if not test_path.exists():
        print(f"Test file not found: {test_path}")
        return 1
    
    args = [str(test_path)]
    if verbose:
        args.extend(['-v', '--tb=short'])
    
    return pytest.main(args)


def run_test_suite_analysis():
    """Analyze test suite coverage and performance"""
    backend_dir = Path(__file__).parent
    test_dir = backend_dir / 'tests'
    
    print("=== Test Suite Analysis ===")
    
    # Count test files
    test_files = list(test_dir.glob('test_*.py'))
    print(f"Total test files: {len(test_files)}")
    
    # Analyze test files
    total_tests = 0
    test_categories = {
        'unit': 0,
        'integration': 0,
        'api': 0,
        'performance': 0,
        'database': 0
    }
    
    for test_file in test_files:
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Count test methods
            test_count = content.count('def test_')
            total_tests += test_count
            
            # Categorize tests
            if 'integration' in test_file.name:
                test_categories['integration'] += test_count
            elif 'performance' in test_file.name:
                test_categories['performance'] += test_count
            elif 'api' in test_file.name:
                test_categories['api'] += test_count
            elif 'database' in test_file.name:
                test_categories['database'] += test_count
            else:
                test_categories['unit'] += test_count
    
    print(f"Total test methods: {total_tests}")
    print("\nTest categories:")
    for category, count in test_categories.items():
        percentage = (count / total_tests * 100) if total_tests > 0 else 0
        print(f"  {category.capitalize()}: {count} ({percentage:.1f}%)")
    
    # List test files
    print(f"\nTest files:")
    for test_file in sorted(test_files):
        print(f"  {test_file.name}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Run backend tests')
    parser.add_argument('--type', choices=['unit', 'integration', 'api', 'database', 'performance'],
                       help='Run specific type of tests')
    parser.add_argument('--file', help='Run specific test file')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    parser.add_argument('--coverage', '-c', action='store_true',
                       help='Run with coverage analysis')
    parser.add_argument('--performance', '-p', action='store_true',
                       help='Include performance tests')
    parser.add_argument('--analyze', '-a', action='store_true',
                       help='Analyze test suite')
    
    args = parser.parse_args()
    
    if args.analyze:
        run_test_suite_analysis()
        return 0
    
    if args.file:
        return run_specific_test_file(args.file, args.verbose)
    
    return run_tests(
        test_type=args.type,
        verbose=args.verbose,
        coverage=args.coverage,
        performance=args.performance
    )


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)