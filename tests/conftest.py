"""Collection of fixtures to assist the testing scripts."""

import pytest

# An import of LOGGER is required for INFO logging events to be visible to tests
# This can be removed as soon as a script that imports logger is imported
import virtual_rainforest.core.logger  # noqa


def log_check(caplog: pytest.LogCaptureFixture, expected_log: tuple[tuple]) -> None:
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
