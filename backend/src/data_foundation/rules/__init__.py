"""Rule Specification Layer for Impact Observatory.

Declarative, auditable rule definitions that compile into DecisionRuleORM
objects for the existing decision engine.

Modules:
  spec       — RuleSpec Pydantic schema
  loader     — Parse rule specs from JSON or YAML files
  validator  — Validate specs against indicator catalog + source registry
  compiler   — Compile validated specs into DecisionRuleORM rows
"""

from src.data_foundation.rules.spec import RuleSpec, ConditionSpec  # noqa: F401
from src.data_foundation.rules.loader import load_spec, load_specs_dir  # noqa: F401
from src.data_foundation.rules.validator import validate_spec, validate_all  # noqa: F401
from src.data_foundation.rules.compiler import compile_spec  # noqa: F401
