"""The ''plant_resources'' classes provides toy plant module functionality that are
required for setting up and testing the early stages of the animal module.
"""  # noqa: D205

from virtual_ecosystem.core.data import Data
from virtual_ecosystem.models.animal.animal_traits import VerticalOccupancy
from virtual_ecosystem.models.animal.protocols import Consumer


class AggregatedPlantResource:
    """Resource pool aggregating plant mass by resource type."""

    def __init__(
        self,
        cell_id: int,
        resource_name: str,
        data: "Data",
        functional_types: list[str],
        cell_area: float,
        vertical_occupancy: VerticalOccupancy,
        variable_name: str,
    ) -> None:
        self.cell_id = cell_id
        self.resource_name = resource_name
        self.vertical_occupancy = vertical_occupancy

        self.mass_by_fg: dict[str, float] = {}

        for fg in functional_types:
            if variable_name not in data:
                continue

            try:
                per_area = (
                    data[variable_name]
                    .sel(cell_id=cell_id, plant_functional_type=fg)
                    .item()
                )
                self.mass_by_fg[fg] = per_area * cell_area
            except KeyError:
                continue

    @property
    def mass_current(self) -> float:
        """Return total biomass across all contributing functional groups."""
        return sum(self.mass_by_fg.values())

    def get_eaten(
        self,
        consumed_mass: float,
        consumer: "Consumer",
    ) -> tuple[dict[str, float], dict[str, float]]:
        """Placeholder to satisfy the Resource protocol."""
        raise NotImplementedError(
            "Resource-specific get_eaten logic not yet implemented."
        )


# The following belongs in AnimalModel
""" def populate_aggregated_plant_resources(
    data: "Data",
    grid: "Grid",
    functional_groups: list[str],
    cell_area: float,
) -> dict[int, dict[str, AggregatedPlantResource]]:
    

    resource_definitions = {
        "leaves": {
            "variable_name": "layer_leaf_mass",
            "vertical_occupancy": VerticalOccupancy.CANOPY,
        },
        "seeds": {
            "variable_name": "fallen_n_propagules",
            "vertical_occupancy": VerticalOccupancy.GROUND,
        },
        "subcanopy_veg": {
            "variable_name": "subcanopy_vegetation_biomass",
            "vertical_occupancy": VerticalOccupancy.GROUND,
        },
        "seedbank": {
            "variable_name": "subcanopy_seedbank_biomass",
            "vertical_occupancy": VerticalOccupancy.SOIL,
        },
    }

    resources: dict[int, dict[str, AggregatedPlantResource]] = {}

    for cell_id in grid.cell_id:
        cell_resources = {}

        for name, info in resource_definitions.items():
            pool = AggregatedPlantResource(
                cell_id=cell_id,
                resource_name=name,
                data=data,
                functional_groups=[fg.name for fg in functional_groups],
                cell_area=cell_area,
                vertical_occupancy=info["vertical_occupancy"],
                variable_name=info["variable_name"],
            )
            cell_resources[name] = pool

        resources[cell_id] = cell_resources

    return resources
 """
