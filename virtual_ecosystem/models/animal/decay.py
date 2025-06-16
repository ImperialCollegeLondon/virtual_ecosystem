"""The :mod:`~virtual_ecosystem.models.animal.decay` module contains
pools which are still potentially forageable by animals but are in the process of
microbial decomposition. This includes excrement and carcasses that are tracked solely
in the animal module. This also includes plant litter which is mainly tracked in the
`litter` module, but is made available for animal consumption.
"""  # noqa: D205

from dataclasses import dataclass, field

from virtual_ecosystem.core.data import Data
from virtual_ecosystem.core.logger import LOGGER
from virtual_ecosystem.models.animal.animal_traits import VerticalOccupancy
from virtual_ecosystem.models.animal.cnp import CNP
from virtual_ecosystem.models.animal.protocols import Consumer, ScavengeableResource


class ScavengeableMixin:
    """Mixin for nutrient pools that can be scavenged by animal cohorts."""

    def get_eaten(
        self: "ScavengeableResource",
        consumed_mass: float,
        scavenger: "Consumer",
    ) -> tuple[dict[str, float], dict[str, float]]:
        """Remove biomass from the scavengeable pool and return stoichiometric gain.

        Args:
            consumed_mass: Wet-mass the scavenger tries to eat [kg].
            scavenger: The animal cohort consuming the material.

        Returns:
            Dict with keys ``"carbon"``, ``"nitrogen"``, ``"phosphorus"`` giving
            the mass of each element actually ingested, and a second empty dict.

        Raises:
            ValueError: If ``consumed_mass`` is negative.
        """
        if consumed_mass < 0:
            raise ValueError("consumed_mass cannot be negative.")

        available = self.scavengeable_cnp.total
        if available == 0.0:
            return {"carbon": 0.0, "nitrogen": 0.0, "phosphorus": 0.0}, {}

        taken_wet = min(consumed_mass, available)

        mech_eff = scavenger.functional_group.mechanical_efficiency
        ingested_wet = taken_wet * mech_eff
        missed_wet = taken_wet * (1.0 - mech_eff)

        frac_C = self.scavengeable_cnp.carbon / available
        frac_N = self.scavengeable_cnp.nitrogen / available
        frac_P = self.scavengeable_cnp.phosphorus / available

        ingested_cnp = {
            "carbon": ingested_wet * frac_C,
            "nitrogen": ingested_wet * frac_N,
            "phosphorus": ingested_wet * frac_P,
        }

        # Update pool states
        self.scavengeable_cnp.update(
            carbon=-taken_wet * frac_C,
            nitrogen=-taken_wet * frac_N,
            phosphorus=-taken_wet * frac_P,
        )
        self.decomposed_cnp.update(
            carbon=missed_wet * frac_C,
            nitrogen=missed_wet * frac_N,
            phosphorus=missed_wet * frac_P,
        )

        return ingested_cnp, {}


@dataclass
class CarcassPool(ScavengeableMixin):
    """This class stores information about the carcass biomass in each grid cell."""

    scavengeable_cnp: CNP = field(
        default_factory=lambda: CNP(carbon=0.0, nitrogen=0.0, phosphorus=0.0)
    )
    """A CNP object storing animal-accessible nutrients in the carcass pool."""

    decomposed_cnp: CNP = field(
        default_factory=lambda: CNP(carbon=0.0, nitrogen=0.0, phosphorus=0.0)
    )
    """A CNP object storing decomposed nutrients in the carcass pool."""
    cell_id: int = -1
    """Grid position of carcass pool."""
    vertical_occupancy: VerticalOccupancy = VerticalOccupancy.GROUND
    """Vertical position of carcass pool."""

    @property
    def mass_current(self) -> float:
        """Total scavengeable carcass mass (kg)."""
        return self.scavengeable_cnp.total

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
class ExcrementPool(ScavengeableMixin):
    """This class stores information about the amount of excrement in each grid cell."""

    scavengeable_cnp: CNP = field(
        default_factory=lambda: CNP(carbon=0.0, nitrogen=0.0, phosphorus=0.0)
    )
    """A CNP object storing animal-accessible nutrients in the excrement pool."""

    decomposed_cnp: CNP = field(
        default_factory=lambda: CNP(carbon=0.0, nitrogen=0.0, phosphorus=0.0)
    )
    """A CNP object storing decomposed nutrients in the excrement pool."""
    cell_id: int = -1
    """Grid position of carcass pool."""
    vertical_occupancy: VerticalOccupancy = VerticalOccupancy.GROUND
    """Vertical position of carcass pool."""

    @property
    def mass_current(self) -> float:
        """Total scavengeable excrement mass (kg)."""
        return self.scavengeable_cnp.total

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
    """Interface between litter model variables in ``Data`` and the animal module.

    One :class:`LitterPool` instance now represents **one litter type *in one grid
    cell***.
    """

    vertical_occupancy: VerticalOccupancy = VerticalOccupancy.GROUND
    """Vertical position of carcass pool."""

    def __init__(
        self,
        pool_name: str,
        cell_id: int,
        data: "Data",
        cell_area: float,
    ) -> None:
        self.pool_name = pool_name
        self.cell_id = cell_id
        self.cell_area = cell_area

        carbon_stock = (
            data[f"litter_pool_{pool_name}"].sel(cell_id=cell_id).item()
        )  # kg C m⁻²
        self.c_n_ratio = data[f"c_n_ratio_{pool_name}"].sel(cell_id=cell_id).item()
        self.c_p_ratio = data[f"c_p_ratio_{pool_name}"].sel(cell_id=cell_id).item()

        if min(self.c_n_ratio, self.c_p_ratio) <= 0:
            raise ValueError(
                f"{pool_name}: non-positive C:N or C:P ratio in cell {cell_id}."
            )

        # Convert to absolute mass (kg) and build stoichiometry
        carbon_mass = carbon_stock * cell_area
        self.mass_cnp = CNP(
            carbon=carbon_mass,
            nitrogen=carbon_mass / self.c_n_ratio,
            phosphorus=carbon_mass / self.c_p_ratio,
        )

        # Sanity-check
        if self.mass_cnp.total < 0:
            raise ValueError(
                f"{pool_name}: negative mass detected in cell {cell_id} "
                f"({self.mass_cnp})."
            )

    @property
    def mass_current(self) -> float:
        """Return current carbon mass in the pool [kg]."""
        return self.mass_cnp.carbon

    def get_eaten(
        self,
        consumed_mass: float,
        detritivore: "Consumer",
    ) -> tuple[dict[str, float], dict[str, float]]:
        """Remove biomass when a cohort consumes this litter pool.

        Args:
            consumed_mass: Target wet-mass to consume **after** mechanical efficiency is
              applied (kg).  Any attempt to over-consume is automatically capped.
            detritivore: The cohort that is feeding used only to obtain mechanical
              efficiency.

        Returns:
            Dictionary of element masses actually assimilated, keys ``carbon``,
            ``nitrogen``, ``phosphorus`` (kg).
        """
        if consumed_mass < 0:
            raise ValueError("consumed_mass must be non-negative")

        total_available = self.mass_cnp.total
        mech_eff = detritivore.functional_group.mechanical_efficiency
        actual = min(consumed_mass, total_available) * mech_eff

        frac_C = self.mass_cnp.carbon / total_available
        frac_N = self.mass_cnp.nitrogen / total_available
        frac_P = self.mass_cnp.phosphorus / total_available

        taken = {
            "carbon": actual * frac_C,
            "nitrogen": actual * frac_N,
            "phosphorus": actual * frac_P,
        }

        # in-place update
        self.mass_cnp.update(
            carbon=-taken["carbon"],
            nitrogen=-taken["nitrogen"],
            phosphorus=-taken["phosphorus"],
        )
        return taken, {}


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
