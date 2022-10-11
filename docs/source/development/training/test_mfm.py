# flake8: noqa D103 - docstrings on unit tests

import pytest
from mfm import TimesTable, my_float_multiplier, my_picky_float_multiplier


def test_fm() -> None:

    assert 10 == my_float_multiplier(2, 5)


def test_pfm() -> None:

    with pytest.raises(ValueError) as err_hndlr:

        x = my_picky_float_multiplier(2, 5)

    assert str(err_hndlr.value) == "Both x and y must be of type float"


def test_pfm_fail() -> None:

    with pytest.raises(ValueError) as err_hndlr:

        x = my_picky_float_multiplier(2.0, 5.0)

    assert str(err_hndlr.value) == "Both x and y must be of type float"


@pytest.mark.parametrize(
    argnames=["x", "y", "expected"],
    argvalues=[
        (1.0, 3.0, 3.0),
        (1.5, -3.0, -4.5),
        (-1.5, 3.0, -4.5),
        (-1.5, -3.0, 4.5),
    ],
)
def test_pfm_param_noid(x: float, y: float, expected: float) -> None:

    assert expected == my_picky_float_multiplier(x, y)


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
def test_pfm_param_ids(x: float, y: float, expected: float) -> None:

    assert expected == my_picky_float_multiplier(x, y)


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
def test_pfm_twoparam(x: float, y: float) -> None:

    assert 4.5 == abs(my_picky_float_multiplier(x, y))


@pytest.fixture
def twoparam_expected() -> dict[str, float]:

    expected = {"+-+": 4.5, "---": 4.5, "--+": -4.5, "+--": -4.5}
    return expected


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
def test_pfm_twoparam_fixture(
    request: pytest.FixtureRequest,
    twoparam_expected: dict[str, float],
    x: float,
    y: float,
) -> None:

    expected = twoparam_expected[request.node.callspec.id]

    assert expected == my_picky_float_multiplier(x, y)


@pytest.fixture()
def times_table_instance() -> TimesTable:
    return TimesTable(num=7)


def test_times_table_errors(times_table_instance: TimesTable) -> None:

    with pytest.raises(TypeError) as err_hndlr:
        times_table_instance.table(1.6, 23.9)  # type: ignore

    assert str(err_hndlr.value) == "'float' object cannot be interpreted as an integer"


def test_times_table_values(times_table_instance: TimesTable) -> None:

    value = times_table_instance.table(2, 7)
    assert value == [14, 21, 28, 35, 42, 49]
