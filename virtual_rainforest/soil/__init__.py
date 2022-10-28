import json
from pathlib import Path
from typing import Any

from numpy import datetime64, timedelta64

from virtual_rainforest.core.config import register_schema
from virtual_rainforest.core.logger import log_and_raise
from virtual_rainforest.core.model import register_model
from virtual_rainforest.soil.model import InitialisationError, SoilModel


@register_schema("soil")
def schema() -> dict:
    """Defines the schema that the soil module configuration should conform to."""

    schema_file = Path(__file__).parent.resolve() / "soil_schema.json"

    with schema_file.open() as f:
        config_schema = json.load(f)

    return config_schema


@register_model("soil")
def generate_soil_model(
    config: dict[str, Any],
) -> SoilModel:
    """Function that initialises the soil model.

    This function unpacks the relevant information from the configuration file, and then
    uses it to initialise the model.

    Args:
        config: The complete (and validated) virtual rainforest configuration.

    Raises:
        InitialisationError: If the information required to initialise the model either
            isn't found, or isn't of the correct type.
    """

    try:
        start_time = datetime64(config["core"]["timing"]["start_time"])
        end_time = datetime64(config["core"]["timing"]["end_time"])
        raw_interval = config["core"]["timing"]["update_interval"]
        # Round raw time interval to nearest minute
        update_interval = timedelta64(int(raw_interval * 24 * 60), "m")
        no_layers = config["soil"]["no_layers"]
    except KeyError as e:
        log_and_raise(
            f"Configuration is missing information required to initialise the soil "
            f"model. The first missing key is {str(e)}.",
            InitialisationError,
        )
    except ValueError as e:
        log_and_raise(
            f"Configuration types appear not to have been properly validated. This "
            f"problem prevents initialisation of the soil model. The first instance of "
            f"this problem is as follows: {str(e)}",
            InitialisationError,
        )

    # TODO - Add further relevant checks on input here as they become relevant

    return SoilModel(start_time, end_time, update_interval, no_layers)
