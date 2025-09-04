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

from types import SimpleNamespace

import numpy as np
from numpy.typing import NDArray
from xarray import DataArray

from virtual_ecosystem.core.data import Data
from virtual_ecosystem.core.grid import Grid
from virtual_ecosystem.models.animal.animal_traits import VerticalOccupancy
from virtual_ecosystem.models.animal.protocols import Resource

# Data object

data = Data(Grid(cell_nx=3, cell_ny=4))
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

    def set_mass_and_elemental_ratios(self):
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

    def __getitem__(self, cell_id) -> PlantResource:
        """Indexing onto cell_id within the ArrayResource.

        This returns a PlantResource object providing the required cell specific masses.
        The total_consumed_mass attribute of the resources is however a view onto the
        specific cell in the ArrayResources.consumed_mass array, so that updates to the
        cell specific resource are automatically collated back into
        """
        return PlantResource(
            mass_var=self.mass_var,
            mass_current=self.mass[cell_id],
            n_ratio=self.n_ratio[cell_id],
            p_ratio=self.p_ratio[cell_id],
            total_consumed_mass=self.consumed_mass[..., cell_id],
            vertical_occupancy=self.vertical_occupancy,
            cell_id=cell_id,
        )

    def write_herbivory(self):
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


class PlantResource(Resource):
    """Single cell plant resource implementing the Resource protocol."""

    def __init__(
        self,
        mass_var: str,
        mass_current: float,
        n_ratio: float,
        p_ratio: float,
        total_consumed_mass: NDArray,
        vertical_occupancy: VerticalOccupancy,
        cell_id: int,
    ):
        self.mass_var = mass_var
        self._mass_current = mass_current
        self.n_ratio = n_ratio
        self.p_ratio = p_ratio
        self.total_consumed_mass = total_consumed_mass
        self.vertical_occupancy = vertical_occupancy
        self.cell_id = cell_id

        self.cnp_proportions = dict(c=1 - (n_ratio + p_ratio), n=n_ratio, p=p_ratio)

    @property
    def mass_current(self):
        """The current available mass in the resource."""

        return self._mass_current

    def get_eaten(self, consumed_mass, consumer):
        """The get_eaten method for the PlantResource."""

        # Constrain by available mass.
        actual = min(self._mass_current, consumed_mass)

        # Handle zero or invalid request fast.
        if actual <= 0:
            zero = dict(c=0, n=0, p=0)
            return zero, zero

        # Remove from the pool (this also refreshes CNP split).
        self._mass_current -= actual

        # Split consumed mass into effective vs mechanical loss.
        # - Effective mass that can be converted to tissue.
        effective = actual * consumer.functional_group.mechanical_efficiency
        # - Mechanical loss mass (becomes waste routed by caller).
        waste = actual - effective
        # - Net gain after conversion efficiency.
        net_gain = effective * consumer.functional_group.conversion_efficiency
        # - Record total consumption
        self.total_consumed_mass += actual

        # Translate scalar masses to CNP dicts.
        herbivore_gain_cnp = {e: net_gain * p for e, p in self.cnp_proportions.items()}
        plant_waste_cnp = {e: waste * p for e, p in self.cnp_proportions.items()}

        return herbivore_gain_cnp, plant_waste_cnp


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

herbivory_resources = (*leaves, subcanopy)

print(herbivory_resources)

# Faked consumer namespace and list of four consumers
consumer = SimpleNamespace(
    functional_group=SimpleNamespace(
        mechanical_efficiency=0.9, conversion_efficiency=0.6
    )
)

consumers = [consumer] * 4

rng = np.random.default_rng()


# Within a single time loop
for cell_id in np.arange(12):
    cell_resources = [array_res[cell_id] for array_res in herbivory_resources]

    for herbivore in [consumer] * 4:
        for resource in cell_resources:
            resource.get_eaten(consumed_mass=rng.random(), consumer=herbivore)

# Look at the accumulated herbivory in the ArrayResource instances
for array_res in herbivory_resources:
    print(array_res)
    print(array_res.consumed_mass)


data["leaf_mass_consumed"]
data["subcanopy_mass_consumed"]

for array_res in herbivory_resources:
    array_res.write_herbivory()

data["leaf_mass_consumed"]
data["subcanopy_mass_consumed"]

for array_res in herbivory_resources:
    array_res.set_mass_and_elemental_ratios()
