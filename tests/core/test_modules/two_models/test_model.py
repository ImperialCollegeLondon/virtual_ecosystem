"""A test module to test module registration."""

from virtual_rainforest.core.base_model import BaseModel


class ATestModel1(BaseModel):
    """A test module."""

    model_name = "two_models"
    required_init_vars = tuple()
    lower_bound_on_time_scale = "1 day"
    upper_bound_on_time_scale = "1 month"
    vars_updated = tuple()


class ATestModel2(BaseModel):
    """A second unwanted test module."""

    model_name = "two_models"
    required_init_vars = tuple()
    lower_bound_on_time_scale = "1 day"
    upper_bound_on_time_scale = "1 month"
    vars_updated = tuple()
