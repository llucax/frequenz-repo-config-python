"""Fix grpc/protobuf dependency bounds in `pyproject.toml` after Dependabot.

Dependabot's grouped updates for `grpcio*`/`protobuf` leave Frequenz API
repositories in an inconsistent state. These repositories split the gRPC and
protobuf dependencies in two parts:

* A *build-time* part (`grpcio-tools`, `mypy-protobuf`, etc.) that is used
  to generate Python bindings from the `.proto` files. Dependabot tracks and
  bumps these because they are pinned in `pyproject.toml`.
* A *runtime* part (`grpcio`, `protobuf`) expressed as a *range* that
  consumers of the generated bindings must satisfy. The lower bound must be
  no greater than the build-time pin (otherwise the bindings would be built
  against an unsupported version), and the upper bound encodes the
  compatibility window we are willing to support.

Dependabot only knows how to bump the build-time pins. After such an update
the runtime ranges are stale and consumers can end up resolving runtime
versions that are *older* than the version the bindings were generated with.

On top of that, `protobuf`'s compatibility guarantees span two consecutive
major versions, while `grpcio` only guarantees one. The upper bound of each
runtime range encodes that contract, and there is a trailing
`# Do not widen beyond N!` comment that mirrors the upper bound to make the
intent explicit (and to provide an additional anchor for this script).

This script reads the JSON metadata that the `dependabot/fetch-metadata`
GitHub Action writes to `UPDATED_DEPENDENCIES_JSON`, finds the new
build-time versions for `grpcio`/`protobuf`, and rewrites the runtime
ranges in `pyproject.toml` accordingly:

* The lower bound becomes the new build-time version.
* The upper bound becomes `new_major + offset` where `offset` is `1` for
  `grpcio` and `2` for `protobuf`.
* The `# Do not widen beyond N!` comment is updated to match.
"""

import argparse
import json
import os
import re
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn

PYPROJECT = Path("pyproject.toml")
"""Default path to the `pyproject.toml` file to update."""

METADATA_ENV_VAR = "UPDATED_DEPENDENCIES_JSON"
"""Environment variable populated by `dependabot/fetch-metadata`."""

TRACKED_DEPS = ("protobuf", "grpcio-tools", "grpcio")
"""Dependency names this script consumes from the Dependabot metadata.

`grpcio-tools` is included so the Dependabot payload is accepted even when
only the build-time package was bumped; the runtime `grpcio` floor is then
synced from the same version because they are kept in lockstep.
"""

RUNTIME_DEPS = ("protobuf", "grpcio")
"""Runtime dependencies whose range is rewritten in `pyproject.toml`."""

UPPER_BOUND_OFFSETS = {
    "protobuf": 2,
    "grpcio": 1,
}
"""How many major versions past the new floor each runtime range may span.

`protobuf` guarantees compatibility across two consecutive majors; `grpcio`
only across one.
"""


@dataclass(frozen=True, kw_only=True)
class DependencyUpdate:
    """A single Dependabot-reported dependency version update."""

    name: str
    """Dependency name (e.g. `"protobuf"`)."""

    new_version: str
    """The new version Dependabot wants to pin (e.g. `"6.32.1"`)."""


def fail(message: str) -> NoReturn:
    """Report an error and exit immediately."""
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def major(version: str) -> int:
    """Return the major version number extracted from a version string."""
    match = re.match(r"v?(\d+)", version.strip())
    if match is None:
        fail(f"could not parse a major version from {version!r}")
    return int(match.group(1))


def parse_dependabot_metadata(raw: str) -> list[DependencyUpdate]:
    """Parse the Dependabot `updated-dependencies` JSON payload.

    Only entries from the `pip` ecosystem in the root directory whose name
    is in `TRACKED_DEPS` are returned. Conflicting versions for the same
    dependency cause the script to abort.
    """
    if not raw:
        fail(f"{METADATA_ENV_VAR} is empty")

    try:
        dependencies = json.loads(raw)
    except json.JSONDecodeError as exc:
        fail(f"failed to parse {METADATA_ENV_VAR}: {exc}")

    if not isinstance(dependencies, list):
        fail(f"{METADATA_ENV_VAR} must be an array")

    updates: dict[str, DependencyUpdate] = {}
    for dependency in dependencies:
        if not isinstance(dependency, dict):
            fail(f"{METADATA_ENV_VAR} contains a non-object item")
        if (
            dependency.get("packageEcosystem") != "pip"
            or dependency.get("directory") != "/"
        ):
            continue
        name = dependency.get("dependencyName")
        if name not in TRACKED_DEPS:
            continue
        version = dependency.get("newVersion")
        if not isinstance(version, str) or not version:
            fail(f"missing newVersion for {name!r}")
        previous = updates.get(name)
        if previous is not None and previous.new_version != version:
            fail(f"found conflicting {METADATA_ENV_VAR} entries for {name!r}")
        updates[name] = DependencyUpdate(name=name, new_version=version)

    if not updates:
        fail("no grpc/protobuf dependency metadata found")

    return list(updates.values())


def runtime_versions(updates: list[DependencyUpdate]) -> dict[str, str]:
    """Return `{name: new_version}` for runtime dependencies only.

    Build-time-only entries (e.g. `grpcio-tools`) are dropped: a Dependabot
    bump of just `grpcio-tools` does not by itself imply a runtime range
    rewrite. The runtime `grpcio` floor is updated only when Dependabot
    reports a matching `grpcio` bump in the same payload.
    """
    return {
        update.name: update.new_version
        for update in updates
        if update.name in RUNTIME_DEPS
    }


def replace_once(
    text: str,
    pattern: str,
    repl: Callable[[re.Match[str]], str],
    what: str,
) -> tuple[str, int]:
    """Replace the first match of `pattern` in `text`."""
    matches = list(re.finditer(pattern, text))
    if len(matches) != 1:
        fail(f"expected exactly one {what} entry")
    text, count = re.subn(pattern, repl, text, count=1)
    return text, count


def replace_range(text: str, name: str, version: str) -> tuple[str, int]:
    """Update a dependency floor and its compatibility upper bound.

    Rewrites the `"<name> >= X, < Y"` runtime range and the trailing
    `# Do not widen beyond Y!` comment so both reflect the new `version`
    and the configured `UPPER_BOUND_OFFSETS` for `name`.
    """
    upper_bound_offset = UPPER_BOUND_OFFSETS.get(name)
    if upper_bound_offset is None:
        fail(f"unsupported runtime dependency {name!r}")

    new_limit_major = major(version) + upper_bound_offset
    pattern = rf'("{re.escape(name)}\s*>=\s*)([^,\"]+)(\s*,\s*<\s*)([^\"]+)(")'

    def repl(match: re.Match[str]) -> str:
        old_floor = match.group(2).strip()
        if major(version) < major(old_floor):
            fail(f"refusing to downgrade {name} from {old_floor} to {version}")
        return (
            f"{match.group(1)}{version}{match.group(3)}"
            f"{new_limit_major}{match.group(5)}"
        )

    text, count = replace_once(text, pattern, repl, f"{name} runtime range")

    comment_pattern = (
        rf'("{re.escape(name)}\s*>=\s*{re.escape(version)}'
        rf'\s*,\s*<\s*{new_limit_major}"\s*,\s*'
        rf"#\s*Do not widen beyond\s*)\d+(!)"
    )
    text = re.sub(comment_pattern, rf"\g<1>{new_limit_major}\2", text, count=1)
    return text, count


def apply_updates(pyproject_path: Path, updates: list[DependencyUpdate]) -> None:
    """Apply runtime range updates derived from `updates` to `pyproject_path`."""
    text = pyproject_path.read_text(encoding="utf-8")
    versions = runtime_versions(updates)
    replacements = 0

    for name in RUNTIME_DEPS:
        version = versions.get(name)
        if version is None:
            continue
        text, count = replace_range(text, name, version)
        replacements += count

    if replacements == 0:
        print("No grpc/protobuf runtime constraints to update.")
        return

    pyproject_path.write_text(text, encoding="utf-8")
    print(f"Updated {pyproject_path} with {replacements} grpc/protobuf constraint(s).")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Sync grpc/protobuf runtime dependency ranges in pyproject.toml "
            "with the build-time versions reported by Dependabot via the "
            f"{METADATA_ENV_VAR} environment variable."
        ),
    )
    parser.add_argument(
        "pyproject",
        nargs="?",
        type=Path,
        default=PYPROJECT,
        help=(f"Path to the pyproject.toml file to update (default: {PYPROJECT})."),
    )
    return parser.parse_args(argv)


def main() -> None:
    """Apply dependency version updates to a `pyproject.toml` file."""
    args = parse_args()
    if not args.pyproject.exists():
        fail(f"{args.pyproject} not found")
    raw_metadata = os.environ.get(METADATA_ENV_VAR, "")
    updates = parse_dependabot_metadata(raw_metadata)
    apply_updates(args.pyproject, updates)


if __name__ == "__main__":
    main()
