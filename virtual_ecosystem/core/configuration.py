"""Configuration system elements for pydantic."""

from pydantic import BaseModel


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
