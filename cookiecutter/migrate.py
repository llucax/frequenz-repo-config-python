#!/usr/bin/env python3
# License: MIT
# Copyright © 2024 Frequenz Energy-as-a-Service GmbH

"""Script to migrate existing projects to new versions of the cookiecutter template.

This script migrates existing projects to new versions of the cookiecutter
template, removing the need to completely regenerate the project from
scratch.

To run it, the simplest way is to fetch it from GitHub and run it directly:

    curl -sSL https://raw.githubusercontent.com/frequenz-floss/frequenz-repo-config-python/v0.10.0/cookiecutter/migrate.py | python3

Make sure the version you want to migrate to is correct in the URL.

For jumping multiple versions you should run the script multiple times, once
for each version.

And remember to follow any manual instructions for each run.
"""  # noqa: E501

import os
import subprocess
import tempfile
from pathlib import Path
from typing import SupportsIndex


def apply_patch(patch_content: str) -> None:
    """Apply a patch using the patch utility."""
    subprocess.run(["patch", "-p1"], input=patch_content.encode(), check=True)


def replace_file_contents_atomically(  # noqa; DOC501
    filepath: str | Path,
    old: str,
    new: str,
    count: SupportsIndex = -1,
    *,
    content: str | None = None,
) -> None:
    """Replace a file atomically with new content.

    Args:
        filepath: The path to the file to replace.
        old: The string to replace.
        new: The string to replace it with.
        count: The maximum number of occurrences to replace. If negative, all occurrences are
            replaced.
        content: The content to replace. If not provided, the file is read from disk.

    The replacement is done atomically by writing to a temporary file and
    then moving it to the target location.
    """
    if isinstance(filepath, str):
        filepath = Path(filepath)

    if content is None:
        content = filepath.read_text(encoding="utf-8")

    content = content.replace(old, new, count)

    # Create temporary file in the same directory to ensure atomic move
    tmp_dir = filepath.parent

    # pylint: disable-next=consider-using-with
    tmp = tempfile.NamedTemporaryFile(mode="w", dir=tmp_dir, delete=False)

    try:
        # Copy original file permissions
        st = os.stat(filepath)

        # Write the new content
        tmp.write(content)

        # Ensure all data is written to disk
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp.close()

        # Copy original file permissions to the new file
        os.chmod(tmp.name, st.st_mode)

        # Perform atomic replace
        os.rename(tmp.name, filepath)

    except BaseException:
        # Clean up the temporary file in case of errors
        tmp.close()
        os.unlink(tmp.name)
        raise


def main() -> None:
    """Run the migration steps."""
    # Dependabot patch
    dependabot_yaml = Path(".github/dependabot.yml")
    print(f"{dependabot_yaml}: Add new grouping for actions/*-artifact updates.")
    if dependabot_yaml.read_text(encoding="utf-8").find("actions/*-artifact") == -1:
        apply_patch(
            """\
--- a/.github/dependabot.yml
+++ b/.github/dependabot.yml
@@ -39,3 +39,11 @@ updates:
     labels:
       - "part:tooling"
       - "type:tech-debt"
+    groups:
+      compatible:
+        update-types:
+          - "minor"
+          - "patch"
+      artifacts:
+        patterns:
+          - "actions/*-artifact"
"""
        )
    else:
        print(f"{dependabot_yaml}: seems to be already up-to-date.")
    print("=" * 72)

    # Fix labeler configuration
    labeler_yml = ".github/labeler.yml"
    print(f"{labeler_yml}: Fix the labeler configuration example.")
    replace_file_contents_atomically(
        labeler_yml, "all-glob-to-all-file", "all-globs-to-all-files"
    )
    print("=" * 72)

    # Add a separation line like this one after each migration step.
    print("=" * 72)


def manual_step(message: str) -> None:
    """Print a manual step message in yellow."""
    print(f"\033[0;33m>>> {message}\033[0m")


if __name__ == "__main__":
    main()
