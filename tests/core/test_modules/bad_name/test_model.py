"""A test module to test module registration."""

from virtual_ecosystem.core.base_model import BaseModel


class ATestModel(
    BaseModel,
    model_name="name_is_not_bad_name",
    required_init_vars=tuple(),
    model_update_bounds=("1 day", "1 month"),
    vars_updated=tuple(),
    required_update_vars=tuple(),
    populated_by_init_vars=tuple(),
    populated_by_update_vars=tuple(),
):
    """A test module."""
