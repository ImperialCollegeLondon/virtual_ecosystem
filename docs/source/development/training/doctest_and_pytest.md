---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.13.8
kernelspec:
  display_name: vr_python3
  language: python
  name: vr_python3
---

<!-- markdownlint-disable MD024 MD041 - repeated headings and not header first-->

+++ {"slideshow": {"slide_type": "slide"}, "tags": []}

# Code Testing with `pytest` and `doctest`

David Orme

```{code-cell} ipython3
---
slideshow:
  slide_type: skip
tags: []
---
# Load packages used in loaded code examples
# This code is skipped in the slides
import pytest
from typing import List
```

+++ {"slideshow": {"slide_type": "slide"}, "tags": []}

## What is code testing?

- How do you know your code does what it claims to do?
  - "Well, that's what I wrote it to do"
  - "Well, if I give it this inputs it does this, **as expected**"
- Testing frameworks allow us to:
  - Give inputs to code
  - Check that it does what is expected
  - Repeatably and easily
  - A vital part of **continuous integration**

+++ {"slideshow": {"slide_type": "subslide"}, "tags": []}

## Continuous integration

- Code from a team is pushed into `develop` regularly.
- Need to be aware of **breaking changes**:
  - Updated algorithm gives different answers
  - Updated code takes different arguments
- Code testing helps catch breaking changes:
  - Catch and fix code errors
  - Need to release new **major version**

+++ {"slideshow": {"slide_type": "subslide"}, "tags": []}

## Semantic versioning

- Strict rules for version numbers
  - [](https://semver.org/)
  - [](https://github.com/semver/semver)
- With MAJOR.MINOR.PATCH, increment the:
  - MAJOR version when you make incompatible API changes,
  - MINOR version when you add functionality in a backwards compatible manner, and
  - PATCH version when you make backwards compatible bug fixes.

+++ {"slideshow": {"slide_type": "subslide"}, "tags": []}

## What should tests be?

- Pieces of code
- Expected outcomes of running code
- Individually small in scope
- Not just testing the **right answer**
- Test failure modes
- Quick to run

+++ {"slideshow": {"slide_type": "subslide"}, "tags": []}

## Frameworks

- Lots of options, including:
  - [The `pytest` extension](https://docs.pytest.org/)
  - [The `doctest` standard library](https://docs.python.org/3/library/doctest.html)
  - [The `unittest` standard library](https://docs.python.org/3/library/unittest.html)
  - [The `nose` extension](https://nose.readthedocs.io/en/latest/)

+++ {"slideshow": {"slide_type": "slide"}, "tags": []}

## The `doctest` package

- The **docstrings** for code often includes example use
- The `doctest` package runs those examples
- Check if documented example code is **correct**
  - Looks for inputs (`>>>`, `...`) and output
  - Typically simple, self-contained tests
  - **Exact match** to expected output
  - Look out for whitespace at the ends of lines!

+++ {"slideshow": {"slide_type": "subslide"}, "tags": []}

## The `doctest` package

```{code-cell} ipython3
# %load -s my_float_multiplier mfm.py
def my_float_multiplier(x: float, y: float) -> float:
    """Multiplies two floats together.

    Arguments:
        x: The first number
        y: The second number

    Examples:
        >>> my_float_multiplier(2.1, 3.6)
        7.56
    """

    return x * y
```

+++ {"slideshow": {"slide_type": "subslide"}, "tags": []}

## The `doctest` package

```{code-cell} ipython3
---
slideshow:
  slide_type: skip
tags: []
---
%%bash
doctestfn mfm.py my_float_multiplier
```

+++ {"slideshow": {"slide_type": "subslide"}, "tags": []}

## The `doctest` package

- Adjust the expected value

```{code-cell} ipython3
# %load -s my_float_multiplier2 mfm.py
def my_float_multiplier2(x: float, y: float) -> float:
    """Multiplies two floats together.

    Arguments:
        x: The first number
        y: The second number

    Examples:
        >>> round(my_float_multiplier2(2.1, 3.6), 2)
        7.56
    """
    
    return x * y
```

+++ {"slideshow": {"slide_type": "subslide"}, "tags": []}

## The `doctest` package

- Use `doctest` **directives**

```{code-cell} ipython3
# %load -s my_float_multiplier3 mfm.py
def my_float_multiplier3(x: float, y: float) -> float:
    """Multiplies two floats together.

    Arguments:
        x: The first number
        y: The second number

    Examples:
        >>> my_float_multiplier3(2.1, 3.6) #doctest: +ELLIPSIS
        7.56...
    """

    return x * y
```

+++ {"slideshow": {"slide_type": "subslide"}, "tags": []}

## The `doctest` package

- Can have more than one example
- Checking error conditions
- Can wrap input lines using `...`

```{code-cell} ipython3
# %load -s my_picky_float_multiplier mfm.py
def my_picky_float_multiplier(x: float, y: float) -> float:
    """Multiplies two floats together.

    Arguments:
        x: The first number
        y: The second number

    Examples:
        >>> my_float_multiplier3(2.1, 3.6)  # doctest: +ELLIPSIS
        7.56...
        >>> my_picky_float_multiplier_doctest(2, 3)  
        ... # doctest: +ELLIPSIS
        Traceback (most recent call last):
          ...
        ValueError: Both x and y must be of type float
    """

    if not (isinstance(x, float) and isinstance(y, float)):
        raise ValueError('Both x and y must be of type float')
    
    return x * y
```

+++ {"slideshow": {"slide_type": "subslide"}, "tags": []}

## The `doctest` package

- Can include 'setup' lines within a docstring.

```{code-cell} ipython3
:tags: []

# %load -s TimesTable mfm.py
class TimesTable:
    """Create times tables for a number.

    The TimesTable instance can be used to produce a times
    table for a specific number.

    Attributes:
        num: The base number to use for tables

    Args:
        num: Sets the `num` attribute

    Examples:
        >>> seven_tt = TimesTable(num = 7)
        >>> seven_tt  # doctest: +ELLIPSIS
        <mfm.TimesTable object at 0x...>
        >>> seven_tt.num
        7
    """

    def __init__(self, num: int) -> None:

        self.num = num

    def table(self, start: int = 1, stop: int = 10) -> List[int]:
        """Calculate a table.

        Returns a times table for the initialised base number from
        start to stop.

        Args:
            start: Start number for the table
            stop: End number for the table

        Examples:
            >>> seven_tt = TimesTable(num = 7)
            >>> seven_tt.table(2,7)
            [14, 21, 28, 35, 42, 49]
        """

        return [self.num * v for v in range(start, stop + 1)]
```

+++ {"slideshow": {"slide_type": "subslide"}, "tags": []}

## Running `doctest`

- Use `python -m doctest filename.py`
- Or `python -m doctest folder/*.py`
- Can use `python -m doctest -v filename.py` for **verbose** information

```{code-cell} ipython3
%%bash --no-raise-error
python -m doctest -v mfm.py
```

+++ {"slideshow": {"slide_type": "subslide"}, "tags": []}

## The `doctest` package: summary

- Invaluable for maintaining documentation quality
- Spot checks on code function
- Limited to relatively simple uses
- Tests for each docstring run **independently** and cannot share information

+++ {"slideshow": {"slide_type": "subslide"}, "tags": []}

## Using `doctest`

- Open VS Code
- Use File > Open Folder to open your cloned Virtual Rainforest repo
- Use Terminal > New Terminal to get a command line terminal
- In the Terminal, enter `git checkout testing_training`
- In the File Explorer (icon column on left) open `my_module.py`
- Use the TODO tree (icon column on left) to check off tasks
- Use `python -m doctest my_module.py` to check progress!

+++ {"slideshow": {"slide_type": "slide"}, "tags": []}

## The `pytest` framework

- The main testing framework
- Much more powerful, also more complex!
- Tests in separate files or directories
- Running `pytest` automatically finds tests in files and runs them

+++ {"slideshow": {"slide_type": "subslide"}, "tags": []}

## The `pytest` framework

- Typical package test structure:
  - A separate directory in the package root (`test`)
  - Can contain subfolders (e.g. grouped by package module)
  - Contains test files: `test_xyz.py`
- Tests within files identified by name:
  - classes (e.g. `TestClass`)
  - functions (e.g. `test_function`)

+++ {"slideshow": {"slide_type": "subslide"}, "tags": []}

## A `pytest` test

- A really simple example
- A function that runs a bit of code
- And **`asserts`** that the output equals a value

```{code-cell} ipython3
# %load -s test_fm test_mfm.py
def test_fm():

    assert 10 == my_float_multiplier(2, 5)
```

+++ {"slideshow": {"slide_type": "subslide"}, "tags": []}

## Testing failure modes

- A more picky function

```{code-cell} ipython3
# %load -s my_picky_float_multiplier mfm.py
def my_picky_float_multiplier(x: float, y: float) -> float:
    """Multiplies two floats together.

    Arguments:
        x: The first number
        y: The second number

    Examples:
        >>> my_float_multiplier3(2.1, 3.6)  # doctest: +ELLIPSIS
        7.56...
        >>> my_picky_float_multiplier(2, 3)  
        ... # doctest: +ELLIPSIS
        Traceback (most recent call last):
          ...
        ValueError: Both x and y must be of type float
    """

    if not (isinstance(x, float) and isinstance(y, float)):
        raise ValueError('Both x and y must be of type float')
    
    return x * y
```

+++ {"slideshow": {"slide_type": "subslide"}, "tags": []}

## Testing exceptions

- Use the `pytest.raises` context manager
- Traps exceptions
- Makes sure the exception is the right type

```{code-cell} ipython3
# %load -s test_pfm test_mfm.py
def test_pfm():

    with pytest.raises(ValueError) as err_hndlr:

        x = my_picky_float_multiplier(2, 5)

    assert str(err_hndlr.value) == "Both x and y must be of type float"
```

+++ {"slideshow": {"slide_type": "subslide"}, "tags": []}

## Running tests

- Use `pytest`!
- Can use `pytest filename` or \`filename filename::testname\`\`.

```{code-cell} ipython3
:tags: []

%%bash
pytest -v test_mfm.py::test_fm test_mfm.py::test_pfm
```

+++ {"slideshow": {"slide_type": "subslide"}, "tags": []}

## When tests go bad

```{code-cell} ipython3
%%bash --no-raise-error
pytest test_mfm.py::test_pfm_fail
```

+++ {"slideshow": {"slide_type": "subslide"}, "tags": []}

## Parameterization

- Reuse the same test function
- Test different input values

```{code-cell} ipython3
# %load -s test_pfm_param_noid test_mfm.py
@pytest.mark.parametrize(
    argnames=["x", "y", "expected"],
    argvalues=[
        (1.0, 3.0, 3.0),
        (1.5, -3.0, -4.5),
        (-1.5, 3.0, -4.5),
        (-1.5, -3.0, 4.5),
    ],
)
def test_pfm_param_noid(x, y, expected):

    assert expected == my_picky_float_multiplier(x, y)
```

+++ {"slideshow": {"slide_type": "subslide"}, "tags": []}

## Running `pytest`

```{code-cell} ipython3
:tags: []

%%bash
pytest -v test_mfm.py::test_pfm_param_noid
```

+++ {"slideshow": {"slide_type": "subslide"}, "tags": []}

## Parameterization: test ids

- Adds a label for each parameterized test

```{code-cell} ipython3
# %load -s test_pfm_param_ids test_mfm.py
@pytest.mark.parametrize(
    argnames=["x", "y", "expected"],
    argvalues=[
        (1.5, 3.0, 4.5),
        (1.5, -3.0, -4.5),
        (-1.5, 3.0, -4.5),
        (-1.5, -3.0, 4.5),
    ],
    ids=["++", "-+", "+-", "--"],
)
def test_pfm_param_ids(x, y, expected):

    assert expected == my_picky_float_multiplier(x, y)
```

+++ {"slideshow": {"slide_type": "subslide"}, "tags": []}

## Running `pytest`

```{code-cell} ipython3
%%bash
pytest -v test_mfm.py::test_pfm_param_ids
```

+++ {"slideshow": {"slide_type": "subslide"}, "tags": []}

## Parameterization: combinatorial

- You can add more than on parameter set
- The test will run on all combinations

```{code-cell} ipython3
# %load -s test_pfm_twoparam test_mfm.py
@pytest.mark.parametrize(
    argnames=["x"],
    argvalues=[(1.5,), (-1.5,)],
    ids=["+", "-"],
)
@pytest.mark.parametrize(
    argnames=["y"],
    argvalues=[(3.0,), (-3.0,)],
    ids=["+", "-"],
)
def test_pfm_twoparam(x, y):

    assert 4.5 == abs(my_picky_float_multiplier(x, y))
```

+++ {"slideshow": {"slide_type": "subslide"}, "tags": []}

## Running `pytest`

- The IDs for each test get concatenated using `-`

```{code-cell} ipython3
%%bash
pytest -v test_mfm.py::test_pfm_twoparam
```

+++ {"slideshow": {"slide_type": "subslide"}, "tags": []}

## Fixtures

- Reusable bits of code shared between tests
  - Built in fixtures
  - User defined fixtures using the `@pytest.fixture` **decorator**

```{code-cell} ipython3
# %load -s twoparam_expected test_mfm.py
@pytest.fixture
def twoparam_expected():

    expected = {'+-+':  4.5, '---': 4.5, '--+': -4.5, '+--': -4.5}
    return expected
```

+++ {"slideshow": {"slide_type": "subslide"}, "tags": []}

## Using fixtures

- Add the fixture name to the test function arguments
- Example has a user defined and built-in fixture (`request`)

```{code-cell} ipython3
# %load -s test_pfm_twoparam_fixture test_mfm.py
@pytest.mark.parametrize(
    argnames=["x"],
    argvalues=[(1.5,), (-1.5,)],
    ids=["+", "-"],
)
@pytest.mark.parametrize(
    argnames=["y"],
    argvalues=[(3.0,), (-3.0,)],
    ids=["+", "-"],
)
def test_pfm_twoparam_fixture(request, twoparam_expected, x, y):

    expected = twoparam_expected[request.node.callspec.id]

    assert expected == my_picky_float_multiplier(x, y)
```

+++ {"slideshow": {"slide_type": "subslide"}, "tags": []}

## Running `pytest`

```{code-cell} ipython3
%%bash
pytest -v test_mfm.py::test_pfm_twoparam_fixture
```

+++ {"slideshow": {"slide_type": "subslide"}, "tags": []}

## Conftest and other built-in fixtures

- The `pytest` package looks for `conftest.py`
  - Create settings and fixtures used across test files
- The `caplog` built-in fixture
  - Captures emitted messages from the `logging` package
- The `fakefs` package and `fs` built-in fixture
  - Allows file paths and contents to be simulated
  - Ensure consistent locations for testing across platforms

+++ {"slideshow": {"slide_type": "subslide"}, "tags": []}

## Using `pytest`

- Go back to VS Code
- Open the `test_my_module.py` file
- Use the TODO tree to work through required tests
- Use `pytest -v test_my_module.py` to run tests
- Or use the Testing icon to view and run tests
