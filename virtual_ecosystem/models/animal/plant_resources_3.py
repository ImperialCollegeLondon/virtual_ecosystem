"""The ''plant_resources'' classes provides toy plant module functionality that are
required for setting up and testing the early stages of the animal module.
"""  # noqa: D205

from virtual_ecosystem.core.data import Data
from virtual_ecosystem.models.animal.animal_traits import VerticalOccupancy
from virtual_ecosystem.models.animal.protocols import Consumer


class PlantResource:
    """Mutable per-cell plant resource for herbivory integration.

    This class represents a single resource type (e.g., leaves, seedbank) in a
    specific grid cell. It initializes its mass from the ``Data`` object using
    the provided ``variable_name`` and ``cell_id``. If the backing variable has
    a plant functional type (PFT) dimension, per-PFT masses are collected into
    ``mass_by_pft`` and summed to produce ``mass_current``. Otherwise a scalar
    per-cell value is read.

    Stoichiometry is currently a toy fixed proportion (C=0.7, N=0.2, P=0.1) and
    is used to derive ``mass_stoich`` from ``mass_current``. These values are
    placeholders until plant-side CNP data are exposed.
    """

    def __init__(
        self,
        data: Data,
        cell_id: int,
        resource_name: str,
        variable_name: str,
        vertical_occupancy: VerticalOccupancy,
        *,
        pft_dim: str = "plant_functional_type",
        cnp_proportions: dict[str, float] | None = None,
    ) -> None:
        """Construct and initialize from ``Data``.

        Reads the mass for ``variable_name`` at ``cell_id``. If the variable has
        a PFT axis named ``pft_dim``, per-PFT masses are recorded and summed to
        set ``mass_current``. Otherwise a scalar value is read. Toy CNP fractions
        are installed if none are provided and ``mass_stoich`` is computed.

        Args:
            data: The global ``Data`` object.
            cell_id: Grid cell identifier.
            resource_name: Human-readable name for this resource.
            variable_name: Name of the backing variable in ``Data``.
            vertical_occupancy: Vertical position enum for this resource.
            pft_dim: Dimension name for PFTs, if present.
            cnp_proportions: Optional C, N, P mass fractions.

        Raises:
            KeyError: If ``variable_name`` is missing in ``data``.
            Exception: Any xarray selection errors will propagate.
        """
        # Identity / config
        self.cell_id = cell_id
        self.resource_name = resource_name
        self.variable_name = variable_name
        self.vertical_occupancy = vertical_occupancy
        self.pft_dim = pft_dim

        # Derived stores
        self.mass_current: float = 0.0
        self.mass_by_pft: dict[str, float] = {}

        # Toy stoichiometry until Plants exposes element data
        self.cnp_proportions: dict[str, float] = (
            {"carbon": 0.7, "nitrogen": 0.2, "phosphorus": 0.1}
            if cnp_proportions is None
            else dict(cnp_proportions)
        )
        self.mass_stoich: dict[str, float] = {}

        # Read backing array; let KeyError/xarray errors surface if misconfigured
        full_resource_array = data[self.variable_name]
        cell_resource_array = full_resource_array.sel(cell_id=self.cell_id)

        # If a PFT axis exists, collect per-PFT and sum; otherwise read scalar
        if self.pft_dim in getattr(cell_resource_array, "dims", ()):
            pfts = cell_resource_array.coords[self.pft_dim].values  # labels per PFT
            self.mass_by_pft = {
                str(pft_label): float(
                    cell_resource_array.sel({self.pft_dim: pft_label}).item()
                )
                for pft_label in pfts
            }

            self.mass_current = sum(self.mass_by_pft.values())
        else:
            self.mass_current = float(cell_resource_array.item())

            # Initialize derived element masses
            self.update_stoichiometric_mass()

    def update_stoichiometric_mass(self) -> None:
        """Recompute per-element masses from total mass and CNP fractions.

        Uses ``mass_current`` and ``cnp_proportions`` to populate
        ``mass_stoich`` for keys ``carbon``, ``nitrogen``, and ``phosphorus``.
        """
        self.mass_stoich = {
            element: self.mass_current * proportion
            for element, proportion in self.cnp_proportions.items()
        }

    def set_mass_current(self, new_mass: float) -> None:
        """Set aggregate mass and refresh derived stoichiometric masses.

        Args:
            new_mass: New aggregate mass (kg).

        Raises:
            ValueError: If ``new_mass`` is negative.
        """
        if new_mass < 0:
            raise ValueError("Mass cannot be negative.")
        self.mass_current = new_mass
        self.update_stoichiometric_mass()

    def get_eaten(
        self, consumed_mass: float, herbivore: "Consumer"
    ) -> tuple[dict[str, float], dict[str, float]]:
        """Apply herbivory and return herbivore gain and plant litter CNP.

        Mass is removed from the resource up to the requested amount. The mass
        is partitioned into:
        - Herbivore net gain: ``consumed_mass * mech_eff * conv_eff``
        - Plant litter: ``consumed_mass * (1 - mech_eff)``

        Stoichiometric masses are computed by multiplying these totals by
        ``cnp_proportions``. ``mass_current`` is reduced accordingly and
        ``mass_stoich`` is updated.

        Args:
            consumed_mass: Intended wet mass to be consumed (kg).
            herbivore: Consumer with efficiency parameters.

        Returns:
            Tuple of two dicts:
            - Herbivore gain CNP ``{"carbon","nitrogen","phosphorus"}``
            - Plant litter CNP ``{"carbon","nitrogen","phosphorus"}``

        Notes:
            If ``consumed_mass <= 0``, both returned dicts contain zeros.
        """
        # Handle zero or invalid consumption
        if consumed_mass <= 0:
            zeros = {e: 0.0 for e in self.cnp_proportions}
            return zeros, zeros

        # Cap requested mass to what is available
        actual_consumed_mass = min(self.mass_current, consumed_mass)

        # Update plant mass (stoichiometry auto-updates via setter)
        self.set_mass_current(self.mass_current - actual_consumed_mass)

        # Partition by mechanical efficiency
        mech_eff = herbivore.functional_group.mechanical_efficiency
        effective_mass = actual_consumed_mass * mech_eff
        excess_mass = actual_consumed_mass * (1.0 - mech_eff)

        # Convert effective mass to body mass by conversion efficiency
        conv_eff = herbivore.functional_group.conversion_efficiency
        net_mass_gain = effective_mass * conv_eff

        # Map to stoichiometric masses
        herbivore_gain_cnp = {
            elem: net_mass_gain * prop for elem, prop in self.cnp_proportions.items()
        }
        plant_litter_cnp = {
            elem: excess_mass * prop for elem, prop in self.cnp_proportions.items()
        }

        return herbivore_gain_cnp, plant_litter_cnp
