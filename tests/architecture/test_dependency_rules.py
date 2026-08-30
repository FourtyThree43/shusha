"""Architecture boundary and dependency direction validation tests."""

from __future__ import annotations

import ast
from pathlib import Path


def _find_imports(file_path: Path) -> list[str]:
    """Extract all imported module names from a Python source file."""
    imports: list[str] = []
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
    except Exception:
        return imports

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return imports


def test_core_domain_has_no_ui_or_backend_dependencies() -> None:
    """Validate that domain core does not import UI or concrete backends."""
    root = Path(__file__).parent.parent.parent
    domain_dir = root / "src" / "shusha" / "domain"
    if not domain_dir.exists():
        return

    forbidden_patterns = [
        "ttkbootstrap",
        "tkinter",
        "textual",
        "shusha.views",
        "shusha.presentation",
        "shusha.infrastructure.aria2",
    ]

    for py_file in domain_dir.glob("**/*.py"):
        imports = _find_imports(py_file)
        for imp in imports:
            for forbidden in forbidden_patterns:
                assert not imp.startswith(forbidden), (
                    f"Forbidden import '{imp}' found in domain entity {py_file.name}"
                )
