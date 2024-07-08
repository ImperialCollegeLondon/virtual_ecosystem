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

# Code quality and static typing

We use:

* `pre-commit` to ensure common code standards and style, and
* `mypy` to provide static typing of the `virtual_ecosystem` codebase.

## Using `pre-commit`

As described in the [developer overview](./overview.md), `pre-commit` is installed as by
`poetry` as part of the `virtual_ecosystem` developer dependencies. At this point, it
just need to be set up to run using:

```sh
poetry run pre-commit install
poetry run pre-commit run --all-files
```

This can take a while on the first run, and when the configuration updates, as the tool
needs to install or update all the hooks that are applied to changes within a commit.
Usually the hooks only run on files changed by a particular `git commit` but using
`pre-commit run --all-files` scans the entire codebase and is a commonly used check to
make sure all is well.

### The `pre-commit` configuration

The file
[.pre-commit-config.yaml](https://github.com/ImperialCollegeLondon/virtual_ecosystem/blob/develop/.pre-commit-config.yaml)
contains the pre-commit hooks used by `virtual_ecosystem`. You can see the full details
of the file below but the tools used are:

`pre-commit-hooks`
: We use these basic hooks to check for remaning `git` merge conflict markers in code
files (`check-merge-conflicts`) and for debugger imports and `breakpoint()` calls
(`dubug-statements`), which should not end up in code in the repository.

`ruff-pre-commit`
: This tool wraps the [`ruff`](https://docs.astral.sh/ruff/) code linter and formatter
and we use both the linting (`ruff`) and formatting (`ruff-format`) hooks.

`mypy`
: We use a hook here to run the `mypy` static typing checks on newly committed code. See
[below](#typing-with-mypy) for more information.

`markdownlint`
: Checks all markdown files for common formatting issues.

::::{dropdown} The `pre-commit-config.yaml` configuraiton
:::{literalinclude} ../../../../.pre-commit-config.yaml
:language: yaml
:::
::::

### Output and configuration

When `pre-commit` runs, you may see some lines about package installation and update,
but the key information is the output below, which shows the status of the checks set up
by each hook:

```text
check for merge conflicts............................................Passed
debug statements (python)............................................Passed
ruff.................................................................Passed
ruff-format..........................................................Passed
mypy.................................................................Passed
markdownlint.........................................................Passed
```

### Updating `pre-commit`

The hooks used by `pre-commit` are constantly being updated to provide new features or
to update code to deal with changes in the implementation. You can update the hooks
manually using `pre-commit autoupdate`, but the configuration is regularly updated
through the [pre-commit.ci](https://pre-commit.ci/) service.

## Typing with `mypy`

Unlike many programming languages, Python does not require variables to be declared as
being of a particular type. For example, in C++, this code creates a variable that is
_explicitly_ an integer and a function that _explicitly_ requires an integer and returns
an integer value. This is called **typing**.

```c++
int my_integer = 15;

int fun(int num) {

  printf("num = %d \n", num);

  return 0;
}
```

Python does not require explicit typing. That can be very useful but it can also make it
very difficult to be clear what kinds of variables are being used. The
`virtual_ecosystem` project
requires static typing of the source code: the syntax for this started with [PEP
484](https://peps.python.org/pep-0484/) and a set of quality assurance tools have
developed to help support clear and consistent typing. We use
[`mypy`](https://mypy.readthedocs.io/en/stable/) to check static typing. It does take a
bit of getting used to but is a key tool in maintaining clear code and variable
structures.

## Supressing checking

The `pre-commit` tools sometimes complain about things that we do not want to change.
Almost all of the tools can be told to suppress checking, using comments with a set
format to tell the tool what to do.

This should not be done lightly: we are using these QA tools for a reason.

* Code linting issued identified by `ruff` can be ignored by either using `# noqa: E501`
  to ignore the issue for that line.
* Code formatting changes suggested by `ruff-format` can be supressed by using the
  `# fmt: off` tag at the end of a specific line or wrapping a section in `# fmt: off`
  and then `# fmt: on`.
* `mypy` uses the syntax `# type: ignore` comment to [suppress
  warnings](https://mypy.readthedocs.io/en/stable/error_codes.html#silencing-errors-based-on-error-codes).
  Again, `virtual_ecosystem` requires that you provide the specific `mypy` error code to
  be ignored to avoid missing other issues:  `# type: ignore[operator]`.
* `markdownlint` catches issues in Markdown files and uses a range of [HTML comment
  tags](https://github.com/DavidAnson/markdownlint?tab=readme-ov-file#configuration) to
  suppress format warnings. An example is `<!-- markdownlint-disable-line MD001 -->` and
  a list of the rule codes can be found
  [here](https://github.com/DavidAnson/markdownlint/blob/main/doc/Rules.md).
