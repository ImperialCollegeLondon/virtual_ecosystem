"""The :mod:`~virtual_ecosystem.models.animal.decay` module contains
pools which are still potentially forageable by animals but are in the process of
microbial decomposition. This includes excrement and carcasses that are tracked solely
in the animal module. This also includes plant litter which is mainly tracked in the
`litter` module, but is made available for animal consumption.
"""  # noqa: D205

from dataclasses import dataclass, field
from math import exp

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


class FungalFruitPool:
    """A class to track the mass of fungal fruiting bodies in each grid cell.

    TODO - A proper explanation as I add stuff
    """

    def __init__(
        self,
        cell_id: int,
        data: "Data",
        cell_area: float,
        c_n_ratio: float,
        c_p_ratio: float,
    ) -> None:
        self.cell_id = cell_id
        self.cell_area = cell_area

        carbon_stock = (
            data["fungal_fruiting_bodies"].sel(cell_id=cell_id).item()
        )  # kg C m⁻²

        self.c_n_ratio = c_n_ratio
        self.c_p_ratio = c_p_ratio

        if min(self.c_n_ratio, self.c_p_ratio) <= 0:
            raise ValueError(
                f"Fungal fruiting bodies: non-positive C:N or C:P ratio in cell "
                f"{cell_id}."
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
                f"Fungal fruiting bodies: negative mass detected in cell {cell_id} "
                f"({self.mass_cnp})."
            )

    vertical_occupancy: VerticalOccupancy = VerticalOccupancy.GROUND
    """Vertical position of fungal fruiting pool."""

    @property
    def mass_current(self) -> float:
        """Return current carbon mass in the pool [kg]."""
        return self.mass_cnp.carbon

    def get_eaten(
        self,
        consumed_mass: float,
        detritivore: "Consumer",
    ) -> tuple[dict[str, float], dict[str, float]]:
        """Remove biomass when a cohort consumes fungal fruiting bodies.

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

    def apply_decay(self, decay_constant: float, time_period: float) -> float:
        """Apply exponential decay to the fungal fruiting bodies pool.

        Args:
            decay_constant: The rate constant for fungal fruiting body decay [day^-1].
            time_period: The time period over which decay occurs [day].

        Returns:
            The total amount of fungal fruiting bodies that decayed in this specific
            grid cell (in carbon terms) [kg]
        """

        # Calculate total decay in carbon terms
        total_decay = (1 - exp(-decay_constant * time_period)) * self.mass_cnp.carbon
        # And then update the pool masses based on this and the fixed stoichiometry
        self.mass_cnp.update(
            carbon=-total_decay,
            nitrogen=-total_decay / self.c_n_ratio,
            phosphorus=-total_decay / self.c_p_ratio,
        )

        return total_decay


class LitterPool:
    """Interface between litter model variables in ``Data`` and the animal module.

    One :class:`LitterPool` instance now represents **one litter type *in one grid
    cell***.
    """

    vertical_occupancy: VerticalOccupancy = VerticalOccupancy.GROUND
    """Vertical position of litter pool."""

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


class SoilPool:
    """Interface between litter model variables in ``Data`` and the animal module.

    One :class:`SoilPool` instance now represents **one soil pool type *in one grid
    cell***.
    """

    vertical_occupancy: VerticalOccupancy = VerticalOccupancy.SOIL
    """Vertical position of soil pool."""

    def __init__(
        self,
        pool_name: str,
        cell_id: int,
        data: "Data",
        cell_area: float,
        max_depth_microbial_activity: float,
        c_n_p_ratios: dict[str, dict[str, float]],
    ) -> None:
        accepted_names = ["pom", "bacteria", "fungi"]

        if pool_name not in accepted_names:
            err = ValueError(
                f"Invalid soil pool name provided ({pool_name}), pools available for "
                f"animal consumption are: {accepted_names}"
            )
            LOGGER.critical(err)
            raise err

        self.pool_name = pool_name
        self.cell_id = cell_id
        self.cell_area = cell_area

        if pool_name == "pom":
            self.mass_cnp = self._extract_pom_cnp_mass(
                data=data,
                biotic_activity_depth=max_depth_microbial_activity,
            )
        elif pool_name == "bacteria":
            self.mass_cnp = self._extract_bacteria_cnp_mass(
                data=data,
                biotic_activity_depth=max_depth_microbial_activity,
                c_n_p_ratios_bacteria=c_n_p_ratios["bacteria"],
            )
        else:
            self.mass_cnp = self._extract_fungi_cnp_mass(
                data=data,
                biotic_activity_depth=max_depth_microbial_activity,
                c_n_p_ratios=c_n_p_ratios,
            )

        # Sanity-check
        if self.mass_cnp.total < 0:
            raise ValueError(
                f"{pool_name}: negative mass detected in cell {cell_id} "
                f"({self.mass_cnp})."
            )

    def _extract_pom_cnp_mass(self, data: Data, biotic_activity_depth: float):
        """Extract the CNP masses of the :term`POM` soil pool.

        Args:
            data: The Virtual Ecosystem data object
            biotic_activity_depth: The soil depth at which biotic activity is assumed to
                halt [m]
        """

        carbon_stock = data["soil_c_pool_pom"].sel(cell_id=self.cell_id).item()
        nitrogen_stock = (
            data["soil_n_pool_particulate"].sel(cell_id=self.cell_id).item()
        )
        phosphorus_stock = (
            data["soil_p_pool_particulate"].sel(cell_id=self.cell_id).item()
        )

        # Convert stocks (kg m^-3) into masses by multiplying by grid square area and by
        # soil active depth
        carbon_mass = carbon_stock * self.cell_area * biotic_activity_depth
        nitrogen_mass = nitrogen_stock * self.cell_area * biotic_activity_depth
        phosphorus_mass = phosphorus_stock * self.cell_area * biotic_activity_depth

        return CNP(
            carbon=carbon_mass, nitrogen=nitrogen_mass, phosphorus=phosphorus_mass
        )

    def _extract_bacteria_cnp_mass(
        self,
        data: Data,
        biotic_activity_depth: float,
        c_n_p_ratios_bacteria: dict[str, float],
    ):
        """Extract the CNP masses of the soil bacteria pool.

        Args:
            data: The Virtual Ecosystem data object
            biotic_activity_depth: The soil depth at which biotic activity is assumed to
                halt [m]
            c_n_p_ratios_bacteria: Carbon to nitrogen and carbon to phosphorus ratios
                for bacterial biomass [unitless]
        """

        carbon_stock = data["soil_c_pool_bacteria"].sel(cell_id=self.cell_id).item()

        # Convert stock (kg m^-3) into mass by multiplying by grid square area and by
        # soil active depth
        carbon_mass = carbon_stock * self.cell_area * biotic_activity_depth
        nitrogen_mass = carbon_mass / c_n_p_ratios_bacteria["nitrogen"]
        phosphorus_mass = carbon_mass / c_n_p_ratios_bacteria["phosphorus"]

        return CNP(
            carbon=carbon_mass, nitrogen=nitrogen_mass, phosphorus=phosphorus_mass
        )

    def _extract_fungi_cnp_mass(
        self,
        data: Data,
        biotic_activity_depth: float,
        c_n_p_ratios: dict[str, dict[str, float]],
    ):
        """Extract the CNP masses of the soil fungi pools.

        Animals are assumed to just generically eat soil fungi rather than being able to
        choose a specific fungal functional group to eat. This means that the biomass
        for all three groups is combined into one.

        It's possible for the soil model to produce slightly negative mycorrhizal fungal
        abundances, when that happens this will be treated as zero abundance, to prevent
        the possibility of a negative rate of animal consumption.

        Args:
            data: The Virtual Ecosystem data object
            biotic_activity_depth: The soil depth at which biotic activity is assumed to
                halt [m]
            c_n_p_ratios: Carbon to nitrogen and carbon to phosphorus ratios for soil
                microbial pools [unitless]
        """

        saprotrophic_stock = (
            data["soil_c_pool_saprotrophic_fungi"].sel(cell_id=self.cell_id).item()
        )
        arbuscular_mycorrhizal_stock = (
            data["soil_c_pool_arbuscular_mycorrhiza"]
            .sel(cell_id=self.cell_id)
            .where(lambda x: x >= 0)
            .fillna(0)
            .item()
        )
        ectomycorrhizal_stock = (
            data["soil_c_pool_ectomycorrhiza"]
            .sel(cell_id=self.cell_id)
            .where(lambda x: x >= 0)
            .fillna(0)
            .item()
        )
        # Individual stock sizes now used to find total stock and the overall C:N and
        # C:P ratios of this total stock
        carbon_stock = (
            saprotrophic_stock + arbuscular_mycorrhizal_stock + ectomycorrhizal_stock
        )
        nitrogen_stock = (
            (saprotrophic_stock / c_n_p_ratios["saprotrophic_fungi"]["nitrogen"])
            + (
                arbuscular_mycorrhizal_stock
                / c_n_p_ratios["arbuscular_mycorrhiza"]["nitrogen"]
            )
            + (ectomycorrhizal_stock / c_n_p_ratios["ectomycorrhiza"]["nitrogen"])
        )
        phosphorus_stock = (
            (saprotrophic_stock / c_n_p_ratios["saprotrophic_fungi"]["phosphorus"])
            + (
                arbuscular_mycorrhizal_stock
                / c_n_p_ratios["arbuscular_mycorrhiza"]["phosphorus"]
            )
            + (ectomycorrhizal_stock / c_n_p_ratios["ectomycorrhiza"]["phosphorus"])
        )

        # Convert stock (kg m^-3) into mass by multiplying by grid square area and by
        # soil active depth
        carbon_mass = carbon_stock * self.cell_area * biotic_activity_depth
        nitrogen_mass = nitrogen_stock * self.cell_area * biotic_activity_depth
        phosphorus_mass = phosphorus_stock * self.cell_area * biotic_activity_depth

        return CNP(
            carbon=carbon_mass, nitrogen=nitrogen_mass, phosphorus=phosphorus_mass
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
        """Remove biomass when a cohort consumes this soil pool.

        In contrast to the LitterPool case, for soil pools mechanical efficiency is
        assumed to be 100% so does not factor into this calculation.

        Args:
            consumed_mass: Target wet-mass to consume (kg). Any attempt to over-consume
                is automatically capped.
            detritivore: The cohort that is feeding, this is only needed to maintain
                same function signature as SoilPool case

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
