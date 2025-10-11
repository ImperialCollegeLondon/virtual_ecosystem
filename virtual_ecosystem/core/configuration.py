"""Configuration system elements for pydantic."""

from pathlib import Path
from typing import Annotated, TypeAlias

from pydantic import BaseModel, BeforeValidator, Field, FilePath


class ModelConfig(BaseModel):
    """Root configuration class for models.

    This model provides a common base class for all model implementations. It defines
    the shared ``static`` option for each model. Each model should define a single class
    inheriting from :class:`ModelConfig` in the ``model_config.py`` submodule. This file
    can contain other :class:`pydantic.BaseModel` classes, but there must be a single
    root model configuration class.
    """

    static: bool = False
    """The model static mode setting."""


def placeholder_validator(path: str) -> str:
    """A custom validator to reject "<PLACEHOLDER>" when loading file paths."""
    if path == "<PLACEHOLDER>":
        raise ValueError("Path placeholder value in configuration.")

    return path


FILEPATH_PLACEHOLDER: TypeAlias = Annotated[
    FilePath,
    Field(default=Path("<PLACEHOLDER>")),
    BeforeValidator(placeholder_validator),
]
"""Pydantic type that provides a default '<PLACEHOLDER>' text for writing configuration
templates, but screens input before the standard validation to refuse unreplaced
placeholder values. The type then uses FilePath, which validates that a path actually
exists on the file system. The field does not set ``validate_defaults`` so the
placeholder value can be written despite not being an existing file.

.. TODO: Fix autodoc
    This generates a bizarre set of autodoc link failures that generate random text 
    chunks from the Annotator pattern. Currently tackled using nitpick ignore.
"""
