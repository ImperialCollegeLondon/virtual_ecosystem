"""The ''plant_resources'' classes provides toy plant module functionality that are
required for setting up and testing the early stages of the animal module.
"""  # noqa: D205

from virtual_ecosystem.core.data import Data
from virtual_ecosystem.models.animal.animal_traits import VerticalOccupancy
from virtual_ecosystem.models.animal.protocols import Consumer


class PlantResourcePool:
    """Tracks plant resources for a specific functional group in one grid cell."""

    def __init__(
        self,
        cell_id: int,
        functional_group_name: str,
        data: "Data",
        cell_area: float,
    ) -> None:
        self.cell_id = cell_id
        self.functional_group_name = functional_group_name
        self.vertical_occupancy = VerticalOccupancy.CANOPY

        # Optional fields, default to zero if missing
        self.leaf_mass = (
            data["layer_leaf_mass"]
            .sel(cell_id=cell_id, plant_functional_type=functional_group_name)
            .item()
            * cell_area
            if "layer_leaf_mass" in data
            else 0.0
        )

        self.canopy_n_propagules = (
            data["canopy_n_propagules"]
            .sel(cell_id=cell_id, plant_functional_type=functional_group_name)
            .item()
            if "canopy_n_propagules" in data
            else 0.0
        )

        self.fallen_n_propagules = (
            data["fallen_n_propagules"]
            .sel(cell_id=cell_id, plant_functional_type=functional_group_name)
            .item()
            if "fallen_n_propagules" in data
            else 0.0
        )

        self.subcanopy_veg_mass = (
            data["subcanopy_vegetation_biomass"]
            .sel(cell_id=cell_id, plant_functional_type=functional_group_name)
            .item()
            * cell_area
            if "subcanopy_vegetation_biomass" in data
            else 0.0
        )

        self.seedbank_mass = (
            data["subcanopy_seedbank_biomass"]
            .sel(cell_id=cell_id, plant_functional_type=functional_group_name)
            .item()
            * cell_area
            if "subcanopy_seedbank_biomass" in data
            else 0.0
        )

    @property
    def mass_current(self) -> float:
        """Total available plant biomass for this pool."""
        return self.leaf_mass + self.subcanopy_veg_mass

    def get_eaten(
        self,
        consumed_mass: float,
        consumer: "Consumer",
    ) -> tuple[dict[str, float], dict[str, float]]:
        """Placeholder to satisfy the Resource protocol."""
        raise NotImplementedError(
            "Resource-specific get_eaten logic not yet implemented."
        )
