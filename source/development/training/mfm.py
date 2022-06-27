"""Demonstrate docstring.

Some example code used to demonstrate docstrings
"""

# flake8: noqa D202, D107

from typing import List
from pydantic import validate_arguments

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
        raise ValueError("Both x and y must be of type float")

    return x * y


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


@validate_arguments
def my_validated_float_multiplier(x: float, y: float) -> float:
    """Multiplies two floats together.

    Arguments:
        x: The first number
        y: The second number

    Examples:
        >>> my_float_multiplier(2.1, 3.6)
        7.56
    """

    return x * y

