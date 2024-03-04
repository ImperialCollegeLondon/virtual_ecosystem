"""Testing the logger functions.

Note the use of the autouse teardown_hook fixture. This  acts as a safeguard against
failing tests leaving active file loggers on the vr LOGGER instance, which then causes
interference _between_ tests. Each individual test should clear up its own logger setup
but if a test fails, this fixture should tidy up and stop logger issues propagating
across tests.

In addition, Windows cannot exit ``with TemporaryDirectory`` blocks cleanly while the
file being used by a FileHandler is still open, so these need to explicitly closed down
using ``remove_file_handler`` inside the ``with`` rather than relying on the teardown
hook to close the file when the test exits.
"""

from logging import INFO
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from tests.conftest import log_check


@pytest.fixture(autouse=True)
def teardown_hook():
    """Logger test teardown hook."""
    from virtual_ecosystem.core.logger import remove_file_logger

    yield

    # Code following the yield will be executed by pytest during test cleanup, so should
    # remove any remaining file loggers.
    remove_file_logger()


def test_add_file_logger():
    """Test the add_file_logger function works."""
    from virtual_ecosystem.core.logger import (
        LOGGER,
        add_file_logger,
        remove_file_logger,
    )

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
                == "[INFO] - test_logger - test_add_file_logger(47) - Message logged\n"
            )

        # Close the logger to shut down open files within the TemporaryDirectory block
        remove_file_logger()


def test_add_file_logger_twice_fails():
    """Test that add_logger function works."""
    from virtual_ecosystem.core.logger import add_file_logger, remove_file_logger

    with TemporaryDirectory() as tempdir:
        tempfile = Path(tempdir) / "test_add_file_logger.log"
        add_file_logger(logfile=tempfile)

        with pytest.raises(RuntimeError) as excep:
            add_file_logger(logfile=tempfile)

        assert str(excep.value).startswith("Already logging to file:")

        # Close the logger to shut down open files within the TemporaryDirectory block
        remove_file_logger()


def test_remove_file_logger(caplog):
    """Tests that remove_file_logger behaves as expected."""
    from virtual_ecosystem.core.logger import (
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
        # file logger.
        remove_file_logger()
