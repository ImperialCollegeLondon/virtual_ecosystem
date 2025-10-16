"""Testing experimental config system."""

import json
import tomllib
from contextlib import nullcontext as does_not_raise

import pytest
import tomli_w
from pydantic import create_model


def test_pydantic(tmp_path):
    """Builds a combined config model from all models and then dumps and reloads it."""
    from virtual_ecosystem.core.model_config import CoreConfig
    from virtual_ecosystem.models.abiotic.model_config import AbioticConfig
    from virtual_ecosystem.models.abiotic_simple.model_config import AbioticSimpleConfig
    from virtual_ecosystem.models.animal.model_config import AnimalConfig
    from virtual_ecosystem.models.hydrology.model_config import HydrologyConfig
    from virtual_ecosystem.models.litter.model_config import LitterConfig
    from virtual_ecosystem.models.plants.model_config import PlantsConfig
    from virtual_ecosystem.models.soil.model_config import SoilConfig

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
    config_path = tmp_path / "config.toml"
    with open(config_path, "wb") as tomlfile:
        tomli_w.dump(json.loads(combined().model_dump_json()), tomlfile)

    # Reload it - substituting path placeholders for a temporary real file.
    tmp_file = tmp_path / "temp_file.txt"
    tmp_file.touch()

    with open(config_path) as tomlfile:
        content = tomlfile.read()
        content = content.replace('"<PLACEHOLDER>"', f"'{tmp_file!s}'")
        content_parsed = tomllib.loads(content)
        config = combined().model_validate_json(json.dumps(content_parsed))

    tmp_file.unlink()
    config_path.unlink()

    # Very basic check for submodels
    for submodel, _ in submodel_details:
        assert hasattr(config, submodel)


def test_filepath_placeholder(tmp_path):
    """Validate the FILEPATH_PLACEHOLDER custom field."""
    from pydantic import TypeAdapter, ValidationError

    from virtual_ecosystem.core.configuration import FILEPATH_PLACEHOLDER

    filepath_placeholder_field = TypeAdapter(FILEPATH_PLACEHOLDER)

    # Object early to <PLACEHOLDER> in input
    with pytest.raises(ValidationError) as err:
        filepath_placeholder_field.validate_python("<PLACEHOLDER>")

        assert str(err) == "Path placeholder value in configuration."

    # Object to file path not existing
    with pytest.raises(ValidationError) as err:
        filepath_placeholder_field.validate_python("no_such_file.py")

        assert str(err) == "Path does not point to a file"

    # Do not object when the path exists.
    tmp_file = tmp_path / "file_to_find.txt"
    tmp_file.touch()
    with does_not_raise():
        filepath_placeholder_field.validate_python(tmp_file)
    tmp_file.unlink()
