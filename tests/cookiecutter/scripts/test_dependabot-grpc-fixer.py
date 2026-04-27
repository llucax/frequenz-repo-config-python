"""Tests for the dependabot_gprc_fixer package."""

import importlib.util
from pathlib import Path
from typing import Protocol, cast

# The script is not intended to be imported as a module, so we load it "dynamically"
# here to test do some unit testing of its internal functions.
FIXER_PATH = (
    Path(__file__).resolve().parents[3]
    / "cookiecutter/scripts/dependabot-grpc-fixer.py"
)


class FixerModule(Protocol):
    """Typing contract for the loaded fixer script."""

    PYPROJECT: Path

    def main(self, pyproject_path: Path = ...) -> None:
        """Run the fixer script."""

    def replace_range(self, text: str, name: str, version: str) -> tuple[str, int]:
        """Update a dependency range."""


def _load_fixer() -> FixerModule:
    """Load the fixer script as a module for direct testing."""
    spec = importlib.util.spec_from_file_location("fixer", FIXER_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError(f"could not load {FIXER_PATH}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return cast(FixerModule, module)


fixer = _load_fixer()
