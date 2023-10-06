"""A test module to test module registration."""

from virtual_rainforest.core.base_model import BaseModel


class TestModel(BaseModel):
    """A test module."""

    model_name = "name"
    required_init_vars = tuple()
    lower_bound_on_time_scale = "1 day"
    upper_bound_on_time_scale = "1 month"
    vars_updated = tuple()
