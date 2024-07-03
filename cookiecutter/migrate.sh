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

echo "Fixing pip cache in '.github/workflows/ci.yaml'"
sed -i "s|hashFiles('\*\*/pyproject.toml')|hashFiles('pyproject.toml')|" .github/workflows/ci.yaml

echo "========================================================================"

echo "Fixing nox-(cross-arch-)all jobs to fail on child jobs failure in '.github/workflows/ci.yaml'"
sed -i \
  -e '/^    needs: \["nox-cross-arch"\]$/,/^        run: "true"$/c\
    needs: \["nox-cross-arch"\]\
    # We skip this job only if nox-cross-arch was also skipped\
    if: always() && needs.nox-cross-arch.result != '"'"'skipped'"'"'\
    runs-on: ubuntu-20.04\
    env:\
      DEPS_RESULT: ${{ needs.nox-cross-arch.result }}\
    steps:\
      - name: Check matrix job result\
        run: test "$DEPS_RESULT" = "success"' \
  -e '/^    needs: \["nox"\]$/,/^        run: "true"$/c\
    needs: ["nox"]\
    # We skip this job only if nox was also skipped\
    if: always() && needs.nox.result != '"'"'skipped'"'"'\
    runs-on: ubuntu-20.04\
    env:\
      DEPS_RESULT: ${{ needs.nox.result }}\
    steps:\
      - name: Check matrix job result\
        run: test "$DEPS_RESULT" = "success"' \
  .github/workflows/ci.yaml

echo "========================================================================"

echo "Disabling some pylint checks also checked by other tools"
sed -i -e '/  "unsubscriptable-object",/a \  # Checked by mypy\
  "no-member",' \
  -e '/  # Checked by flake8/a \  "f-string-without-interpolation",' \
  -e '/  "line-too-long",/a \  "missing-function-docstring",' \
  pyproject.toml

echo "========================================================================"

echo "Using symlink aliases in 'mkdocs.yml'"
sed -i "s|alias_type: redirect|alias_type: symlink|" mkdocs.yml

echo "========================================================================"

echo "Fixing credentials not being properly passed in '.github/workflows/ci.yaml'"
patch --merge -p1 <<'EOF'
diff --git a/.github/containers/test-installation/Dockerfile b/.github/containers/test-installation/Dockerfile
index 2494545..ac3de24 100644
--- a/.github/containers/test-installation/Dockerfile
+++ b/.github/containers/test-installation/Dockerfile
@@ -14,5 +14,8 @@ RUN apt-get update -y && \
     python -m pip install --upgrade --no-cache-dir pip
 
 COPY dist dist
-RUN pip install dist/*.whl && \
-    rm -rf dist
+# This git-credentials file is made available by the GitHub ci.yaml workflow
+COPY git-credentials /root/.git-credentials
+RUN git config --global credential.helper store && \
+    pip install dist/*.whl && \
+    rm -rf dist /root/.git-credentials
diff --git a/.github/workflows/ci.yaml b/.github/workflows/ci.yaml
index 8062a61..67000f1 100644
--- a/.github/workflows/ci.yaml
+++ b/.github/workflows/ci.yaml
@@ -41,6 +41,13 @@ jobs:
     runs-on: ${{ matrix.os }}
 
     steps:
+      - name: Setup Git
+        uses: frequenz-floss/gh-action-setup-git@v0.x.x
+        # TODO(cookiecutter): Uncomment this for projects with private dependencies
+        # with:
+        #   username: ${{ secrets.GIT_USER }}
+        #   password: ${{ secrets.GIT_PASS }}
+
       - name: Print environment (debug)
         run: env
 
@@ -119,6 +126,13 @@ jobs:
     runs-on: ${{ matrix.os }}
 
     steps:
+      - name: Setup Git
+        uses: frequenz-floss/gh-action-setup-git@v0.x.x
+        # TODO(cookiecutter): Uncomment this for projects with private dependencies
+        # with:
+        #   username: ${{ secrets.GIT_USER }}
+        #   password: ${{ secrets.GIT_PASS }}
+
       - name: Fetch sources
         uses: actions/checkout@v4
 
@@ -220,6 +234,13 @@ jobs:
     name: Build distribution packages
     runs-on: ubuntu-20.04
     steps:
+      - name: Setup Git
+        uses: frequenz-floss/gh-action-setup-git@v0.x.x
+        # TODO(cookiecutter): Uncomment this for projects with private dependencies
+        # with:
+        #   username: ${{ secrets.GIT_USER }}
+        #   password: ${{ secrets.GIT_PASS }}
+
       - name: Fetch sources
         uses: actions/checkout@v4
         with:
@@ -252,17 +273,31 @@ jobs:
     needs: ["build"]
     runs-on: ubuntu-20.04
     steps:
+      - name: Setup Git
+        uses: frequenz-floss/gh-action-setup-git@v0.x.x
+        # TODO(cookiecutter): Uncomment this for projects with private dependencies
+        # with:
+        #   username: ${{ secrets.GIT_USER }}
+        #   password: ${{ secrets.GIT_PASS }}
+
       - name: Fetch sources
         uses: actions/checkout@v4
+
       - name: Download package
         uses: actions/download-artifact@v4
         with:
           name: dist-packages
           path: dist
+
+      - name: Make Git credentials available to docker
        run: |
          touch ~/.git-credentials  # Ensure the file exists
+         cp ~/.git-credentials git-credentials || true
+
       - name: Set up QEMU
         uses: docker/setup-qemu-action@v3
+
       - name: Set up docker-buildx
         uses: docker/setup-buildx-action@v3
+
       - name: Test Installation
         uses: docker/build-push-action@v6
         with:
@@ -277,14 +312,18 @@ jobs:
     if: github.event_name != 'push'
     runs-on: ubuntu-20.04
     steps:
+      - name: Setup Git
+        uses: frequenz-floss/gh-action-setup-git@v0.x.x
+        # TODO(cookiecutter): Uncomment this for projects with private dependencies
+        # with:
+        #   username: ${{ secrets.GIT_USER }}
+        #   password: ${{ secrets.GIT_PASS }}
+
       - name: Fetch sources
         uses: actions/checkout@v4
         with:
           submodules: true
 
-      - name: Setup Git user and e-mail
-        uses: frequenz-floss/setup-git-user@v2
-
       - name: Set up Python
         uses: actions/setup-python@v5
         with:
@@ -319,14 +358,18 @@ jobs:
     permissions:
       contents: write
     steps:
+      - name: Setup Git
+        uses: frequenz-floss/gh-action-setup-git@v0.x.x
+        # TODO(cookiecutter): Uncomment this for projects with private dependencies
+        # with:
+        #   username: ${{ secrets.GIT_USER }}
+        #   password: ${{ secrets.GIT_PASS }}
+
       - name: Fetch sources
         uses: actions/checkout@v4
         with:
           submodules: true
 
-      - name: Setup Git user and e-mail
-        uses: frequenz-floss/setup-git-user@v2
-
       - name: Set up Python
         uses: actions/setup-python@v5
         with:
EOF
manual_step "Please make sure to remove or uncomment the options to the 'gh-action-setup-git' action in the '.github/workflows/ci.yaml'"
grep -n "TODO(cookiecutter)" -- .github/workflows/ci.yaml .github/containers/test-installation/Dockerfile

# Add a separation line like this one after each migration step.
echo "========================================================================"
