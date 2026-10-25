import os
import sys
import importlib.util

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, 'backend')
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

backend_config_path = os.path.join(BACKEND_DIR, 'config.py')
spec = importlib.util.spec_from_file_location("backend_config", backend_config_path)
backend_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backend_config)

Config = backend_config.Config
