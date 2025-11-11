import os
import sys
import json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

_config_dir = os.path.join(ROOT, "config")
_config_file = os.path.join(_config_dir, "store_ssm.json")
if not os.path.exists(_config_file):
    try:
        os.makedirs(_config_dir, exist_ok=True)
        # point to a test SSM name; tests should monkeypatch get_ssm_parameter_value
        with open(_config_file, "w", encoding="utf-8") as fh:
            json.dump({"store_param": "/test/store"}, fh)
    except Exception:
        pass