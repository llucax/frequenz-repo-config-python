# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH

"""This module defines macros for use in Markdown files."""

import logging
import os
import subprocess
from typing import Any

import markdown as md
from markdown.extensions import toc
from mkdocs_macros import plugin as macros

_logger = logging.getLogger(__name__)

_CODE_ANNOTATION_MARKER: str = (
    r'<span class="md-annotation">'
    r'<span class="md-annotation__index" tabindex="-1">'
    r'<span data-md-annotation-id="1"></span>'
    r"</span>"
    r"</span>"
)


def _slugify(text: str) -> str:
    """Slugify a text.

    Args:
        text: The text to slugify.

    Returns:
        The slugified text.
    """
    # The type of the return value is not defined for the markdown library.
    # Also for some reason `mypy` thinks the `toc` module doesn't have a
    # `slugify_unicode` function, but it definitely does.
    return toc.slugify_unicode(text, "-")  # type: ignore[attr-defined,no-any-return]


def _get_git_output(*args: str) -> str | None:
    """Get the output of a git command.

    Args:
        *args: The arguments to pass to the git command.

    Returns:
        The output of the git command or `None` if the command didn't output anything
            or failed.
    """
    try:
        return subprocess.check_output(["git", *args]).decode("utf-8").strip() or None
    except subprocess.CalledProcessError as exc:
        _logger.warning("Failed to get git output for %s: %s", args, exc)
        return None


def _strip_v(version: str) -> str:
    """Strip a leading `v` from a version string.

    Args:
        version: The version to strip the `v` from.

    Returns:
        The version without the leading `v`.
    """
    return version[1:] if version.startswith("v") else version


def _add_version_variables(env: macros.MacrosPlugin) -> None:
    """Add variables with git information to the environment.

    Args:
        env: The environment to add the variables to.
    """
    git_tag = _get_git_output("tag", "--points-at", "HEAD")
    git_branch = _get_git_output("branch", "--show-current")
    git_tag_last = _get_git_output("describe", "--abbrev=0", "--tags", "HEAD^")
    git_ref_name = os.environ.get("GIT_REF_NAME", None) or git_tag or git_branch
    pkg_version_last = None
    pkg_version_next = None
    if git_tag_last is not None:
        pkg_version_last = _strip_v(git_tag_last)
        try:
            major_str, minor_str, _ = _strip_v(git_tag_last).split(".", maxsplit=2)
        except ValueError as exc:
            _logger.warning(
                "Failed to parse major and minor version from %s: %s", git_tag_last, exc
            )
        else:
            try:
                last_major = int(major_str)
                last_minor = int(minor_str)
            except ValueError as exc:
                _logger.warning(
                    "Failed to parse last tag version from %s: %s", git_tag_last, exc
                )
            else:
                if last_major == 0:
                    pkg_version_next = f"{last_major}.{last_minor + 1}"
                else:
                    pkg_version_next = f"{last_major + 1}"

    env.variables["git_tag"] = git_tag
    env.variables["git_branch"] = git_branch
    env.variables["git_ref_name"] = git_ref_name
    env.variables["git_tag_last"] = git_tag_last
    env.variables["pkg_version_last"] = pkg_version_last
    env.variables["pkg_version_next"] = pkg_version_next


def _hook_macros_plugin(env: macros.MacrosPlugin) -> None:
    """Integrate the `mkdocs-macros` plugin into `mkdocstrings`.

    This is a temporary workaround to make `mkdocs-macros` work with
    `mkdocstrings` until a proper `mkdocs-macros` *pluglet* is available. See
    https://github.com/mkdocstrings/mkdocstrings/issues/615 for details.

    Args:
        env: The environment to hook the plugin into.
    """
    # get mkdocstrings' Python handler
    python_handler = env.conf["plugins"]["mkdocstrings"].get_handler("python")

    # get the `update_env` method of the Python handler
    update_env = python_handler.update_env

    # override the `update_env` method of the Python handler
    def patched_update_env(markdown: md.Markdown, config: dict[str, Any]) -> None:
        update_env(markdown, config)

        # get the `convert_markdown` filter of the env
        convert_markdown = python_handler.env.filters["convert_markdown"]

        # build a chimera made of macros+mkdocstrings
        def render_convert(markdown: str, *args: Any, **kwargs: Any) -> Any:
            return convert_markdown(env.render(markdown), *args, **kwargs)

        # patch the filter
        python_handler.env.filters["convert_markdown"] = render_convert

    # patch the method
    python_handler.update_env = patched_update_env


def define_env(env: macros.MacrosPlugin) -> None:
    """Define the hook to create macro functions for use in Markdown.

    Args:
        env: The environment to define the macro functions in.
    """
    # A variable to easily show an example code annotation from mkdocs-material.
    # https://squidfunk.github.io/mkdocs-material/reference/code-blocks/#adding-annotations
    env.variables["code_annotation_marker"] = _CODE_ANNOTATION_MARKER

    _add_version_variables(env)

    # This hook needs to be done at the end of the `define_env` function.
    _hook_macros_plugin(env)
