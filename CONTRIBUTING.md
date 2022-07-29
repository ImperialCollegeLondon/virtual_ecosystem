# Contributing to the Virtual Rainforest

We're really happy that you are thinking about contributing to the Virtual Rainforest
project. The whole point of the project is to generate a tool that can be used widely by
the community and the best way for that to happen is for the community to build it.

To make contributing as seemless as possible, please note these developer guidelines.

## Development setup

Further notes are available [here](source/docs/develop/developer_setup.md) but - once
you have cloned the Virtual Rainforest repository to your own machine - you will need to
set up our development toolchain on your machine to contribute to the project.

* We use `poetry` ([](https://https://python-poetry.org/)) to manage the package
  development. Once you have installed `poetry`, you can use `poetry install` within
  the repo to start using it.
* We use `pre-commit` ([](https://pre-commit.com/)) to maintain code quality on
  submitted code. Before changing the code, install `pre-commit` and then use
  `pre-commit` install to make sure that your code is being checked.

## Contributing code

* Code contributed to the Virtual Rainforest **must** address a documented issue on the
  [issue tracker](https://github.com/ImperialCollegeLondon/virtual_rainforest/issues).
* If you are fixing an existing issue then that is great, but please do ask to be
  assigned to the issue to avoid duplicating effort!
* If this is something new, please raise an issue describing the contribution you want
  to make and **do wait for feedback** on your suggestion before spending time and
  effort coding.
* Once you are ready to contribute code, create a new feature branch in your local
  repository and develop your code in that branch.
* When the issue is solved, do include the text `Closes #nnn` in your final commit
  message body, to tie your pull request to the original issue.
* Obviously, that code needs to pass the `pre-commit` checks!
* Now submit a **pull request** to merge your branch into the `develop` branch of the
  Virtual Rainforest project.
* We will then review the contributed code and merge it once any problems have been
  resolved.

## The `pytest` framework

We use `pytest` ([](https://docs.pytest.org/)) to run continuous integration and other
testing on the code in Virtual Rainforest. If you are adding new functionality or
fixing errors in existing implementations, please also add new tests or amend any
existing tests.
