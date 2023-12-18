# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH

"""Logging utilities to interact with MkDocs logger."""

import inspect
import logging


def get_logger() -> logging.Logger | None:
    """Get the mkdocs logger if we are running inside MkDocs."""
    if _is_running_inside_mkdocs():
        return logging.getLogger("mkdocs")
    return None


def _is_running_inside_mkdocs() -> bool:
    """Whether we are running inside MkDocs or not."""
    for frame_record in inspect.stack():
        frame = frame_record.frame
        module = inspect.getmodule(frame)
        if module is not None:
            # Check if the module's name is associated with MkDocs
            if module.__name__.startswith("mkdocs."):
                return True
    return False
