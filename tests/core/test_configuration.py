"""Testing experimental config system."""

import json
import tomllib
from contextlib import nullcontext as does_not_raise
from importlib import import_module

import pytest
import tomli_w
from pydantic import create_model


def test_pydantic_models(tmp_path):
    """Build a combined config model from all models and then dump and reload it."""

    modules = (
        ("virtual_ecosystem.core", "CoreConfiguration"),
        ("virtual_ecosystem.models.abiotic", "AbioticConfiguration"),
        ("virtual_ecosystem.models.abiotic_simple", "AbioticSimpleConfiguration"),
        ("virtual_ecosystem.models.animal", "AnimalConfiguration"),
        ("virtual_ecosystem.models.hydrology", "HydrologyConfiguration"),
        ("virtual_ecosystem.models.litter", "LitterConfiguration"),
        ("virtual_ecosystem.models.plants", "PlantsConfiguration"),
        ("virtual_ecosystem.models.soil", "SoilConfiguration"),
        ("virtual_ecosystem.models.testing", "TestingConfiguration"),
        (
            "virtual_ecosystem.disturbances.disturbance_testing",
            "DisturbanceTestingConfiguration",
        ),
    )

    submodel_details = {}
    for module_name, config_name in modules:
        module = import_module(f"{module_name}.model_config")
        config_class = getattr(module, config_name)
        submodel_details[module_name.split(".")[-1]] = (config_class, config_class())

    # Combine
    combined = create_model("Config", **submodel_details)

    # Dump config to file
    config_path = tmp_path / "config.toml"
    with open(config_path, "wb") as tomlfile:
        tomli_w.dump(json.loads(combined().model_dump_json()), tomlfile)

    # Reload it - substituting path placeholders for a temporary real file.
    tmp_file = tmp_path / "temp_file.txt"
    tmp_file.touch()

    with open(config_path) as tomlfile:
        content = tomlfile.read()
        content = content.replace('"<FILEPATH_PLACEHOLDER>"', f"'{tmp_file!s}'")
        content = content.replace('"<DIRPATH_PLACEHOLDER>"', f"'{tmp_path!s}'")
        content_parsed = tomllib.loads(content)
        config = combined().model_validate_json(json.dumps(content_parsed))

    tmp_file.unlink()
    config_path.unlink()

    # Very basic check for submodels
    for submodel in submodel_details:
        assert hasattr(config, submodel)


@pytest.mark.parametrize(argnames="toggle_test", argvalues=(True, False))
def test_path_validation(tmp_path, toggle_test):
    """Validate the validation of custom path fields.

    The toggle_test argument switches between testing FILEPATH_VALIDATOR and
    DIRPATH_VALIDATOR, which differ in their default placeholders and whether the
    provided path must be a file or a directory.
    """
    from pydantic import TypeAdapter, ValidationError

    from virtual_ecosystem.core.configuration import (
        DIRPATH_PLACEHOLDER,
        FILEPATH_PLACEHOLDER,
    )

    field = FILEPATH_PLACEHOLDER if toggle_test else DIRPATH_PLACEHOLDER
    # Hack the default from the field metadata.
    default = field.__metadata__[1].default

    placeholder_field = TypeAdapter(field)

    # Object early to <FILEPATH_PLACEHOLDER> patterns in input
    with pytest.raises(ValidationError) as err:
        placeholder_field.validate_python(default)
        assert str(err) == "Path placeholder value in configuration."

    # Object to file path not existing - handled by pydantic
    with pytest.raises(ValidationError) as err:
        placeholder_field.validate_python("no_such_file")
        assert str(err) == "Path does not point to a file"

    # Object to unknown file marker
    with pytest.raises(ValidationError) as err:
        placeholder_field.validate_python("$CONFIG_PATH")
        assert str(err) == "Undefined path marker: $CONFIG_PATH"

    # Generate a file or dir to pass in.
    if toggle_test:
        tmp_file = tmp_path / "file_to_find.txt"
        tmp_file.touch()
    else:
        tmp_file = tmp_path

    # Do not object when the path exists
    with does_not_raise():
        placeholder_field.validate_python(tmp_file)

    # Provide a context mapping a marker to the path
    context = {"cli_paths": {"CONFIG_PATH": str(tmp_file)}}

    with does_not_raise():
        placeholder_field.validate_python("$CONFIG_PATH", context=context)
