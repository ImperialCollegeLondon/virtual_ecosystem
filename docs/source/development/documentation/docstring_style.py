"""This is the documentation for the module. It does not start with a header line
because a header is required at the top of the markdown source page where the API docs
will be inserted using the ``automodule`` declaration, so we do not repeat it here.

That does mean that we need to stop ``flake8`` complaining about a missing blank line
after the first line and a missing full stop at the end of that line, which we can do
using the comment ``# noqa: D205, D415`` after the docstring closes.
"""  # noqa: D205

AN_OBJECT: str = "An object in the module"
"""This is a docstring for a module attribute."""


class MyClass:
    """This is my class.

    This is some text about my class

    Args:
        myarg: An argument used to create an instance of MyClass. Arguments are
            documented here in the class docstring and not in an __init__ docstring.
    """

    a_class_attribute: int = 0
    """A Class attribute.

    Attributes are documented with docstrings underneath the attribute definition. Class
    attributes are grouped with instance attributes in the rendered documentation, so
    should say explictly that they are a class attribute."""

    def __init__(self, myarg: int, name: str) -> None:
        # Note there is no __init__ docstring.

        self.myarg: int = myarg
        """The myarg value used to create the instance.

        All attributes of a class instance should be defined and typed in the __init__
        method, even if they are not used or populated in the __init__ method. This
        ensures that they are picked up and included in the rendered docstrings.
        """

        self.name: str = name
        """The instance name."""

        self.myarg_multiple: int
        """An instance attribute.

        This attribute is not populated in ``__init__`` but must be defined and
        documented here."""

    def __repr__(self) -> str:
        """Create a text representation of the class."""
        return f"MyClass: {self.name}"

    def multiply_me(self, factor: int) -> int:
        """Multiples myarg by a factor.

        Methods must define any arguments and provide Returns and Raises sections if
        appropriate.

        Args:
            factor: An integer factor by which to multiply self.myarg.

        Returns:
            The value of self.myarg multiplied by the provided factor. This result is
            also stored in ``self.myarg_multiple``.

        Raises:
            ValueError: if the provided factor is not an integer.
        """

        if not isinstance(factor, float):
            raise ValueError(f"The factor value {factor} is not an integer.")

        self.myarg_multiple = self.myarg * factor

        return self.myarg_multiple


def multiplier(arg1: int, arg2: int) -> int:
    """Multiply two integers.

    This function calculates the product of two integers. The docstring documents the
    arguments, return value and any exceptions that can be raised.

    Args:
        arg1: The first integer
        arg2: The second integer

    Returns:
        The product of the two integers.

    Raises:
        ValueError: if either argument is not an integer.
    """

    if not (isinstance(arg1, int) and isinstance(arg2, int)):
        raise ValueError("Both arguments must be integers")

    return arg1 * arg2
