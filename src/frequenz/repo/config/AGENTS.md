# AGENTS.md - Package Subtree Guide

This subtree contains the core `frequenz-repo-config` package implementation. It provides the scaffolding, configuration, and utilities for Frequenz repositories.

## Internal Navigation

### Core Modules
- `_core.py`: Repository type definitions (`RepositoryType`).
- `github.py`: GitHub Actions and workflow utilities.
- `protobuf.py`: Protobuf/gRPC path and build helpers.
- `version.py`: Versioning logic.

### Internal Clusters
- `nox/`: Largest cluster. Predefined sessions and configuration for `nox`.
  - `session.py`: The actual `@nox.session` definitions (CI, formatting, mypy, etc.).
  - `config.py`: Options and path resolution for nox commands.
- `mkdocs/`: Substantial subpackage for documentation generation.
  - `api_pages.py`: Automatic Python API reference generation.
  - `mike.py`: Integration with `mike` for versioned docs.
- `pytest/`: Testing utilities.
  - `examples.py`: Plugin for linting code examples in docstrings.
- `setuptools/`: Build system hooks.
  - `grpc_tools.py`: `CompileProto` command for compiling protobufs during build.
- `cli/`: Command-line tools, specifically for version management under `cli/version/mike/`.

## Conventions & Style

- **Strict Typing**: All functions and classes must have complete type hints.
- **Docstrings**: Use Google-style docstrings. Document all arguments, return values, and exceptions.
- **Configuration**: Use `pyproject-driven` patterns. Tools should read their configuration from `pyproject.toml` whenever possible.
- **Naming**: Match existing patterns: snake_case for modules/functions, PascalCase for classes, UPPER_SNAKE for constants.

## Where to Look

- **Add a new nox session**: Check `nox/session.py`.
- **Modify API doc generation**: Check `mkdocs/api_pages.py`.
- **Change protobuf build logic**: Check `setuptools/grpc_tools.py` or `protobuf.py`.
- **Fix docstring example linting**: Check `pytest/examples.py`.
- **Define new repository types**: Check `_core.py`.
