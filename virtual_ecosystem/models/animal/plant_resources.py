"""This module provides a draft of an ArrayResources class and API used to communicate
between animal foraging (using the Resource protocol) and data saved in the main Data
object.

The basic workflow is:

* An array resource object connects to four variables in the data object: a total mass
  variable (like leaf mass), two elemental ratio variables (or these could be masses -
  yet to determine), and lastly a variable to record consumed mass.

* Within any one time loop, the ``ArrayResource.set_mass_and_elemental_ratios()``
  method is used to set the available mass within each cells. The instance settings
  automatically optionally subset to a particular PFT and collapse vertical layers into
  a single pool per cell.

* Within cells, the `array_resource_instance[cell_id]` interface is used to extract a
  single cell resource as the PlantResource class, which implements the Resource
  protocol. Calls to ``PlantResource.get_eaten()`` reduce the available mass.

* The ``PlantResource.total_consumed_mass`` attribute is a view back onto an array
  within the ArrayResource, so herbivory within cells is automatically collated back at
  the ArrayResource level.

* At the end of a time loop, the ``ArrayResources.write_herbivory()`` method pushes the
  collated eaten mass back into the data.

* The next loop starts by running ``ArrayResource.set_mass_and_elemental_ratios()`` to
  reset the mass consumed and update to the new pool sizes.

"""  # noqa: D205

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from xarray import DataArray

from virtual_ecosystem.core.data import Data
from virtual_ecosystem.models.animal.animal_traits import VerticalOccupancy
from virtual_ecosystem.models.animal.protocols import Consumer, Resource


class ArrayResources:
    """Interface between plants model variables in ``Data`` and the animal module.

    An array resource instance is responsible for collapsing down carbon mass arrays,
    along with nitrogen and phosphorous ratio arrays to a single value per grid cell.
    This can involve dropping all but one named PFT and summing across vertical layers.

    The class can then be indexed by cell ID to return individual cell resource objects
    that conform to the Resource protocol. The resource object additionally includes an
    attribute (``total_consumed_mass``) that is a _view_ back onto the consumed mass
    attribute of the ArrayResource used to generate the cell resource. This allows the
    total herbivory across individual cell resources to be automatically collated, so
    that the total herbivory can be easily written back to the data object.
    """

    def __init__(
        self,
        mass_var: str,
        n_ratio_var: str,
        p_ratio_var: str,
        mass_consumed_var: str,
        vertical_occupancy: VerticalOccupancy,
        data: Data,
        vertical_layers: DataArray | None = None,
        pft: str | None = None,
        # cell_id: int,
    ):
        self.data = data
        self.mass_var = mass_var
        self.n_ratio_var = n_ratio_var
        self.p_ratio_var = p_ratio_var
        self.mass_consumed_var = mass_consumed_var
        self.vertical_occupancy = vertical_occupancy
        self.vertical_layers = vertical_layers
        self.pft = pft

        for var in (mass_var, n_ratio_var, p_ratio_var, mass_consumed_var):
            if var not in data:
                raise ValueError(
                    f"Cannot initialise ArrayResource: {var} not found in data object"
                )

        # Type internal array attributes
        self.mass: NDArray
        self.n_ratio: NDArray
        self.p_ratio: NDArray
        self.consumed_mass: NDArray

        # Populate the internal array attributes
        self.set_mass_and_elemental_ratios()

    def set_mass_and_elemental_ratios(self) -> None:
        """Sets the available mass and elemental masses from the data object.

        This also resets the consumed mass tracking, both within the ArrayResource and
        the named consumed mass variable in the data object.
        """

        # Needs to collapse down to a single mass and element ratio per cell
        mass_data = self.data[self.mass_var]
        n_ratio = self.data[self.n_ratio_var]
        p_ratio = self.data[self.p_ratio_var]

        if self.pft is not None:
            mass_data = mass_data.sel(pft=self.pft)
            n_ratio = n_ratio.sel(pft=self.pft)
            p_ratio = p_ratio.sel(pft=self.pft)

        if self.vertical_layers is not None:
            mass_data = mass_data.sel(vertical_layer=self.vertical_layers).sum(
                "vertical_layer"
            )
            # Currently assuming ratios are invariant vertically

        # Store per cell values into array attributes
        self.mass = mass_data.to_numpy()
        self.n_ratio = n_ratio.to_numpy()
        self.p_ratio = p_ratio.to_numpy()

        # Create a local array within the ArrayResources instance that accumulates the
        # mass consumption across cells and zero the consumed mass variable in the data
        # object.
        self.consumed_mass = np.zeros_like(self.mass)
        self.data[self.mass_consumed_var].loc[:] = 0

    def _cnp_props_for(self, cell_id: int) -> dict[str, float]:
        """Return C, N, P proportions for a given cell.

        Computes elemental proportions used to split a scalar plant mass into carbon,
        nitrogen, and phosphorus components. The carbon fraction is derived to ensure
        the three parts sum to one.

        Args:
            cell_id: Grid cell index.

        Returns:
            A dict with keys "c", "n", and "p" whose values sum to 1.0.
        """
        # c proportion = 1 - (n + p)
        n = float(self.n_ratio[cell_id])
        p = float(self.p_ratio[cell_id])
        return {"c": 1.0 - (n + p), "n": n, "p": p}

    def __getitem__(self, cell_id: int) -> PlantResources:
        """Return a per-cell resource view bound to this instance.

        The returned ``PlantResource`` reads current mass from this object's arrays
        and writes consumption back in-place to ``mass`` and ``consumed_mass`` for
        the specified cell.

        Args:
            cell_id: Grid cell index.

        Returns:
            A lightweight PlantResources view for the requested cell.
        """
        # Return a lightweight view that writes back into this instance
        return PlantResources(
            parent=self, cell_id=cell_id, vertical_occupancy=self.vertical_occupancy
        )

    def write_herbivory(self) -> None:
        """Write accumulated herbivory back into the data object."""

        if self.pft is None:
            self.data[self.mass_consumed_var][:] = self.consumed_mass
        else:
            self.data[self.mass_consumed_var].loc[:, self.pft] = self.consumed_mass

    def __repr__(self) -> str:
        """Object representation."""

        if self.pft is None:
            return f"ArrayResources({self.mass_var})"

        return f"ArrayResources({self.mass_var}, pft={self.pft})"


class PlantResources(Resource):
    """Single-cell plant resource that mutates its parent arrays in-place.

    This view object represents a plant resource available to herbivores within a
    single grid cell. It reads current mass directly from the parent
    ``ArrayResources`` and writes consumption back to the parent's ``mass`` and
    ``consumed_mass`` arrays.

    Attributes:
        _parent: The parent ``ArrayResources`` instance backing this view.
        cell_id: The grid cell index this resource represents.
        vertical_occupancy: The vertical occupancy of the resource pool.
    """

    def __init__(
        self,
        parent: ArrayResources,
        cell_id: int,
        vertical_occupancy: VerticalOccupancy,
    ) -> None:
        """Initialize a per-cell plant resource view.

        Args:
            parent: The backing ``ArrayResources`` instance.
            cell_id: Grid cell index for this resource.
            vertical_occupancy: Resource vertical occupancy enum.
        """
        # Store parent ArrayResources and the index we represent
        self._parent: ArrayResources = parent
        self.cell_id: int = cell_id
        self.vertical_occupancy: VerticalOccupancy = vertical_occupancy

    @property
    def mass_current(self) -> float:
        """Return the live, per-cell available mass.

        Returns:
            The current available mass (kg or model mass unit) for this cell.
        """
        # Read current value directly from parent mass array
        return float(self._parent.mass[self.cell_id])

    def get_eaten(
        self,
        consumed_mass: float,
        consumer: Consumer,
    ) -> tuple[dict[str, float], dict[str, float]]:
        """Consume mass and update parent arrays in-place.

        This method:
        1) Caps requested consumption by available mass,
        2) Subtracts the actual consumed mass from the parent's pool,
        3) Splits consumed mass into effective intake vs. mechanical loss using the
           consumer's mechanical and conversion efficiencies, and
        4) Writes the total consumed mass back to the parent's tracking array.

        Args:
            consumed_mass: Requested consumption amount for this step.
            consumer: Consumer cohort (animalcohort protocol)

        Returns:
            A 2-tuple:
                - herbivore_gain_cnp: Dict with keys ``"c"``, ``"n"``, ``"p"`` giving
                  net assimilated gains after efficiencies.
                - plant_waste_cnp: Dict with keys ``"c"``, ``"n"``, ``"p"`` giving the
                  mechanically lost portion returned to the environment.

        """
        # Constrain by available mass
        available: float = self.mass_current
        actual: float = min(available, consumed_mass)
        if actual <= 0.0:
            zero = {"c": 0.0, "n": 0.0, "p": 0.0}
            return zero, zero

        # Remove from the parent pool
        self._parent.mass[self.cell_id] -= actual

        # Efficiencies from consumer functional group
        fg = consumer.functional_group
        effective: float = actual * fg.mechanical_efficiency
        waste: float = actual - effective
        net_gain: float = effective * fg.conversion_efficiency

        # Record total consumption back on the parent
        self._parent.consumed_mass[self.cell_id] += actual

        # Elemental split (c proportion = 1 - (n + p))
        cnp = self._parent._cnp_props_for(self.cell_id)
        # Net assimilated gain for the herbivore
        gain = {elem: net_gain * prop for elem, prop in cnp.items()}
        # Mechanical-loss plant waste returned to environment
        plant_waste = {elem: waste * prop for elem, prop in cnp.items()}
        return gain, plant_waste


# ------------------------------------------------
# Example workflow
# ------------------------------------------------

# Create a Data object of masses and ratios for a leaf mass resource with 3 PFTs and
# vertical structure and a subcanopy vegetation mass with only cell id.

"""data = Data(Grid(cell_nx=3, cell_ny=4))
pfts = np.array(["pioneer", "canopy", "emergent"])
vertical_layers = np.arange(6)
cell_ids = np.arange(data.grid.n_cells)

mass = DataArray(
    np.ones((vertical_layers.size, data.grid.n_cells, pfts.size)),
    dims=("vertical_layer", "cell_id", "pft"),
    coords=dict(
        vertical_layer=vertical_layers,
        cell_id=cell_ids,
        pft=pfts,
    ),
)

elemental_ratio = DataArray(
    np.ones((data.grid.n_cells, pfts.size)),
    dims=("cell_id", "pft"),
    coords=dict(
        cell_id=cell_ids,
        pft=pfts,
    ),
)

data.add_from_dict(
    dict(
        leaf_mass=mass,
        leaf_n_ratio=elemental_ratio + 0.05,
        leaf_p_ratio=elemental_ratio + 0.02,
        leaf_mass_consumed=elemental_ratio,
        subcanopy_mass=mass[0, :, 0] * 3,
        subcanopy_n_ratio=elemental_ratio[:, 0] + 0.03,
        subcanopy_p_ratio=elemental_ratio[:, 0] + 0.01,
        subcanopy_mass_consumed=elemental_ratio[:, 0],
    )
)

# Get a tuple of all herbivory array resources

leaves = [
    ArrayResources(
        data=data,
        mass_var="leaf_mass",
        n_ratio_var="leaf_n_ratio",
        p_ratio_var="leaf_p_ratio",
        mass_consumed_var="leaf_mass_consumed",
        vertical_occupancy=VerticalOccupancy.CANOPY,
        pft=pft,
        vertical_layers=DataArray([0, 1, 2], dims="vertical_layer"),
    )
    for pft in data["pft"].to_numpy()
]

subcanopy = ArrayResources(
    data=data,
    mass_var="subcanopy_mass",
    n_ratio_var="subcanopy_n_ratio",
    p_ratio_var="subcanopy_p_ratio",
    mass_consumed_var="subcanopy_mass_consumed",
    vertical_occupancy=VerticalOccupancy.GROUND,
)


# Faked consumer namespace and hence a list of four consumers
consumer = SimpleNamespace(
    functional_group=SimpleNamespace(
        mechanical_efficiency=0.9, conversion_efficiency=0.6
    )
)

consumers = [consumer] * 4

rng = np.random.default_rng()

# At init, create a list of herbivory resources:

herbivory_resources = (*leaves, subcanopy)
print(herbivory_resources)

# Then within a single time loop
for cell_id in np.arange(12):
    # Get the cell level resource for this cell from each array resource
    cell_resources = [array_res[cell_id] for array_res in herbivory_resources]

    # All consumers feed on all four resources
    for herbivore in [consumer] * 4:
        for resource in cell_resources:
            resource.get_eaten(consumed_mass=rng.random(), consumer=herbivore)

# After the loop finishes print out the accumulated herbivory in the ArrayResource
# instances
for array_res in herbivory_resources:
    print(array_res)
    print(array_res.consumed_mass)

# The data object still doesn't know about herbivory
data["leaf_mass_consumed"]
data["subcanopy_mass_consumed"]

# So use the write_herbivory() to push the accumualate value out to the Data object.
# Note that the PFT specific resources are writing to different parts of the same data
# array.
for array_res in herbivory_resources:
    array_res.write_herbivory()

data["leaf_mass_consumed"]
data["subcanopy_mass_consumed"]

# And then, before starting the next loop:

for array_res in herbivory_resources:
    array_res.set_mass_and_elemental_ratios()"""
