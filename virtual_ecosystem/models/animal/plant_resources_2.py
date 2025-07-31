"""The ''plant_resources'' classes provides toy plant module functionality that are
required for setting up and testing the early stages of the animal module.
"""  # noqa: D205

from virtual_ecosystem.core.data import Data

# from virtual_ecosystem.models.animal.animal_traits import VerticalOccupancy
from virtual_ecosystem.models.animal.protocols import Consumer


class PlantResourcePool:
    """A class to track plant biomass resources in a given grid cell.

    This generic class reads a plant biomass value from the `data` object and stores
    current mass for resource use (e.g. herbivory).

    Args:
        cell_id: The grid cell ID.
        data: The Data object containing the variable.
        variable_name: The name of the data variable in `data`.
        cell_area: Area of the grid cell in m² (used if data is in per-area units).
    """

    def __init__(
        self,
        cell_id: int,
        data: "Data",
        variable_name: str,
        cell_area: float,
    ) -> None:
        self.cell_id = cell_id
        self.variable_name = variable_name

        # Get per-area biomass value and convert to absolute mass
        biomass_per_area = data[variable_name].sel(cell_id=cell_id).item()
        self.mass_current: float = biomass_per_area * cell_area

        if self.mass_current < 0:
            raise ValueError(
                f"{variable_name}: negative biomass value in cell {cell_id}: "
                f"{self.mass_current} kg"
            )

    def get_eaten(
        self,
        consumed_mass: float,
        consumer: "Consumer",
    ) -> tuple[dict[str, float], dict[str, float]]:
        """Simulate consumption of the plant resource by a consumer.

        Args:
            consumed_mass: Target wet-mass to consume **after** mechanical efficiency is
              applied (kg).
            consumer: The AnimalCohort or similar consumer.

        Returns:
            Tuple of:
              - dict of element masses assimilated by consumer (currently just 'carbon')
              - dict of losses (currently empty).
        """
        if consumed_mass < 0:
            raise ValueError("consumed_mass must be non-negative")

        mech_eff = consumer.functional_group.mechanical_efficiency
        actual = min(consumed_mass, self.mass_current) * mech_eff

        # Simple carbon-only return for now
        taken = {"carbon": actual}
        self.mass_current -= actual
        return taken, {}
