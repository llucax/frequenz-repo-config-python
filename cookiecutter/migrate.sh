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

echo "TODO: Describe your migration step here."
# Add your migration steps here.
manual_step "Add any manual instructions for this step here."

# Add a separation line like this one after each migration step.
echo "========================================================================"
