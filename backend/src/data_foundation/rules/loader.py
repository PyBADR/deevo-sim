"""Rule spec loader — parse rule specifications from JSON or YAML files.

Supports:
  - Single spec from a file path
  - All specs from a directory (recursive .json and .yaml/.yml)
  - Direct dict input (for programmatic use)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Union

from src.data_foundation.rules.spec import RuleSpec

logger = logging.getLogger(__name__)

# Default specs directory
_SPECS_DIR = Path(__file__).parent / "specs"


def _load_yaml(path: Path) -> dict:
    """Load a YAML file. Raises ImportError if PyYAML is not installed."""
    try:
        import yaml
    except ImportError:
        raise ImportError(
            f"PyYAML is required to load YAML rule specs. "
            f"Install it: pip install pyyaml"
        )
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _load_json(path: Path) -> dict:
    """Load a JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_spec(source: Union[str, Path, Dict]) -> RuleSpec:
    """Load and parse a single rule spec.

    Args:
        source: File path (str/Path) or a dict of spec data.

    Returns:
        Validated RuleSpec.

    Raises:
        FileNotFoundError: If path does not exist.
        ValueError: If spec data is invalid.
        ImportError: If YAML file but PyYAML not installed.
    """
    if isinstance(source, dict):
        return RuleSpec(**source)

    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(f"Rule spec not found: {path}")

    suffix = path.suffix.lower()
    if suffix in (".yaml", ".yml"):
        data = _load_yaml(path)
    elif suffix == ".json":
        data = _load_json(path)
    else:
        raise ValueError(f"Unsupported file type '{suffix}'. Use .json, .yaml, or .yml")

    logger.info("Loaded rule spec from %s: %s", path.name, data.get("rule_id", "?"))
    return RuleSpec(**data)


def load_specs_dir(directory: Union[str, Path, None] = None) -> List[RuleSpec]:
    """Load all rule specs from a directory.

    Args:
        directory: Path to scan. Defaults to the built-in specs/ directory.

    Returns:
        List of validated RuleSpec objects.
        Specs that fail validation are logged and skipped.
    """
    dirpath = Path(directory) if directory else _SPECS_DIR
    if not dirpath.is_dir():
        logger.warning("Specs directory does not exist: %s", dirpath)
        return []

    specs: List[RuleSpec] = []
    errors: List[str] = []

    for path in sorted(dirpath.iterdir()):
        if path.suffix.lower() not in (".json", ".yaml", ".yml"):
            continue
        if path.name.startswith("_") or path.name.startswith("."):
            continue

        try:
            spec = load_spec(path)
            specs.append(spec)
        except Exception as exc:
            msg = f"Failed to load {path.name}: {exc}"
            logger.error(msg)
            errors.append(msg)

    logger.info(
        "Loaded %d rule specs from %s (%d errors)",
        len(specs), dirpath, len(errors),
    )
    return specs
