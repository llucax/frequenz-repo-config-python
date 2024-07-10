# Frequenz Repository Configuration Release Notes

## Summary

This release includes quite a few enhancements and bug fixes for the cookiecutter template, but most importantly a new script for migrating to new templates, generating the templates is no longer needed for upgrading.

## Upgrading

### Cookiecutter template

- A new script for migrating to new templates (instead of regenerating all files) is provided. It can't handle the upgrade 100% automatically, but should make the migration process much easier and less error prone.

  To run it, the simplest way is to fetch it from GitHub and run it directly:

  ```console
  curl -sSL https://raw.githubusercontent.com/frequenz-floss/frequenz-repo-config-python/v0.10.0/cookiecutter/migrate.sh | sh
  ```

  Make sure the version you want to migrate to is correct in the URL.

  For jumping multiple versions you should run the script multiple times, once for each version.

  And remember to follow any manual instructions for each run.

## New Features

- A new GitHub ruleset is provided to configure the merge queue, so branch protection rules are not needed anymore.

## Enhancements

- The generated docs now show the symbol type in the table of contents.

### Cookiecutter template

- The `Markdown` dependency was bumped so we don't need to add a `type: ignore` due to incorrect type hints.
- The generated docs now show the symbol type in the table of contents.
- The dependecies were updated to the latest versions.
- Disabled some `pylint` checks that are already checked by other tools.
- The generated documentation now uses symlinks for aliases, which allows deep linking when using aliases too.

## Bug Fixes

- The code example extractor relied on a bug in the upstream sybil project that was recently fixed, thus our code also needed to be fixed.

### Cookiecutter template

- Fixed a bug where the pip cache post action fails in the CI workflow because of permissions issues.
- Make the `nox-cross-arch-all` job fail if any `nox-cross-arch` matrix job fails.
- Fix credentials not being passed to the `test-installation` job in the CI workflow.
- Make sure credentials are configured for all jobs that check out the repository in the CI workflow.
- Disable the new `check-class-attributes` check in pydoclint 0.5.3, as we use a different way to document class attributes.
- Fix permissions issues with the `release-notes-check` workflow when the repository Actions configuration is set up without full access.
