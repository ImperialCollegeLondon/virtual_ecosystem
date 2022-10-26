"""The `core.model` module.

The `core.model` module defines the api that all individual models (e.g. the soil
model) should conform to. This consists of a class (`Model`), which defines the expected
functions. The relevant modules will create classes to represent specific models, which
will inherit from the `Model` base class. These subclasses will generally overwrite the
functions defined in the base class, which are defined mainly to force a consistent api
between models. It also establishes a model registry that allows models to become
accessible across scripts without individual loading in.
"""

from numpy import datetime64, timedelta64

from virtual_rainforest.core.logger import log_and_raise

# TODO - Add a decorator here, once an inherited class has been defined. This should
# allow newly defined models to be added to a module registry


class Model:
    """A superclass for all `vr` models.

    Describes the common functions and attributes that all `vr` models should have. This
    includes functions to setup, spin up and solve the specific model, as well as a
    function to cleanup redundant model data. At this level these functions are not
    define and are mere placeholders to be overwritten (where appropriate) by the
    inheriting classes.

    Args:
        start_time: Point in time that the model simulation should be started.
        end_time: Time that the model simulation should end
        update_interval: Time to wait between updates of the model state.

    Attributes:
        name: Names the model that is described
    """

    name = "base model"

    def setup(self) -> None:
        """Function to use input data to set up the model."""
        pass

    def spinup(self) -> None:
        """Function to spin up the model."""
        pass

    def solve(self) -> None:
        """Function to solve the model."""
        pass

    def cleanup(self) -> None:
        """Function to delete objects within the class that are no longer needed."""
        pass

    def __repr__(self) -> str:
        """Represent a Model as a string."""
        return (
            f"Model(start_time={self.start_time}, end_time={self.end_time}, "
            f"update_interval={self.update_interval})"
        )

    def __str__(self) -> str:
        """Inform user what the model type is."""
        return f"A {self.name} instance"

    def __init__(
        self, start_time: datetime64, end_time: datetime64, update_interval: timedelta64
    ):
        if start_time > end_time:
            log_and_raise(
                "Model cannot end at an earlier time than it starts!", ValueError
            )

        self.start_time: datetime64 = start_time
        self.end_time: datetime64 = end_time
        self.update_interval: timedelta64 = update_interval
