# flake8: noqa D103 - docstrings on unit tests

import pytest
from mfm import TimesTable, my_float_multiplier, my_picky_float_multiplier


def test_fm():

    assert 10 == my_float_multiplier(2, 5)


def test_pfm():

    with pytest.raises(ValueError) as err_hndlr:

        x = my_picky_float_multiplier(2, 5)

    assert str(err_hndlr.value) == "Both x and y must be of type float"


def test_pfm_fail():

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
def test_pfm_param_noid(x, y, expected):

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
def test_pfm_param_ids(x, y, expected):

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
def test_pfm_twoparam(x, y):

    assert 4.5 == abs(my_picky_float_multiplier(x, y))


@pytest.fixture
def twoparam_expected():

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
def test_pfm_twoparam_fixture(request, twoparam_expected, x, y):

    expected = twoparam_expected[request.node.callspec.id]

    assert expected == my_picky_float_multiplier(x, y)


@pytest.fixture()
def times_table_instance():
    return TimesTable(num=7)


def test_times_table_errors(times_table_instance):

    with pytest.raises(TypeError) as err_hndlr:
        times_table_instance.table(1.6, 23.9)

    assert str(err_hndlr.value) == "'float' object cannot be interpreted as an integer"


def test_times_table_values(times_table_instance):

    value = times_table_instance.table(2, 7)
    assert value == [14, 21, 28, 35, 42, 49]
