---
jupytext:
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.3
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

# Package release process

The package release process has three stages. The last step is automated:

* Make a PR to `develop` that increments the version number using `poetry` and updates
  any notebooks that are stored in an executed format.
* Publish a release on GitHub - this is basically just a specific tagged commit on
  `develop` that has some associated release notes.
* Publish the built code packages to PyPI - this is the packaged version of the code
  that users will install and use. The `virtual_ecosystem` package uses the trusted
  publishing mechanism to make it easy to add new release to PyPI.

## Pre-release candidates and experimental releases

The documentation below describes the process for 'official' releases of the Virtual
Ecosystem, but it is sometimes useful to be able to release a test version or a release
candidate. This can of course follow exactly the same instructions as below - an
official release candidate is fine! However, you _can_ create a release from any
branch, so it is possible to make a test release from `release/X.Y.Z` branch. This
should always be discussed with the wider developer team.

In this case, you may want to include the text `test-pypi-only` in the release name.
This will publish the package on the Test PyPI archive but not the main PyPI archive.
This has some advantages - we don't clutter up the official releases with experimental
versions - but the test archive does not necessarily include all the versions of
required packages needed and so is not really suitable for versions intended for testing
by end users. See below for more information on how this option works.

## Generate the code commit to be released

You should start the release process by first making an issue for the release, using the
issue template for releases. This template summarises the checks and steps you must
perform to create a releasable commit on `develop`. These are as follows:

1. In a new PR, update the `pyproject.toml` file to use the expected release versions
   number and commit that change. You can use `poetry version` command to increment the
   major, minor and patch version but it is almost as easy to edit the file by hand.

1. **The CI testing obviously needs to pass**. Any issues need to be resolved in this
   PR.

1. Making the PR should set the standard `ci.yaml` actions going, which includes
   code QA, testing and docs building. However, you should also check the documentation
   builds on Read The Docs.

   Log in to [https://readthedocs.org](https://readthedocs.org) which is the admin site
   controlling the build process. From the Versions tab, activate the `develop` branch
   and wait for it to build. Check the Builds tab to see that it has built successfully!
   If it has built successfully, do check pages to make sure that page code has executed
   successfully, and then go back to the Versions tab and deactivate and hide the
   branch. If any changes are needed before releasing, do come back and check that those
   changes have also built successfully.

1. The tests run as part of the CI are unit tests, we do not run an extended integration
   test. So, before releasing you should check that the model runs successfully with the
   example data (we provide [instructions for how to do
   this](../../using_the_ve/example_data.md)).

1. Some of the documentation consists of Jupyter note books that are stored in an
   executed form in order to reduce documentation build times. However, these need to be
   updated with each new release to ensure that the steps contained in them have not
   become outdated. This can be done for all relevant notebooks at once, by navigating
   to `docs/source` and running the `update_notebooks.sh` script.

1. Once everything on the list above is working merge this PR into `develop`.

## Create the GitHub release

The head of the `develop` branch is now at the commit that will be released as version
`X.Y.Z`. The starting point is to **go to the [draft new release
page](https://github.com/ImperialCollegeLondon/virtual_ecosystem/releases/new)**. The
creation of a new release is basically attaching notes and files to a specific commit on
a target branch. The steps are:

1. On that release page, the **release target** dropdown should essentially always be
   set to `develop`:

1. You need to provide a tag for the commit to be released - so you need to **tag the
   commit on the `develop` branch** using the format `vX.Y.Z`. You can:

   * Create the tag locally using `git tag vX.Y.Z` and then push the tag using `git push
     --tags`. You can then select the existing tag from the drop down on the release
     page.
   * Alternatively, you can simply type the tag name into that drop down and the tag
     will be created alongside the draft release.

1. You will need to choose a title for the release: basically `Release vX.Y.Z` is fine.
   However, the title text also provides a mechanism for suppressing automatic trusted
   publication to the main PyPI server by using `Release vX.Y.Z test-pypi-only`. See
   below for details.

1. You can create release notes automatically - this is basically a list of the commits
   being added since the last release - and can also set the version as a pre-release.
   This is different from having an explicit release version number (e.g. `X.Y.Za1`) -
   it is just a marker used on GitHub.

   At this point, you can either save the draft or simply publish it. It is probably
   good practice to save the draft and then have a discussion with the other developers
   about whether to publish it.

1. Once everyone is agreed **publish the release**: this will **automatically** publish
   the release on PyPI.

## Publish the package on PyPI

We publish to _two_ package servers:

* The
  [TestPyPI](https://test.pypi.org/project/virtual_ecosystem/) server is a final check
  to make sure that the package build and publication process is working as expected.
* The package builds are then published to the main
  [PyPI](https://pypi.org/project/virtual_ecosystem/) server for public use.

The `virtual_ecosystem` repository is set up to use trusted publishing through [a Github
Actions workflow](./github_actions.md#publication-workflow).
