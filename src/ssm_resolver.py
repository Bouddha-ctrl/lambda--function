#!/usr/bin/env python3
import json
import logging
import os
import boto3
from typing import Dict

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ssm = boto3.client("ssm")


def _candidate_config_paths():
    """
    Candidate locations for the config file. CI should write the file to project-root config/
    so the first entry (cwd_path) will normally match.
    """
    cwd_path = os.path.join(os.getcwd(), "config", "store_ssm.json")
    module_dir = os.path.dirname(__file__)
    packaged_path = os.path.join(module_dir, "config", "store_ssm.json")
    parent_packaged_path = os.path.normpath(os.path.join(module_dir, "..", "config", "store_ssm.json"))
    var_task_path = "/var/task/config/store_ssm.json"
    opt_path = "/opt/config/store_ssm.json"
    return [cwd_path, packaged_path, parent_packaged_path, var_task_path, opt_path]


def _load_mapping(path: str = None) -> dict:
    """
    Load the mapping JSON from a single config file.
    Expected format:
      {"store_param": "/path/to/ssm-parameter"}
    Raises FileNotFoundError or ValueError on problems.
    """
    candidates = [path] if path else _candidate_config_paths()
    data = None
    for p in candidates:
        if not p:
            continue
        try:
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                logger.info("Loaded store mapping from config file: %s", p)
                break
        except Exception as e:
            logger.debug("Failed reading config file %s: %s", p, e)
            data = None
    if data is None:
        raise FileNotFoundError("No config file found at any of: " + ", ".join([str(x) for x in candidates if x]))
    if not isinstance(data, dict):
        raise ValueError("config must be a JSON object")
    if "store_param" not in data:
        raise ValueError("config must contain 'store_param' key pointing to the SSM parameter name")
    return data


def _get_ssm_parameter_value(name: str) -> str:
    """
    Fetch a single SSM parameter value (WithDecryption=True). Raises on failure.
    """
    try:
        resp = ssm.get_parameter(Name=name, WithDecryption=True)
        return resp["Parameter"]["Value"]
    except Exception as e:
        logger.error("Error fetching SSM parameter %s: %s", name, e)
        raise


def get_store_urls(config_path: str = None) -> Dict[str, str]:
    """
    Public function the application should call.

    - Reads the config mapping (either from config_path or standard candidate paths).
      The mapping must be: {"store_param": "/path/to/one-ssm-param"}

    - Reads that single SSM parameter (WithDecryption=True). The parameter's value
      must be JSON with keys "oil_api" and "exchange_api", e.g.:
        {"oil_api":"https://api.oil/...","exchange_api":"https://api.fx/..."}

    - Returns: {"oil_api": "<url>", "exchange_api": "<url>"}

    Raises FileNotFoundError, ValueError or boto3-related exceptions on error.
    """
    mapping = _load_mapping(config_path)
    store_param = mapping["store_param"]
    logger.info("Resolving store parameter %s from SSM", store_param)
    raw = _get_ssm_parameter_value(store_param)
    try:
        parsed = json.loads(raw)
    except Exception as e:
        logger.error("Failed to parse JSON from SSM parameter %s: %s", store_param, e)
        raise ValueError(f"SSM parameter {store_param} did not contain valid JSON")

    oil_api = parsed.get("oil_api")
    exchange_api = parsed.get("exchange_api")
    if not oil_api or not exchange_api:
        raise ValueError(f"SSM parameter {store_param} JSON must contain both 'oil_api' and 'exchange_api'")

    return {"oil_api": oil_api, "exchange_api": exchange_api}