"""Testing experimental config system."""

import json
import tomllib

import tomli_w
from pydantic import create_model


def test_pydantic():
    """Builds a combined config model from all models and then dumps and reloads it."""
    from virtual_ecosystem.core.conf import CoreConfig
    from virtual_ecosystem.models.abiotic.config import AbioticConfig
    from virtual_ecosystem.models.abiotic_simple.config import AbioticSimpleConfig
    from virtual_ecosystem.models.animal.config import AnimalConfig
    from virtual_ecosystem.models.hydrology.config import HydrologyConfig
    from virtual_ecosystem.models.litter.config import LitterConfig
    from virtual_ecosystem.models.plants.config import PlantsConfig
    from virtual_ecosystem.models.soil.config import SoilConfig

    submodel_details = (
        ("core", CoreConfig),
        ("abiotic", AbioticConfig),
        ("animal", AnimalConfig),
        ("hydrology", HydrologyConfig),
        ("litter", LitterConfig),
        ("soil", SoilConfig),
        ("plants", PlantsConfig),
        ("abiotic_simple", AbioticSimpleConfig),
    )

    # Combine
    combined = create_model(
        "Config", **{fname: (cname, cname()) for fname, cname in submodel_details}
    )

    # Dump config to file
    with open("config.toml", "wb") as tomlfile:
        tomli_w.dump(json.loads(combined().model_dump_json()), tomlfile)

    # Reload it
    with open("config.toml", "rb") as tomlfile:
        config = combined().model_validate_json(json.dumps(tomllib.load(tomlfile)))

    # Very basic check for submodels
    for submodel, _ in submodel_details:
        assert hasattr(config, submodel)
