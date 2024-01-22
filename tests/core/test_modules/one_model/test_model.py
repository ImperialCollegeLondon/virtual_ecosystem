"""A test module to test module registration."""

from virtual_rainforest.core.base_model import BaseModel


class ATestModel(
    BaseModel,
    model_name="one_model",
    required_init_vars=tuple(),
    model_update_bounds=("1 day", "1 month"),
    vars_updated=tuple(),
):
    """A test module."""
