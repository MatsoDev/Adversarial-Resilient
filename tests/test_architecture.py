"""Guard the documented Python layer boundaries without importing runtime services.

This checks static absolute imports (including imports in functions/TYPE_CHECKING),
not dynamic imports or arbitrary filesystem access.
"""

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _forbidden_imports(source: str, forbidden: set[str]) -> list[str]:
    violations = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and not node.level:
            modules = [node.module or ""]
        else:
            continue
        violations.extend(
            f"line {node.lineno}: {module}"
            for module in modules
            if module.split(".")[0] in forbidden
        )
    return violations


@pytest.mark.parametrize(
    "layer, forbidden",
    [
        ("src", {"api", "dashboard", "scripts", "tests"}),
        ("api", {"dashboard"}),
        ("dashboard", {"api"}),
    ],
)
def test_python_layers_follow_dependency_direction(layer, forbidden):
    violations = []
    for path in sorted((ROOT / layer).rglob("*.py")):
        violations.extend(
            f"{path.relative_to(ROOT)}: {error}"
            for error in _forbidden_imports(path.read_text(encoding="utf-8"), forbidden)
        )
    assert not violations, "\n".join(violations)


@pytest.mark.parametrize(
    "source, rejected",
    [
        ("import api.main", True),
        ("import os, dashboard.client as client", True),
        ("from scripts import preprocess", True),
        ("def deferred():\n    from tests.data_fixtures import ember_record", True),
        ("if TYPE_CHECKING:\n    import api", True),
        ("from src.data import load_ember", False),
        ("from . import tabular", False),
        ('message = "from api import main"', False),
    ],
)
def test_boundary_checker_recognizes_imports_not_strings(source, rejected):
    assert bool(_forbidden_imports(source, {"api", "dashboard", "scripts", "tests"})) is rejected
