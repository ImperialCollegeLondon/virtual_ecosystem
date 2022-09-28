"""Collection of fixtures to assist the testing scripts."""

from virtual_rainforest.core.config import register_schema


def log_check(caplog, expected_log):
    """Helper function to check that the captured log is as expected.

    Arguments:
        caplog: An instance of the caplog fixture
        expected_log: An iterable of 2-tuples containing the
            log level and message.
    """

    assert len(expected_log) == len(caplog.records)

    assert all(
        [exp[0] == rec.levelno for exp, rec in zip(expected_log, caplog.records)]
    )
    assert all(
        [exp[1] in rec.message for exp, rec in zip(expected_log, caplog.records)]
    )


# Register a bunch of schema so that schema validation can be appropriately tested
@register_schema("bad_module_1")
def test_schema1():
    """Defines a (bad) test schema for unit testing."""

    config_schema = {
        "type": "object",
        "properties": {
            "bad_module_1": {
                "type": "object",
                "properties": {
                    "an_integer": {
                        "type": "integer",
                    },
                },
                "required": ["an_integer"],
            }
        },
    }

    return config_schema


@register_schema("bad_module_2")
def test_schema2():
    """Defines another (bad) test schema for unit testing."""

    config_schema = {
        "type": "object",
        "propertie": {
            "bad_module_2": {
                "type": "object",
                "properties": {
                    "an_integer": {
                        "type": "integer",
                    },
                },
                "required": ["an_integer"],
            }
        },
        "required": ["bad_module_2"],
    }

    return config_schema
