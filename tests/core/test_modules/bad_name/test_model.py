"""A test module to test module registration."""

from virtual_ecosystem.core.base_model import BaseModel


class ATestModel(
    BaseModel,
    model_name="name_is_not_bad_name",
    vars_required_for_init=tuple(),
    model_update_bounds=("1 day", "1 month"),
    vars_updated=tuple(),
    vars_required_for_update=tuple(),
    vars_populated_by_init=tuple(),
    vars_populated_by_first_update=tuple(),
):
    """A test module."""
