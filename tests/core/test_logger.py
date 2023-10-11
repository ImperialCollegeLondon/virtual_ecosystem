"""Testing the logger functions."""

from logging import INFO
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from tests.conftest import log_check


@pytest.fixture
def teardown_hook():
    """Logger test teardown hook.

    Does not provide anything but acts as a teardown to remove file handlers if the
    tests fail for some reason.
    """
    from virtual_rainforest.core.logger import remove_file_logger

    yield
    # Code following the yield will be executed by pytest during test cleanup, so should
    # remove any remaining file loggers.
    remove_file_logger()


def test_add_file_logger(teardown_hook):
    """Test the add_file_logger function works."""
    from virtual_rainforest.core.logger import LOGGER, add_file_logger

    with TemporaryDirectory() as tempdir:
        tempfile = Path(tempdir) / "test_add_file_logger.log"
        add_file_logger(logfile=tempfile)
        LOGGER.info("Message logged")

        # Check the handler has been created by looking for it by name - this will raise
        # with StopIteration if it fails.
        _ = next(handler for handler in LOGGER.handlers if handler.name == "vr_logfile")

        # Check the file is being written to
        assert tempfile.exists()
        with open(tempfile) as tempfile_io:
            contents = tempfile_io.readlines()
            assert len(contents) == 1
            assert (
                contents[0]
                == "[INFO] - test_logger - test_add_file_logger(34) - Message logged\n"
            )


def test_add_file_logger_twice_fails(teardown_hook):
    """Test that add_logger function works."""
    from virtual_rainforest.core.logger import add_file_logger

    with TemporaryDirectory() as tempdir:
        tempfile = Path(tempdir) / "test_add_logger.log"
        add_file_logger(logfile=tempfile)

        with pytest.raises(RuntimeError) as excep:
            add_file_logger(logfile=tempfile)

        assert str(excep.value).startswith("Already logging to file:")


def test_remove_file_logger(caplog, teardown_hook):
    """Tests that remove_file_logger behaves as expected."""
    from virtual_rainforest.core.logger import (
        LOGGER,
        add_file_logger,
        remove_file_logger,
    )

    with TemporaryDirectory() as tempdir:
        tempfile = Path(tempdir) / "test_add_logger.log"
        add_file_logger(logfile=tempfile)

        # Remove the handler and check it is gone
        remove_file_logger()

        with pytest.raises(StopIteration):
            _ = next(
                handler for handler in LOGGER.handlers if handler.name == "vr_logfile"
            )

        # Check the logging works
        LOGGER.info("Stream handler back")

        log_check(
            caplog=caplog,
            expected_log=[
                (INFO, "Stream handler back"),
            ],
        )

        # Check that calling remove_file_logger works cleanly when there is no existing
        # file logger
        remove_file_logger()
