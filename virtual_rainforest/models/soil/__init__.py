import json
from pathlib import Path

from virtual_rainforest.core.config import register_schema
from virtual_rainforest.models.soil.soil_model import SoilModel  # noqa: F401


@register_schema("soil")
def schema() -> dict:
    """Defines the schema that the soil module configuration should conform to."""

    schema_file = Path(__file__).parent.resolve() / "soil_schema.json"

    with schema_file.open() as f:
        config_schema = json.load(f)

    return config_schema
