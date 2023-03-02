"""The ``core.utility_functions`` module contains functions that are used across the
Virtual Rainforest, but which don't have a natural home in a specific module. At the
moment, this module only contains a single function, but it will probably expand in
future. Adding functions here can be a good way to reduce the amount boiler plate code
generated for tasks that are repeated across modules.
"""  # noqa: D205, D415

from typing import Any

import pint
from numpy import datetime64, timedelta64


# TODO - WRITE TEST FOR THIS
# TODO - IMPROVE MODEL SETUP DOCUMENTATION TO REFLECT THIS
def extract_model_time_details(
    config: dict[str, Any], model_name: str
) -> tuple[datetime64, timedelta64]:
    """Function to extract the timing details required to setup a specific model.

    Args:
        config: The configuration for the Virtual Rainforest simulation.
        model_name: The name of the specific model of interest.

    Returns:
        A tuple containing the start date and the update interval for the model

    Raises:
        pint.errors.DimensionalityError: If the desired conversion between units isn't
            possible, e.g. kg to s.
        pint.errors.UndefinedUnitError: If the unit is not known to pint.
    """

    raw_interval = pint.Quantity(config[model_name]["model_time_step"]).to("minutes")
    # Round raw time interval to nearest minute
    update_interval = timedelta64(int(round(raw_interval.magnitude)), "m")

    start_date = datetime64(config["core"]["timing"]["start_date"])

    return start_date, update_interval
