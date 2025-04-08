"""The :mod:`~virtual_ecosystem.models.animal.decay` module contains
pools which are still potentially forageable by animals but are in the process of
microbial decomposition. This includes excrement and carcasses that are tracked solely
in the animal module. This also includes plant litter which is mainly tracked in the
`litter` module, but is made available for animal consumption.
"""  # noqa: D205

from dataclasses import dataclass, field

from xarray import DataArray

from virtual_ecosystem.core.data import Data
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.models.animal.cnp import CNP
from virtual_ecosystem.models.animal.protocols import Consumer


@dataclass
class CarcassPool:
    """This class stores information about the carcass biomass in each grid cell."""

    scavengeable_cnp: CNP = field(
        default_factory=lambda: CNP(carbon=0.0, nitrogen=0.0, phosphorus=0.0)
    )
    """A CNP object storing animal-accessible nutrients in the carcass pool."""

    decomposed_cnp: CNP = field(
        default_factory=lambda: CNP(carbon=0.0, nitrogen=0.0, phosphorus=0.0)
    )
    """A CNP object storing decomposed nutrients in the carcass pool."""

    def decomposed_nutrient_per_area(
        self, nutrient: str, grid_cell_area: float
    ) -> float:
        """Convert decomposed carcass nutrient content to mass per area units.

        Args:
            nutrient (str): The name of the nutrient to calculate for.
            grid_cell_area (float): The size of the grid cell [m^2].

        Raises:
            ValueError: If a nutrient other than carbon, nitrogen, or phosphorus is
              chosen.

        Returns:
            float: The nutrient content of the decomposed carcasses on a per area basis
              [kg m^-2].
        """
        if nutrient not in {"carbon", "nitrogen", "phosphorus"}:
            raise ValueError(
                f"{nutrient} is not a valid nutrient. Valid options: 'carbon', "
                f"'nitrogen', or 'phosphorus'."
            )

        return getattr(self.decomposed_cnp, nutrient) / grid_cell_area

    def add_carcass(self, carbon: float, nitrogen: float, phosphorus: float) -> None:
        """Add carcass mass to the pool based on the provided mass.

        Args:
            carbon (float): The mass of carbon to add.
            nitrogen (float): The mass of nitrogen to add.
            phosphorus (float): The mass of phosphorus to add.

        Raises:
            ValueError: If any input mass is negative.
        """
        if carbon < 0 or nitrogen < 0 or phosphorus < 0:
            raise ValueError(
                f"CNP values must be non-negative. Provided values: carbon={carbon}, "
                f"nitrogen={nitrogen}, phosphorus={phosphorus}"
            )

        self.scavengeable_cnp.update(
            carbon=carbon, nitrogen=nitrogen, phosphorus=phosphorus
        )

    def reset(self) -> None:
        """Reset tracking of the nutrients associated with decomposed carcasses.

        This function sets the decomposed carbon, nitrogen, and phosphorus to zero.
        It should only be called after transfers to the soil model due to decomposition
        have been calculated.
        """
        self.decomposed_cnp = CNP(0.0, 0.0, 0.0)


@dataclass
class ExcrementPool:
    """This class stores information about the amount of excrement in each grid cell."""

    scavengeable_cnp: CNP = field(
        default_factory=lambda: CNP(carbon=0.0, nitrogen=0.0, phosphorus=0.0)
    )
    """A CNP object storing animal-accessible nutrients in the excrement pool."""

    decomposed_cnp: CNP = field(
        default_factory=lambda: CNP(carbon=0.0, nitrogen=0.0, phosphorus=0.0)
    )
    """A CNP object storing decomposed nutrients in the excrement pool."""

    def decomposed_nutrient_per_area(
        self, nutrient: str, grid_cell_area: float
    ) -> float:
        """Convert decomposed excrement nutrient content to mass per area units.

        Args:
            nutrient (str): The name of the nutrient to calculate for.
            grid_cell_area (float): The size of the grid cell [m^2].

        Raises:
            ValueError: If a nutrient other than carbon, nitrogen, or phosphorus is
              chosen.

        Returns:
            float: The nutrient content of the decomposed excrement on a per area basis
              [kg m^-2].
        """
        if nutrient not in {"carbon", "nitrogen", "phosphorus"}:
            raise ValueError(
                f"{nutrient} is not a valid nutrient. Valid options: 'carbon',"
                f"'nitrogen', or 'phosphorus'."
            )

        return getattr(self.decomposed_cnp, nutrient) / grid_cell_area

    def add_excrement(self, carbon: float, nitrogen: float, phosphorus: float) -> None:
        """Add excrement mass to the pool based on the provided input mass.

        Args:
            carbon (float): The mass of carbon to add.
            nitrogen (float): The mass of nitrogen to add.
            phosphorus (float): The mass of phosphorus to add.

        Raises:
            ValueError: If any input mass is negative.
        """
        if carbon < 0 or nitrogen < 0 or phosphorus < 0:
            raise ValueError(
                f"CNP values must be non-negative. Provided values: carbon={carbon}, "
                f"nitrogen={nitrogen}, phosphorus={phosphorus}"
            )

        self.scavengeable_cnp.update(
            carbon=carbon, nitrogen=nitrogen, phosphorus=phosphorus
        )

    def reset(self) -> None:
        """Reset tracking of the nutrients associated with decomposed excrement.

        This function sets the decomposed carbon, nitrogen, and phosphorus to zero.
        It should only be called after transfers to the soil model due to decomposition
        have been calculated.
        """
        self.decomposed_cnp = CNP(carbon=0.0, nitrogen=0.0, phosphorus=0.0)


def find_decay_consumed_split(
    microbial_decay_rate: float, animal_scavenging_rate: float
):
    """Find fraction of biomass that is assumed to decay rather than being scavenged.

    This should be calculated separately for each relevant biomass type (excrement and
    carcasses). This function should could be replaced in future by something that
    incorporates more of the factors determining this split (e.g. temperature).

    Args:
        microbial_decay_rate: Rate at which biomass type decays due to microbes [day^-1]
        animal_scavenging_rate: Rate at which biomass type is scavenged due to animals
            [day^-1]
    """

    return microbial_decay_rate / (animal_scavenging_rate + microbial_decay_rate)


class LitterPool:
    """A class that makes litter available for animal consumption.

    This class acts as the interface between litter model data stored in the core data
    object and the animal model.
    """

    def __init__(self, pool_name: str, data: "Data", cell_area: float) -> None:
        self.pool_name = pool_name

        carbon_mass = data[f"litter_pool_{pool_name}"].to_numpy() * cell_area
        self.c_n_ratio = data[f"c_n_ratio_{pool_name}"].to_numpy()
        self.c_p_ratio = data[f"c_p_ratio_{pool_name}"].to_numpy()

        if (self.c_n_ratio <= 0).any() or (self.c_p_ratio <= 0).any():
            raise ValueError(f"Invalid C:N or C:P ratios in {self.pool_name} pool.")

        self.mass_cnp = [
            CNP(
                carbon=carbon_mass[i],
                nitrogen=carbon_mass[i] / self.c_n_ratio[i],
                phosphorus=carbon_mass[i] / self.c_p_ratio[i],
            )
            for i in range(len(carbon_mass))
        ]

        if any(cnp.total < 0 for cnp in self.mass_cnp):
            raise ValueError(f"Negative values detected in {self.pool_name} pool.")

    @property
    def mass_current(self) -> DataArray:
        """Property returning the total mass of carbon in the litter pool."""
        carbon_values = [cnp.carbon for cnp in self.mass_cnp]
        return DataArray(carbon_values, dims=["cell_id"])

    def get_eaten(
        self, consumed_mass: float, detritivore: "Consumer", grid_cell_id: int
    ) -> dict[str, float]:
        """Method for handling a trophic interaction with detritivores."""
        if consumed_mass < 0:
            raise ValueError("Consumed mass cannot be negative.")

        cell_cnp = self.mass_cnp[
            grid_cell_id
        ]  # Access CNP object for the given grid cell
        total_mass_available = cell_cnp.total
        actual_consumed_mass = (
            min(total_mass_available, consumed_mass)
            * detritivore.functional_group.mechanical_efficiency
        )

        nutrient_proportions = {
            "carbon": cell_cnp.carbon / total_mass_available,
            "nitrogen": cell_cnp.nitrogen / total_mass_available,
            "phosphorus": cell_cnp.phosphorus / total_mass_available,
        }

        consumed = {
            nutrient: actual_consumed_mass * proportion
            for nutrient, proportion in nutrient_proportions.items()
        }

        # Update the CNP object in place
        cell_cnp.update(
            carbon=-consumed["carbon"],
            nitrogen=-consumed["nitrogen"],
            phosphorus=-consumed["phosphorus"],
        )

        return consumed


class HerbivoryWaste:
    """A class to track the amount of waste generated by each form of herbivory.

    This is used as a temporary storage location before the wastes are added to the
    litter model. As such it is not made available for animal consumption.

    The litter model splits its plant matter into four classes: wood, leaves, roots, and
    reproductive tissues (fruits and flowers). A separate instance of this class should
    be used for each of these groups.

    Args:
        pool_name: Type of plant matter this waste pool contains.

    Raises:
        ValueError: If initialised for a plant matter type that the litter model doesn't
            accept.
    """

    def __init__(self, plant_matter_type: str) -> None:
        # Check that this isn't being initialised for a plant matter type that the
        # litter model doesn't use
        accepted_plant_matter_types = [
            "leaf",
            "root",
            "deadwood",
            "reproductive_tissue",
        ]
        if plant_matter_type not in accepted_plant_matter_types:
            to_raise = ValueError(
                f"{plant_matter_type} not a valid form of herbivory waste, valid forms "
                f"are as follows: {accepted_plant_matter_types}"
            )
            LOGGER.error(to_raise)
            raise to_raise

        self.plant_matter_type = plant_matter_type
        """Type of plant matter this waste pool contains."""

        self.mass_cnp: dict[str, float] = {
            "carbon": 0.0,
            "nitrogen": 0.0,
            "phosphorus": 0.0,
        }
        """The mass of each stoichiometric element found in the plant resources,
        {"carbon": value, "nitrogen": value, "phosphorus": value}."""

        self.lignin_proportion = 0.25
        """Proportion of the herbivory waste pool carbon that is lignin [unitless]."""

    def add_waste(self, input_mass_cnp: dict[str, float]) -> None:
        """Add waste to the pool based on the provided stoichiometric mass.

        Args:
            input_mass_cnp: Dictionary specifying the mass of each element in the waste
                {"carbon": value, "nitrogen": value, "phosphorus": value}.

        Raises:
            ValueError: If the input dictionary is missing required elements or contains
                negative values.
        """
        # Validate input structure and content
        required_keys = {"carbon", "nitrogen", "phosphorus"}
        if not required_keys.issubset(input_mass_cnp.keys()):
            raise ValueError(
                f"mass_cnp must contain all required keys {required_keys}. "
                f"Provided keys: {input_mass_cnp.keys()}"
            )
        if any(value < 0 for value in input_mass_cnp.values()):
            raise ValueError(
                f"CNP values must be non-negative. Provided values: {input_mass_cnp}"
            )

        # Add the masses to the current pool
        for element, value in input_mass_cnp.items():
            self.mass_cnp[element] += value
