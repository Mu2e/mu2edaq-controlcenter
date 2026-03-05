"""
config_loader.py - Load and validate the control center YAML configuration.
"""

import os
import yaml
from typing import Any, Dict, List, Optional


DEFAULT_CONFIG: Dict[str, Any] = {
    "title": "Control Center",
    "grid": {"rows": 2, "cols": 2},
    "status_indicators": [
        {"name": "Status", "state": "unknown"},
    ],
    "pages": [],
    "status_server": {"host": "127.0.0.1", "port": 9876},
}


def load_config(path: str) -> Dict[str, Any]:
    """Load configuration from a YAML file, merging with defaults."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Configuration file not found: {path}")

    with open(path, "r") as fh:
        user_cfg = yaml.safe_load(fh) or {}

    cfg: Dict[str, Any] = {}
    cfg["title"] = user_cfg.get("title", DEFAULT_CONFIG["title"])
    cfg["grid"] = {**DEFAULT_CONFIG["grid"], **user_cfg.get("grid", {})}

    raw_indicators = user_cfg.get("status_indicators", DEFAULT_CONFIG["status_indicators"])
    cfg["status_indicators"] = _validate_indicators(raw_indicators)

    raw_pages = user_cfg.get("pages", DEFAULT_CONFIG["pages"])
    cfg["pages"] = _validate_pages(raw_pages)

    srv_defaults = DEFAULT_CONFIG["status_server"]
    cfg["status_server"] = {**srv_defaults, **user_cfg.get("status_server", {})}

    return cfg


def _validate_indicators(raw: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    valid_states = {"ok", "warning", "error", "unknown"}
    result = []
    for item in raw:
        name = str(item.get("name", "Indicator"))
        state = str(item.get("state", "unknown")).lower()
        if state not in valid_states:
            state = "unknown"
        result.append({"name": name, "state": state})
    return result


def _validate_pages(raw: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    result = []
    auto_idx = 0
    for item in raw:
        name = str(item.get("name", f"Page {auto_idx + 1}"))
        url = str(item.get("url", "about:blank"))
        pos = item.get("position")
        if isinstance(pos, (list, tuple)) and len(pos) == 2:
            position: Optional[List[int]] = [int(pos[0]), int(pos[1])]
        else:
            position = None
        result.append({"name": name, "url": url, "position": position})
        auto_idx += 1
    return result
