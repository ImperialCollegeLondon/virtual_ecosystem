import json
from pathlib import Path

from virtual_rainforest.core.config import register_schema
from virtual_rainforest.models.abiotic.abiotic_model import AbioticModel  # noqa: F401


@register_schema("abiotic")
def schema() -> dict:
    """Defines the schema that the abiotic module configuration should conform to."""

    schema_file = Path(__file__).parent.resolve() / "abiotic_schema.json"

    with schema_file.open() as f:
        config_schema = json.load(f)

    return config_schema
