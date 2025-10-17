"""Testing experimental config system."""

import json
import tomllib
from contextlib import nullcontext as does_not_raise
from importlib import import_module

import pytest
import tomli_w
from pydantic import create_model


def test_pydantic(tmp_path):
    """Builds a combined config model from all models and then dumps and reloads it."""

    modules = (
        "virtual_ecosystem.core",
        "virtual_ecosystem.models.abiotic",
        "virtual_ecosystem.models.abiotic_simple",
        "virtual_ecosystem.models.animal",
        "virtual_ecosystem.models.hydrology",
        "virtual_ecosystem.models.litter",
        "virtual_ecosystem.models.plants",
        "virtual_ecosystem.models.soil",
    )

    submodel_details = {}
    for module_name in modules:
        module = import_module(f"{module_name}.model_config")
        config_class = getattr(module, "ModelConfiguration")
        submodel_details[module_name.split(".")[-1]] = (config_class, config_class())

    # Combine
    combined = create_model("Config", **submodel_details)

    # Dump config to file
    with open("config.toml", "wb") as tomlfile:
        tomli_w.dump(json.loads(combined().model_dump_json()), tomlfile)

    # Reload it - substituting path placeholders for a temporary real file.
    tmp_file = tmp_path / "temp_file.txt"
    tmp_file.touch()

    with open("config.toml") as tomlfile:
        content = tomlfile.read()
        content = content.replace('"<PLACEHOLDER>"', f"'{tmp_file!s}'")
        content_parsed = tomllib.loads(content)
        config = combined().model_validate_json(json.dumps(content_parsed))

    tmp_file.unlink()

    # Very basic check for submodels
    for submodel in submodel_details:
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
