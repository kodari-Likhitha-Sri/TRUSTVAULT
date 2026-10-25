import os
import sys
import importlib.util

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, 'backend')
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

spec = importlib.util.spec_from_file_location("backend_tests", os.path.join(BACKEND_DIR, "tests_trustvault.py"))
backend_tests = importlib.util.module_from_spec(spec)
sys.modules["backend_tests"] = backend_tests
spec.loader.exec_module(backend_tests)

TrustVaultTestCase = backend_tests.TrustVaultTestCase

if __name__ == '__main__':
    import unittest
    unittest.main()
