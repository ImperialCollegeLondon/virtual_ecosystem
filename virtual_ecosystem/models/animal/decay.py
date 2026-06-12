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
            Dict with keys ``"C"``, ``"N"``, ``"P"`` giving
            the mass of each element actually ingested, and a second empty dict.

        Raises:
            ValueError: If ``consumed_mass`` is negative.
        """
        if consumed_mass < 0:
            raise ValueError("consumed_mass cannot be negative.")

        available = self.scavengeable_cnp.total
        if available == 0.0:
            return {"C": 0.0, "N": 0.0, "P": 0.0}, {}

        taken_wet = min(consumed_mass, available)

        mech_eff = scavenger.functional_group.mechanical_efficiency
        ingested_wet = taken_wet * mech_eff
        missed_wet = taken_wet * (1.0 - mech_eff)

        frac_C = self.scavengeable_cnp.C / available
        frac_N = self.scavengeable_cnp.N / available
        frac_P = self.scavengeable_cnp.P / available

        ingested_cnp = {
            "C": ingested_wet * frac_C,
            "N": ingested_wet * frac_N,
            "P": ingested_wet * frac_P,
        }

        # Update pool states
        self.scavengeable_cnp.update(
            C=-taken_wet * frac_C,
            N=-taken_wet * frac_N,
            P=-taken_wet * frac_P,
        )
        self.decomposed_cnp.update(
            C=missed_wet * frac_C,
            N=missed_wet * frac_N,
            P=missed_wet * frac_P,
        )

        return ingested_cnp, {}


@dataclass
class CarcassPool(ScavengeableMixin):
    """This class stores information about the carcass biomass in each grid cell."""

    scavengeable_cnp: CNP = field(default_factory=lambda: CNP(C=0.0, N=0.0, P=0.0))
    """A CNP object storing animal-accessible nutrients in the carcass pool."""

    decomposed_cnp: CNP = field(default_factory=lambda: CNP(C=0.0, N=0.0, P=0.0))
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
        if nutrient not in {"C", "N", "P"}:
            raise ValueError(
                f"{nutrient} is not a valid nutrient. Valid options: 'C', 'N', or 'P'."
            )

        return getattr(self.decomposed_cnp, nutrient) / grid_cell_area

    def add_carcass(self, C: float, N: float, P: float) -> None:
        """Add carcass mass to the pool based on the provided mass.

        Args:
            C (float): The mass of carbon to add.
            N (float): The mass of nitrogen to add.
            P (float): The mass of phosphorus to add.

        Raises:
            ValueError: If any input mass is negative.
        """
        if C < 0 or N < 0 or P < 0:
            raise ValueError(
                f"CNP values must be non-negative. Provided values: C={C}, N={N}, P={P}"
            )

        self.scavengeable_cnp.update(C=C, N=N, P=P)

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

    scavengeable_cnp: CNP = field(default_factory=lambda: CNP(C=0.0, N=0.0, P=0.0))
    """A CNP object storing animal-accessible nutrients in the excrement pool."""

    decomposed_cnp: CNP = field(default_factory=lambda: CNP(C=0.0, N=0.0, P=0.0))
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
        if nutrient not in {"C", "N", "P"}:
            raise ValueError(
                f"{nutrient} is not a valid nutrient. Valid options: 'C','N', or 'P'."
            )

        return getattr(self.decomposed_cnp, nutrient) / grid_cell_area

    def add_excrement(self, C: float, N: float, P: float) -> None:
        """Add excrement mass to the pool based on the provided input mass.

        Args:
            C (float): The mass of carbon to add.
            N (float): The mass of nitrogen to add.
            P (float): The mass of phosphorus to add.

        Raises:
            ValueError: If any input mass is negative.
        """
        if C < 0 or N < 0 or P < 0:
            raise ValueError(
                f"CNP values must be non-negative. Provided values: C={C}, N={N}, P={P}"
            )

        self.scavengeable_cnp.update(C=C, N=N, P=P)

    def reset(self) -> None:
        """Reset tracking of the nutrients associated with decomposed excrement.

        This function sets the decomposed carbon, nitrogen, and phosphorus to zero.
        It should only be called after transfers to the soil model due to decomposition
        have been calculated.
        """
        self.decomposed_cnp = CNP(C=0.0, N=0.0, P=0.0)


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
            C=carbon_mass,
            N=carbon_mass / self.c_n_ratio,
            P=carbon_mass / self.c_p_ratio,
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
        return self.mass_cnp.C

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
            Dictionary of element masses actually assimilated, keys ``C``,
            ``N``, ``P`` (kg).
        """
        if consumed_mass < 0:
            raise ValueError("consumed_mass must be non-negative")

        total_available = self.mass_cnp.total
        mech_eff = detritivore.functional_group.mechanical_efficiency
        actual = min(consumed_mass, total_available) * mech_eff

        frac_C = self.mass_cnp.C / total_available
        frac_N = self.mass_cnp.N / total_available
        frac_P = self.mass_cnp.P / total_available

        taken = {
            "C": actual * frac_C,
            "N": actual * frac_N,
            "P": actual * frac_P,
        }

        # in-place update
        self.mass_cnp.update(
            C=-taken["C"],
            N=-taken["N"],
            P=-taken["P"],
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
        total_decay = (1 - exp(-decay_constant * time_period)) * self.mass_cnp.C
        # And then update the pool masses based on this and the fixed stoichiometry
        self.mass_cnp.update(
            C=-total_decay,
            N=-total_decay / self.c_n_ratio,
            P=-total_decay / self.c_p_ratio,
        )

        return total_decay


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

        carbon_stock = (
            data["soil_cnp_pool_pom"].sel(cell_id=self.cell_id, element="C").item()
        )
        nitrogen_stock = (
            data["soil_cnp_pool_pom"].sel(cell_id=self.cell_id, element="N").item()
        )
        phosphorus_stock = (
            data["soil_cnp_pool_pom"].sel(cell_id=self.cell_id, element="P").item()
        )

        # Convert stocks (kg m^-3) into masses by multiplying by grid square area and by
        # soil active depth
        carbon_mass = carbon_stock * self.cell_area * biotic_activity_depth
        nitrogen_mass = nitrogen_stock * self.cell_area * biotic_activity_depth
        phosphorus_mass = phosphorus_stock * self.cell_area * biotic_activity_depth

        return CNP(C=carbon_mass, N=nitrogen_mass, P=phosphorus_mass)

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

        carbon_stock = (
            data["soil_c_pool_bacteria"]
            .sel(cell_id=self.cell_id)
            .where(lambda x: x >= 0)
            .fillna(0)
            .item()
        )

        # Convert stock (kg m^-3) into mass by multiplying by grid square area and by
        # soil active depth
        carbon_mass = carbon_stock * self.cell_area * biotic_activity_depth
        nitrogen_mass = carbon_mass / c_n_p_ratios_bacteria["N"]
        phosphorus_mass = carbon_mass / c_n_p_ratios_bacteria["P"]

        return CNP(C=carbon_mass, N=nitrogen_mass, P=phosphorus_mass)

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
            data["soil_c_pool_saprotrophic_fungi"]
            .sel(cell_id=self.cell_id)
            .where(lambda x: x >= 0)
            .fillna(0)
            .item()
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
            (saprotrophic_stock / c_n_p_ratios["saprotrophic_fungi"]["N"])
            + (
                arbuscular_mycorrhizal_stock
                / c_n_p_ratios["arbuscular_mycorrhiza"]["N"]
            )
            + (ectomycorrhizal_stock / c_n_p_ratios["ectomycorrhiza"]["N"])
        )
        phosphorus_stock = (
            (saprotrophic_stock / c_n_p_ratios["saprotrophic_fungi"]["P"])
            + (
                arbuscular_mycorrhizal_stock
                / c_n_p_ratios["arbuscular_mycorrhiza"]["P"]
            )
            + (ectomycorrhizal_stock / c_n_p_ratios["ectomycorrhiza"]["P"])
        )

        # Convert stock (kg m^-3) into mass by multiplying by grid square area and by
        # soil active depth
        carbon_mass = carbon_stock * self.cell_area * biotic_activity_depth
        nitrogen_mass = nitrogen_stock * self.cell_area * biotic_activity_depth
        phosphorus_mass = phosphorus_stock * self.cell_area * biotic_activity_depth

        return CNP(C=carbon_mass, N=nitrogen_mass, P=phosphorus_mass)

    @property
    def mass_current(self) -> float:
        """Return current carbon mass in the pool [kg]."""
        return self.mass_cnp.C

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
            Dictionary of element masses actually assimilated, keys ``C``,
            ``N``, ``P`` (kg).
        """
        if consumed_mass < 0:
            raise ValueError("consumed_mass must be non-negative")

        total_available = self.mass_cnp.total
        mech_eff = detritivore.functional_group.mechanical_efficiency
        actual = min(consumed_mass, total_available) * mech_eff

        frac_C = self.mass_cnp.C / total_available
        frac_N = self.mass_cnp.N / total_available
        frac_P = self.mass_cnp.P / total_available

        taken = {
            "C": actual * frac_C,
            "N": actual * frac_N,
            "P": actual * frac_P,
        }

        # in-place update
        self.mass_cnp.update(
            C=-taken["C"],
            N=-taken["N"],
            P=-taken["P"],
        )
        return taken, {}


class HerbivoryWaste:
    """A class to track the amount of waste generated by each form of herbivory.

    This is used as a temporary storage location before the wastes are added to the
    litter model. As such it is not made available for animal consumption.

    We assume that any wood partially consumed by herbivores will be sufficiently broken
    down to be passed to the standard metabolic/structural litter pools, rather than the
    dead wood pool which is intended for entire stems. The important distinction to make
    is between herbivory waste from above the soil and within the soil, as this
    determines whether the waste should be added to above or below ground litter pools.
    """

    def __init__(self) -> None:

        self.above_ground_mass_cnp: dict[str, float] = {
            "C": 0.0,
            "N": 0.0,
            "P": 0.0,
        }
        """The mass of each stoichiometric element found in the (above-ground) plant
        resources, {"C": value, "N": value, "P": value}."""

        self.above_ground_lignin_proportion = 0.0
        """Proportion of the (above-ground) herbivory waste pool carbon that is lignin
        [unitless]."""

        self.below_ground_mass_cnp: dict[str, float] = {
            "C": 0.0,
            "N": 0.0,
            "P": 0.0,
        }
        """The mass of each stoichiometric element found in the (below-ground) plant
        resources, {"C": value, "N": value, "P": value}."""

        self.below_ground_lignin_proportion = 0.0
        """Proportion of the (below-ground) herbivory waste pool carbon that is lignin
        [unitless]."""

    def add_waste(
        self, input_mass_cnp: dict[str, float], vertical_occupancy: VerticalOccupancy
    ) -> None:
        """Add waste to the pool based on the provided stoichiometric mass.

        Whether waste is added to above- or below-ground herbivory waste depends on the
        strata the resource pool is found in. If the pool lies in both above and below
        ground strata the waste is split between above- and below-ground. This split
        occurs evenly between strata, i.e. if the resource pool is found just on the
        ground and in the soil the above:below split is 50:50, but if the resource pool
        is also found in the canopy, the below ground then only receives 1/3 of the
        total mass.

        Args:
            input_mass_cnp: Dictionary specifying the mass of each element in the waste
                {"C": value, "N": value, "P": value}.
            vertical_occupancy: The combined vertical occupancy of the consumed resource
                pool.

        Raises:
            ValueError: If the input dictionary is missing required elements or contains
                negative values.
        """
        # Validate input structure and content
        required_keys = {"C", "N", "P"}
        if not required_keys.issubset(input_mass_cnp.keys()):
            raise ValueError(
                f"mass_cnp must contain all required keys {required_keys}. "
                f"Provided keys: {input_mass_cnp.keys()}"
            )
        if any(value < 0 for value in input_mass_cnp.values()):
            raise ValueError(
                f"CNP values must be non-negative. Provided values: {input_mass_cnp}"
            )

        just_soil = VerticalOccupancy.SOIL
        all_strata = (
            VerticalOccupancy.SOIL | VerticalOccupancy.GROUND | VerticalOccupancy.CANOPY
        )

        # Check if the resource is found in the soil
        if (vertical_occupancy & just_soil) == just_soil:
            # Check if resource only in the soil
            if vertical_occupancy == just_soil:
                # Consumed pool entirely in soil so all mass goes to belowground mass
                for element, value in input_mass_cnp.items():
                    self.below_ground_mass_cnp[element] += value
            # Check if resource found across all three strata
            elif (vertical_occupancy & all_strata) == all_strata:
                # Consumed pool found across all three strata, so 1/3 so go to
                # belowground mass (and 2/3 to above)
                for element, value in input_mass_cnp.items():
                    self.above_ground_mass_cnp[element] += (2 / 3) * value
                    self.below_ground_mass_cnp[element] += (1 / 3) * value
            else:
                # Resource pool found in
                for element, value in input_mass_cnp.items():
                    self.above_ground_mass_cnp[element] += 0.5 * value
                    self.below_ground_mass_cnp[element] += 0.5 * value
        else:
            # Consumed pool entirely above ground pool so all mass goes to above mass
            for element, value in input_mass_cnp.items():
                self.above_ground_mass_cnp[element] += value
