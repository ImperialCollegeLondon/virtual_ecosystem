"""Module for all variables."""
from dataclasses import dataclass


@dataclass
class Variable:
    """Base class for all variables."""

    name: str
    description: str
    units: str

    def __post_init__(self) -> None:
        """Post init populates the registry."""
        if self.name in VARIABLES_REGISTRY:
            raise ValueError(f"Variable {self.name} already in registry")

        VARIABLES_REGISTRY[self.name] = self


VARIABLES_REGISTRY: dict[str, Variable] = {}


if __name__ == "__main__":
    Variable(name="temperature", description="The temperature", units="K")
    """Temperature variable."""

    Variable(name="pressure", description="The pressure", units="Pa")
    """Pressure variable."""

    print(VARIABLES_REGISTRY)

    assert "pressure" in VARIABLES_REGISTRY
    assert "temperature" in VARIABLES_REGISTRY
    assert "soil_moisture" not in VARIABLES_REGISTRY

    var_info = VARIABLES_REGISTRY["temperature"]
    assert var_info.units == "K"
