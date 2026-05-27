"""Testing experimental config system."""

import json
import os
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


def test_filepath_placeholder(tmp_path):
    """Validate the FILEPATH_PLACEHOLDER custom field."""
    from pydantic import TypeAdapter, ValidationError

    from virtual_ecosystem.core.configuration import (
        FILEPATH_PLACEHOLDER,
    )

    placeholder_field = TypeAdapter(FILEPATH_PLACEHOLDER)

    # Object early to <FILEPATH_PLACEHOLDER> patterns in input
    with pytest.raises(ValidationError) as err:
        placeholder_field.validate_python("<FILEPATH_PLACEHOLDER>")
        assert str(err) == "Path placeholder value in configuration."

    # Object to file path not existing
    with pytest.raises(ValidationError) as err:
        placeholder_field.validate_python("no_such_file.py")
        assert str(err) == "Path does not point to a file"

    # Object to an unknown environment variable
    with pytest.raises(ValidationError) as err:
        placeholder_field.validate_python("$NO_SUCH_ENV_VAR")
        assert str(err) == "Path set by undefined marker: $NO_SUCH_ENV_VAR"

    # Object when an environment variable does not point to a known file
    os.environ["CONFIG_PATH"] = "no_such_file.py"

    # Object to file path not existing
    with pytest.raises(ValidationError) as err:
        placeholder_field.validate_python("$CONFIG_PATH")
        assert str(err) == "Path does not point to a file"

    # Do not object when the path exists either directly or via environment variable
    tmp_file = tmp_path / "file_to_find.txt"
    tmp_file.touch()
    os.environ["CONFIG_PATH"] = str(tmp_file)

    with does_not_raise():
        placeholder_field.validate_python(tmp_file)
        placeholder_field.validate_python("$CONFIG_PATH")

    # Test marker cannot be set by context and environment
    context = {"cli_paths": {"CONFIG_PATH": str(tmp_file)}}

    with pytest.raises(ValidationError) as err:
        placeholder_field.validate_python("$CONFIG_PATH", context=context)
        assert str(err) == (
            "Path marker defined in both environment variables "
            "and command line arguments : $CONFIG_PATH"
        )

    # Test context works when no environment variable clashing
    del os.environ["CONFIG_PATH"]

    with does_not_raise():
        placeholder_field.validate_python("$CONFIG_PATH", context=context)

    tmp_file.unlink()


def test_dirpath_placeholder(tmp_path):
    """Validate the DIRPATH_PLACEHOLDER custom field."""
    from pydantic import TypeAdapter, ValidationError

    from virtual_ecosystem.core.configuration import DIRPATH_PLACEHOLDER

    placeholder_field = TypeAdapter(DIRPATH_PLACEHOLDER)

    # Object early to <DIRPATH_PLACEHOLDER> patterns in input
    with pytest.raises(ValidationError) as err:
        placeholder_field.validate_python("<DIRPATH_PLACEHOLDER>")
        assert str(err) == "Path placeholder value in configuration."

    # Object to file path not existing
    with pytest.raises(ValidationError) as err:
        placeholder_field.validate_python("no_such_file_dir")
        assert str(err) == "Path does not point to a file"

    # Object to an unknown environment variable
    with pytest.raises(ValidationError) as err:
        placeholder_field.validate_python("$NO_SUCH_ENV_VAR")
        assert (
            str(err) == "Path set by undefined environment variable: $NO_SUCH_ENV_VAR"
        )

    # Object when an environment variable does not point to a known file
    os.environ["CONFIG_PATH"] = "no_such_file_dir"
    # Object to file path not existing
    with pytest.raises(ValidationError) as err:
        placeholder_field.validate_python("$CONFIG_PATH")
        assert str(err) == "Path does not point to a file"

    # Test marker cannot be set by context and environment
    context = {"cli_paths": {"CONFIG_PATH": str(tmp_path)}}

    with pytest.raises(ValidationError) as err:
        placeholder_field.validate_python("$CONFIG_PATH", context=context)
        assert str(err) == (
            "Path marker defined in both environment variables "
            "and command line arguments : $CONFIG_PATH"
        )

    # Test context works when no environment variable clashing
    del os.environ["CONFIG_PATH"]

    with does_not_raise():
        placeholder_field.validate_python("$CONFIG_PATH", context=context)
