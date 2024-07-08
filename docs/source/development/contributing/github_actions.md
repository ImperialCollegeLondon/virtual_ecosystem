---
jupytext:
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.16.2
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

# GitHub Actions

The project uses several workflows using GitHub Actions to maintain code quality and
confirm that the package and website are building correctly. The actions are defined in
the `.github/workflows` directory and currently include:

## Continuous integration workflow

The `ci.yml` workflow runs when a pull request is opened and when new commits are made
to an existing pull request. It is the main quality assurance check on new code and runs
three jobs:

* code quality assurance (`qa`): does the code pass all the `pre-commit` checks.
* code testing (`test`): do all unit and integration tests in the `pytest` suite pass.
* documentation building (`docs_build`): does the documentation build correctly.

If any of those checks fail, you will need to push new commits to the pull request to
fix the outstanding issues. The status of code checking for pull requests can be seen at:

[https://github.com/ImperialCollegeLondon/virtual_ecosystem/actions](https://github.com/ImperialCollegeLondon/virtual_ecosystem/actions)

Although GitHub Actions automates these steps for any pushes, pull requests and releases
on the repository, you should also perform the same steps locally before submitting code
to ensure that your code passes testing. The `pre-commit` test is automatic but follow
the instructions for [running `pytest`](./code_testing.md) and [building the
documentation](../documentation/documentation.md).

::::{dropdown} CI workflow details
:::{literalinclude} ../../../../.github/workflows/ci.yml
:language: yaml
:::
::::

## Publication workflow

The `publish.yaml` workflow runs when a release is made on the GitHub site and uses
trusted publishing to build the package and publish it on
[PyPI](https://pypi.org/project/virtual_ecosystem/).

The full workflow setup can be seen below, along with comments, but the basic flow is:

1. When a GitHub release is published, the PyPI publication workflow is triggered.
1. The standard continuous integration tests are run again, just to be sure!
1. If the tests pass, the package is built and the wheel and source code are stored as
   job artefacts.
1. The built files are automatically added to the release assets.
1. The built files are then also published to the Test PyPI server, which is configured
   to automatically trust publications from this GitHub repository.
1. As long as all the steps above succeed, the built files are now published to the
   main PyPI site, which is also configured to trust publications from the repository.

The last step of publication to the main PyPI site can be skipped by including the
text `test-pypi-only` in the title text for the release. This allows pre-release
tests and experimentation to be tested without automatically adding them to the
official released versions.

::::{dropdown} Publication workflow details
:::{literalinclude} ../../../../.github/workflows/publish.yml
:language: yaml
:::
::::
