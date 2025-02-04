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
from virtual_ecosystem.models.animal.protocols import Consumer


@dataclass
class CarcassPool:
    """This class stores information about the carcass biomass in each grid cell."""

    scavengeable_cnp: dict[str, float] = field(
        default_factory=lambda: {"carbon": 0.0, "nitrogen": 0.0, "phosphorus": 0.0}
    )
    """Dictionary of animal accessible nutrients in the carcass pool
    {"carbon": value, "nitrogen": value, "phosphorus": value} in [kg].
    """

    decomposed_cnp: dict[str, float] = field(
        default_factory=lambda: {"carbon": 0.0, "nitrogen": 0.0, "phosphorus": 0.0}
    )
    """Dictionary of decomposed nutrients in the carcass pool
    {"carbon": value, "nitrogen": value, "phosphorus": value} in [kg].
    """

    def decomposed_nutrient_per_area(
        self, nutrient: str, grid_cell_area: float
    ) -> float:
        """Convert decomposed carcass nutrient content to mass per area units.

        Args:
            nutrient: The name of the nutrient to calculate for
            grid_cell_area: The size of the grid cell [m^2]

        Raises:
            AttributeError: If a nutrient other than carbon, nitrogen, or phosphorus is
                chosen

        Returns:
            The nutrient content of the decomposed carcasses on a per area basis [kg
            m^-2]
        """

        if nutrient not in self.decomposed_cnp:
            raise ValueError(
                f"{nutrient} is not a valid nutrient. Valid options: 'C', 'N', or 'P'."
            )

        return self.decomposed_cnp[nutrient] / grid_cell_area

    def add_carcass(self, input_mass_cnp: dict[str, float]) -> None:
        """Add carcass mass to the pool based on the provided  mass.

        Args:
            input_mass_cnp: Dictionary specifying the input mass of each
                element in the carcass {"carbon": value, "nitrogen": value,
                "phosphorus": value}.

        Raises:
            ValueError: If the input dictionary is missing required elements or contains
                negative values.
        """
        required_keys = {"carbon", "nitrogen", "phosphorus"}
        if not required_keys.issubset(input_mass_cnp.keys()):
            raise ValueError(
                f"input_mass_cnp must contain all required keys {required_keys}. "
                f"Provided keys: {input_mass_cnp.keys()}"
            )
        if any(value < 0 for value in input_mass_cnp.values()):
            raise ValueError(
                f"CNP values must be non-negative. Provided values: {input_mass_cnp}"
            )

        for element, value in input_mass_cnp.items():
            self.scavengeable_cnp[element] += value

    def reset(self):
        """Reset tracking of the nutrients associated with decomposed carcasses.

        This function sets the amount of decomposed carbon, nitrogen and phosphorus to
        zero. This function should only be called after transfers to the soil model due
        to decomposition have been calculated.
        """

        self.decomposed_cnp = {key: 0.0 for key in self.decomposed_cnp}


@dataclass
class ExcrementPool:
    """This class store information about the amount of excrement in each grid cell."""

    scavengeable_cnp: dict[str, float] = field(
        default_factory=lambda: {"carbon": 0.0, "nitrogen": 0.0, "phosphorus": 0.0}
    )
    """Dictionary of animal accessible nutrients in the excrement pool
    {"carbon": value, "nitrogen": value, "phosphorus": value} in [kg].
    """

    decomposed_cnp: dict[str, float] = field(
        default_factory=lambda: {"carbon": 0.0, "nitrogen": 0.0, "phosphorus": 0.0}
    )
    """Dictionary of decomposed nutrients in the excrement pool
    {"carbon": value, "nitrogen": value, "phosphorus": value} in [kg].
    """

    def decomposed_nutrient_per_area(
        self, nutrient: str, grid_cell_area: float
    ) -> float:
        """Convert decomposed excrement nutrient content to mass per area units.

        Args:
            nutrient: The name of the nutrient to calculate for.
            grid_cell_area: The size of the grid cell [m^2].

        Raises:
            AttributeError: If a nutrient other than carbon, nitrogen, or phosphorus is
                chosen

        Returns:
            The nutrient content of the decomposed excrement on a per area basis [kg
            m^-2]
        """
        if nutrient not in self.decomposed_cnp:
            raise ValueError(
                f"{nutrient} is not a valid nutrient. Valid options: 'C', 'N', or 'P'."
            )

        return self.decomposed_cnp[nutrient] / grid_cell_area

    def add_excrement(self, input_mass_cnp: dict[str, float]) -> None:
        """Add excrement to the pool based on the provided input mass.

        Args:
            input_mass_cnp: Dictionary specifying the scavengeable mass of each
                element in the excrement {"carbon": value, "nitrogen": value,
                "phosphorus": value}.

        Raises:
            ValueError: If the input dictionary is missing required elements or contains
                negative values.
        """
        required_keys = {"carbon", "nitrogen", "phosphorus"}
        if not required_keys.issubset(input_mass_cnp.keys()):
            raise ValueError(
                f"input_mass_cnp must contain all required keys {required_keys}. "
                f"Provided keys: {input_mass_cnp.keys()}"
            )
        if any(value < 0 for value in input_mass_cnp.values()):
            raise ValueError(
                f"CNP values must be non-negative. Provided values: {input_mass_cnp}"
            )

        for element, value in input_mass_cnp.items():
            self.scavengeable_cnp[element] += value

    def reset(self) -> None:
        """Reset tracking of the nutrients associated with decomposed excrement.

        This function sets the amount of decomposed carbon, nitrogen and phosphorus to
        zero. This function should only be called after transfers to the soil model due
        to decomposition have been calculated.
        """

        self.decomposed_cnp = {key: 0.0 for key in self.decomposed_cnp}


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

    This class is designed to be reused for all five of the litter pools used in the
    litter model, as all of these pools are consumable by animals.

    Args:
        pool_name: The name of the litter pool being accessed.
        data: A Data object containing information from the litter model.
        cell_area: The size of the cell, used to convert from density to mass units
            [m^2].
    """

    def __init__(self, pool_name: str, data: "Data", cell_area: float) -> None:
        self.pool_name = pool_name
        """Name of the pool."""

        # Initialize mass_cnp based on the pool's carbon content and ratios
        carbon_mass = (data[f"litter_pool_{pool_name}"].to_numpy()) * cell_area
        self.mass_cnp = {
            "carbon": carbon_mass,
            "nitrogen": carbon_mass / data[f"c_n_ratio_{pool_name}"].to_numpy(),
            "phosphorus": carbon_mass / data[f"c_p_ratio_{pool_name}"].to_numpy(),
        }
        """Mass of the litter pool for each nutrient [kg]."""

        if carbon_mass.min() < 0:
            raise ValueError(
                f"Negative values detected in {self.pool_name}"
                f"litter pool: {carbon_mass}"
            )

    @property
    def mass_current(self) -> DataArray:
        """Dynamically calculate the current total body mass from stoichiometry.

        TODO: currently carbon only

        Returns:
            A DataArray representing the total carbon mass for each grid cell.
        """

        return DataArray(
            self.mass_cnp["carbon"],
            dims=["cell_id"],
        )

    def get_eaten(
        self, consumed_mass: float, detritivore: "Consumer", grid_cell_id: int
    ) -> dict[str, float]:
        """Handle litter detritivory.

        Args:
            consumed_mass: The mass intended to be consumed by the detritivore [kg].
            detritivore: The Consumer (AnimalCohort) consuming the Litter.
            grid_cell_id: The cell id of the cell the animal cohort is in.

        Returns:
            A dictionary containing the net mass gain of carbon, nitrogen, phosphorus
            after mechanical efficiencies: {"carbon": value, "nitrogen": value,
            "phosphorus": value}.
        """
        # Ensure consumed_mass is non-negative
        if consumed_mass < 0:
            raise ValueError("Consumed mass cannot be negative.")

        # Check available mass in the specified grid cell
        actually_available_mass = min(
            self.mass_current[grid_cell_id].item(), consumed_mass
        )

        # Calculate the mass of litter consumed after mechanical efficiency
        actual_consumed_mass = (
            actually_available_mass * detritivore.functional_group.mechanical_efficiency
        )

        # Ensure we don't divide by zero when updating nutrient proportions
        if self.mass_current[grid_cell_id] == 0:
            raise ValueError("Litter pool is empty; cannot consume nutrients.")

        # **Store initial nutrient fractions before modifying `mass_cnp`**
        nutrient_fractions = {
            nutrient: self.mass_cnp[nutrient][grid_cell_id]
            / self.mass_current[grid_cell_id]
            for nutrient in self.mass_cnp
        }

        # **Apply mass consumption AFTER fractions are calculated**
        nutrient_gain = {}
        for nutrient in self.mass_cnp:
            nutrient_consumed = actual_consumed_mass * nutrient_fractions[nutrient]
            self.mass_cnp[nutrient][grid_cell_id] -= nutrient_consumed
            nutrient_gain[nutrient] = nutrient_consumed

        return nutrient_gain


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
