#!/bin/sh
# License: MIT
# Copyright © 2024 Frequenz Energy-as-a-Service GmbH
#
# This script migrates existing projects to new versions of the cookiecutter
# template, removing the need to completely regenerate the project from
# scratch.
#
# To run it, the simplest way is to fetch it from GitHub and run it directly:
#
#   curl -sSL https://raw.githubusercontent.com/frequenz-floss/frequenz-repo-config-python/v0.10.0/cookiecutter/migrate.sh | sh
#
# Make sure the version you want to migrate to is correct in the URL.
#
# For jumping multiple versions you should run the script multiple times, once
# for each version.
#
# And remember to follow any manual instructions for each run.
set -eu

manual_step() {
  echo "\033[0;33m>>> $@\033[0m"
}

echo "Removing the 'Markdown' type:ignore from docs/_scripts/macros.py"
sed -i \
	-e 's|return toc.slugify_unicode(text, "-")  # type: ignore\[attr-defined,no-any-return\]|return toc.slugify_unicode(text, "-")|' \
	-e '/# The type of the return value is not defined for the markdown library./d' \
	-e '/# Also for some reason `mypy` thinks the `toc` module doesn'\''t have a/d' \
	-e '/# `slugify_unicode` function, but it definitely does./d' \
	docs/_scripts/macros.py
echo
manual_step "Please make sure that the 'Markdown' and 'types-Markdown' dependencies are at version 3.5.2 or higher in 'pyproject.toml':"
grep 'Markdown' pyproject.toml

echo "========================================================================"

echo "Adding the new 'show_symbol_type_toc' option for MkDocs"
sed -i '/^            show_source: true$/a \            show_symbol_type_toc: true' mkdocs.yml
sed -i '/^  "mkdocstrings\[python\] == .*",$/a \  "mkdocstrings-python == 1.9.2",' pyproject.toml

echo "========================================================================"

manual_step "To configure merge queues via repository rulesets you need to:"
manual_step "  1. Go to your repository settings and click on 'Rules' -> 'Rulesets' in the sidebar."
manual_step "  2. Click on 'New ruleset' on the top right and select 'Import a ruleset'."
manual_step "  3. Select the file 'github-rulesets/Queue PRs for v0.x.x.json'."
manual_step "  4. Make sure the branch name is correct (matches the branch you want to configure the merge queue for) and click 'Create'."
manual_step "  5. Go to the 'Branches' section in the sidebar."
manual_step "  6. Remove any branch protection rules that are not needed anymore (you should probably have only one configuring the merge queue if you were using other rulesets before)."

echo "========================================================================"

echo "Adding a comment about the supported Python versions and architectures to the README.md file"
# Add a multiline text to the README.md file

sed -i '/^- \*\*Architectures:\*\* amd64/a \
\
> [!NOTE]\
> Newer Python versions and other operating systems and architectures might\
> work too, but they are not automatically tested, so we cannot guarantee it.' README.md

echo "========================================================================"

echo "Adding 'mkdocs-includue-markdown-plugin' to the 'pyproject.toml' and 'mkdocs.yml' files"
sed -i '/^        - docs\/_scripts\/mkdocstrings_autoapi\.py$/a \  - include-markdown' mkdocs.yml
sed -i '/^  "mkdocs-gen-files == .*",$/a \  "mkdocs-include-markdown-plugin == 6.0.5",' pyproject.toml

echo "========================================================================"

echo "Adding includable sections to the README.md file"
sed -i -e '/^## Introduction$/a \
\
<!-- introduction -->' \
  -e '/^## Supported Platforms$/i \
<!-- /introduction -->\
' \
  -e '/^## Supported Platforms$/a \
  \
<!-- supported-platforms -->' \
  -e '/^## Contributing$/i \
<!-- /supported-platforms -->\
' \
  README.md
if grep -q '^---8<-- "README.md"$' README.md
then
  echo "Including those sections in docs/index.md instead of the whole README.md file"
  replacement="$(cat <<EOT
$(head -n1 README.md) \\
\\
## Introduction\\
\\
{%\\
   include-markdown "../README.md"\\
   start="<!-- introduction -->"\\
   end="<!-- /introduction -->"\\
%}\\
\\
## Supported Platforms\\
\\
{%\\
   include-markdown "../README.md"\\
   start="<!-- supported-platforms -->"\\
   end="<!-- /supported-platforms -->"\\
%}
EOT
  )"
  sed -i 's|^---8<-- "README.md"$|'"$replacement"'|' docs/index.md
else
  manual_step "Please include the sections 'Introduction' and 'Supported Platforms' from the README.md file in the docs/index.md file."
  echo "    We couldn't find the expected marker in the README.md file to do the update automatically."
fi

# Add a separation line like this one after each migration step.
echo "========================================================================"
