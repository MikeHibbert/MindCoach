#!/usr/bin/env python3
"""
Test runner for the Personalized Learning Path Generator backend
"""

import unittest
import sys
import os

def run_tests():
    """Run all tests"""
    # Add the backend directory to Python path
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, backend_dir)
    
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = os.path.join(backend_dir, 'tests')
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code based on test results
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    exit_code = run_tests()
    sys.exit(exit_code)