"""This module provides the ArrayResources class and API used to communicate
between animal foraging at a grid cell level (using the Resource protocol) and data
saved in the main Data object as spatially structured arrays.

The module defines four classes:

* The ``ArrayResourceDefinition`` is a simple dataclass that is used to define the array
  resources that should be created when the model runs. An array resource is a Virtual
  Ecosystem data array that is structured by *at least* cell id and element, providing
  available biomasses of each element (CNP) by cell. We currently support array
  resources that are further structured by plant functional type (PFT).

* An ``ArrayResource`` instance is created a runtime from an ``ArrayResourceDefinition``
  and the Data object. It creates a new array in the Data object to record consumption
  from the array resource. It is also used to generate a list of ResourcePools: an
  ArrayResource has a one to many mapping to resource pools because of structuring by
  PFT.

* A ``ResourcePool`` instance manages consumption from single resource pool. This is an
  explicitly two dimensional slice through the resource array providing elemental masses
  by cell id. Each resource pool instance defines a `consumed_mass` attribute that
  tracks the total biomass consumed within each cell in the pool. An instance can be
  indexed to generate cell specific resources using the ``CellResource`` class.

    * The ``reset_resources`` method is used to refresh the available mass for
      consumption and reset the consumed mass to zero.
    * The ``write_consumption`` method can then be used to write actual consumed masses
      across cells back to the Data object.

* The ``CellResource`` class is used to manage actual consumption at the grid cell level
  within the simulation. It implements the ``Resource`` protocol, providing the
  ``cell_id``, ``vertical_occupancy`` and ``current_mass`` attributes and the
  ``get_eaten`` method. The instance also contains a reference to the ``consumed_mass``
  array in the parent ``ResourcePool`` and adds consumed mass to the cell_id specific
  entry in that array when the ``get_eaten`` method is called.


The workflow for the model is:

* The model code provides a globally defined list of ``ArrayResourceDefinition``
  instances that should be used within the model.
* At runtime, these are converted into a list of ``ArrayResource`` instances:

.. code: python

    array_resources = [
        ArrayResource(definition=defn, data=data) for defn in ARRAY_RESOURCES
    ]

* Those can then be expanded into a flat list of ResourcePools:

.. code: python

    resource_pools = list(
        chain.from_iterable([res.get_pools(data=data) for res in array_resources])
    )

* At the start of the model update, the ``set_resources`` method must be called each
  resource pool to populate the available masses with the current values from the Data
  instance.

* Individual pools can then be used to extract ``CellResource`` instances for grid cells
  that can be used as part of the foraging environment within each cells alongside other
  resources.

* At the end of a model update step, the ``write_consumption`` method should be called
  for each resource pool to write the consumed masses back to the Data object.

"""  # noqa: D205

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import xarray as xr
from numpy.typing import NDArray

from virtual_ecosystem.core.data import Data
from virtual_ecosystem.models.animal.animal_traits import DietType, VerticalOccupancy
from virtual_ecosystem.models.animal.protocols import Resource


@dataclass
class ArrayResourceDefinition:
    """Dataclass to define array resources."""

    pool_array: str
    """The name of an existing array in the Data object that can be used as an array
    resource."""
    consumed_array: str
    """The name of an array that will be used to record consumed biomass from the
    resource pool. This will have the same dimensional structure as the pool array."""
    vertical_occupancy: VerticalOccupancy
    """A VerticalOccupancy enum value indicating the vertical availability of the
    resource to consumers."""
    diet_type: DietType
    """A definition of the diet type that can forage from this resource."""
    lignin_array: str | None = None
    """The name of an existing array in the Data object that records the lignin content
    of the corresponding array resource (providing this is optional as many resources do
    not contain lignin)."""
    partition_by_pft: bool = False
    """Is the pool array partitioned along the plant functional type axis."""
    density: bool = False
    """Is the input pool density (per m^2) rather than just a mass."""


class ArrayResource:
    """Manager class for consumption from array resources.

    An ArrayResource instance identifies a single array in the Data object that can
    provide one or more resource pools for animal consumption. The `get_pools` method is
    used to return a list of ResourcePool instances available from the ArrayResource and
    then those pools can be used to provide per-cell CellResources. The internals of
    those classes are used to propagate consumption at the cell level back up to
    recording consumption within the Data object.

    .. TODO:

        Think about how to index coordinates within a pool. Currently we have hardcoded
        PFT specific pool generation, but if we - for example - want to go to
        partitioning by vertical dimensions then we may want a more general approach to
        identifting cell x element slices through pool arrays.
    """

    def __init__(self, definition: ArrayResourceDefinition, data: Data):
        """Constructor method for ArrayResource instances."""

        self.pool_array: str = definition.pool_array
        """The name of an array in the Data object that will be used as the biomass pool
        for feeding in this resource."""
        self.consumed_array: str = definition.consumed_array
        """The name of an array that will be used to record consumed biomass from the
        resource pool. This will have the same dimensional structure as the pool
        array."""
        self.vertical_occupancy: VerticalOccupancy = definition.vertical_occupancy
        """A VerticalOccupancy enum value indicating the vertical availability of the
        resource to consumers."""
        self.diet_type: DietType = definition.diet_type
        """A DietType enum value indicating the dietary availability of the resource to
        consumers."""

        self.lignin_array: str | None = definition.lignin_array
        """The name of an existing array in the Data object that records the lignin
        content of the corresponding array resource (providing this is optional as many
        resources do not contain lignin)."""
        self.partition_by_pft: bool = definition.partition_by_pft
        """Should this resource array be partitioned into separate resource pools by
        PFT."""
        self.density: bool = definition.density
        """Is the pool being accessed a density (per m^2) rather than a mass."""
        self.data: Data = data
        """The data instance containing array resources."""

        # Validate the pool array name
        if self.pool_array not in data:
            raise ValueError(f"Array resource not found: {self.pool_array}")

        # Create the consumption pool array if not handled elsewhere.
        if self.consumed_array not in data:
            # Create the consumption array in data
            self.data[self.consumed_array] = xr.zeros_like(self.data[self.pool_array])
            return

        # Otherwise, since the consumption pool exists in data, double check the array
        # dimensions are congruent. Using xr.equal with xr.zeros_like here to test the
        # equality of the dimension coordinates without asserting that the values are
        # equal.
        if self.consumed_array in data and not (
            xr.zeros_like(data[self.pool_array]).equals(
                xr.zeros_like(data[self.consumed_array])
            )
        ):
            raise ValueError(
                f"Resource consumption array dimensions ({self.consumed_array}) "
                f"do not match resource pool array ({self.pool_array})."
            )

    def get_pools(self, data: Data) -> list[ResourcePool]:
        """Return a list of resource pools from an ArrayResource.

        A single defined ArrayResource can contain multiple pools - currently only
        through partitioning by PFT but this could expand - so this method returns a
        list of the pools defined for the resource.

        Args:
            data: A data object containing resource arrays.
        """
        if self.partition_by_pft:
            # Check the pool array has PFT coordinates
            pfts = data[self.pool_array].coords.get("pft")
            if pfts is None:
                raise ValueError(
                    f"ArrayResource for {self.pool_array} cannot be partitioned by PFT."
                )

            # Return a resource for each PFT
            return [
                ResourcePool(data=data, resource=self, pft=pft, density=self.density)
                for pft in pfts.to_numpy()
            ]

        return [ResourcePool(data=data, resource=self, pft=None, density=self.density)]


ARRAY_RESOURCES = [
    ArrayResourceDefinition(
        pool_array="subcanopy_vegetation_cnp",
        consumed_array="subcanopy_vegetation_cnp_consumed",
        vertical_occupancy=VerticalOccupancy.GROUND,
        diet_type=DietType.FOLIAGE,
        # TODO - Currently subcanopy lignin is just a constant, so using this array
        # works, if lignin becomes more dynamic, this will have to be revisited
        lignin_array="subcanopy_vegetation_litter_lignin",
    ),
    ArrayResourceDefinition(
        pool_array="subcanopy_seedbank_cnp",
        consumed_array="subcanopy_seedbank_cnp_consumed",
        vertical_occupancy=VerticalOccupancy.GROUND,
        diet_type=DietType.SEEDS,
        # TODO - Currently subcanopy lignin is just a constant, so using this array
        # works, if lignin becomes more dynamic, this will have to be revisited
        lignin_array="subcanopy_seedbank_litter_lignin",
    ),
    ArrayResourceDefinition(
        pool_array="canopy_foliage_cnp",
        consumed_array="canopy_foliage_cnp_consumed",
        vertical_occupancy=VerticalOccupancy.CANOPY,
        diet_type=DietType.FOLIAGE,
        partition_by_pft=True,
        lignin_array="senesced_leaf_lignin",
    ),
    ArrayResourceDefinition(
        pool_array="canopy_seed_cnp",
        consumed_array="canopy_seed_cnp_consumed",
        vertical_occupancy=VerticalOccupancy.CANOPY,
        diet_type=DietType.SEEDS,
        partition_by_pft=True,
    ),
    ArrayResourceDefinition(
        pool_array="canopy_fruit_cnp",
        consumed_array="canopy_fruit_cnp_consumed",
        vertical_occupancy=VerticalOccupancy.CANOPY,
        diet_type=DietType.FRUIT,
        partition_by_pft=True,
    ),
    ArrayResourceDefinition(
        pool_array="seed_turnover_cnp",
        consumed_array="seed_turnover_cnp_consumed",
        vertical_occupancy=VerticalOccupancy.GROUND,
        diet_type=DietType.SEEDS,
        partition_by_pft=True,
    ),
    ArrayResourceDefinition(
        pool_array="fruit_turnover_cnp",
        consumed_array="fruit_turnover_cnp_consumed",
        vertical_occupancy=VerticalOccupancy.GROUND,
        diet_type=DietType.FRUIT,
        partition_by_pft=True,
    ),
    ArrayResourceDefinition(
        pool_array="litter_pool_above_metabolic_cnp",
        consumed_array="litter_consumed_above_metabolic_cnp",
        vertical_occupancy=VerticalOccupancy.GROUND,
        diet_type=DietType.DETRITUS,
        density=True,
    ),
    ArrayResourceDefinition(
        pool_array="litter_pool_above_structural_cnp",
        consumed_array="litter_consumed_above_structural_cnp",
        vertical_occupancy=VerticalOccupancy.GROUND,
        diet_type=DietType.DETRITUS,
        lignin_array="lignin_above_structural",
        density=True,
    ),
    ArrayResourceDefinition(
        pool_array="litter_pool_woody_cnp",
        consumed_array="litter_consumed_woody_cnp",
        vertical_occupancy=VerticalOccupancy.GROUND,
        diet_type=DietType.DETRITUS,
        lignin_array="lignin_woody",
        density=True,
    ),
    ArrayResourceDefinition(
        pool_array="litter_pool_below_metabolic_cnp",
        consumed_array="litter_consumed_below_metabolic_cnp",
        vertical_occupancy=VerticalOccupancy.SOIL,
        diet_type=DietType.DETRITUS,
        density=True,
    ),
    ArrayResourceDefinition(
        pool_array="litter_pool_below_structural_cnp",
        consumed_array="litter_consumed_below_structural_cnp",
        vertical_occupancy=VerticalOccupancy.SOIL,
        diet_type=DietType.DETRITUS,
        lignin_array="lignin_below_structural",
        density=True,
    ),
]
"""Definition of the set of ArrayResources available to the AnimalModel."""


class ResourcePool:
    """Interface between spatially structured resource pools and per-cell resources.

    The ResourcePool class is used to coordinate consumption within the AnimalModel from
    spatially structured biomass pool arrays within the Data object. An instance tracks
    a two-dimensional slice through a biomass array, that should be structured by
    cell_id and then elemental masses of Carbon, Nitrogen and Phosphorous.

    A cell-specific `CellResource` object, implementing the ``Resource`` protocol, can
    be obtained by indexing a ResourcePool by ``cell_id``. This ``CellResource``
    instance will be populated with the available elemental biomasses from the pool
    available for the specific cell.

    The CellResource is also passed a reference to the ``consumed_total_mass``
    attribute, to allow foraging in different cells to update consumption in a single
    location. Consumed total mass is used within this class to make it easier to track
    individual total masses removed by foraging - when the ``write_consumption`` method
    is called, these total masses are partitioned back into individual elemental masses
    in consumed mass array in the Data object.
    """

    def __init__(
        self,
        resource: ArrayResource,
        data: Data,
        density: bool,
        pft: str | None = None,
    ):
        self.data: Data = data
        self.resource: ArrayResource = resource
        self.pft = pft
        self.density = density

        # Type internal array attributes
        self.elemental_masses: NDArray[np.floating]
        """An array of biomasses of individual elements by cell_id."""
        self.consumed_mass: NDArray[np.floating]
        """An array of total consumed biomass by cell_id."""
        self.lignin_proportion: NDArray[np.floating] | None = None
        """An array of lignin proportions by cell_id (optional)."""

        # Populate the initial state of the resources.
        self.set_resources()

    def set_resources(self):
        """Resets the resource from the data object.

        This method updates the available elemental masses from the resource and resets
        the local array tracking consumed total biomass.
        """

        # Needs to collapse down to a single mass and element ratio per cell
        mass_data = self.data[self.resource.pool_array]

        # If a lignin array is provided save it it should be populated
        if self.resource.lignin_array:
            self.lignin_proportion = self.data[self.resource.lignin_array].to_numpy()
        else:
            self.lignin_proportion = None

        # Reduce to the PFT if needed
        # TODO - think about indexing here with a more general solution.
        if self.pft is not None:
            mass_data = mass_data.sel(pft=self.pft)

        # Store elemental biomasses per cell values into array attributes
        if self.density:
            # in the density case need to convert to mass units
            self.elemental_masses = mass_data.to_numpy() * self.data.grid.cell_area
        else:
            self.elemental_masses = mass_data.to_numpy()

        # Create a per cell array to track _total_ consumed biomass
        self.consumed_total_mass = np.zeros(self.data.grid.n_cells)

    def write_consumption(self):
        """Write accumulated consumption from the pool back into the data object."""

        # Calculate the consumed elemental masses from the current total consumed mass
        consumed_elemental_masses = (
            self.elemental_masses
            * (self.consumed_total_mass / self.elemental_masses.sum(axis=1))[:, None]
        )

        # Write the consumed elemental masses to the data object.
        if self.pft is None:
            self.data[self.resource.consumed_array][:] = consumed_elemental_masses
        else:
            self.data[self.resource.consumed_array].loc[:, self.pft, :] = (
                consumed_elemental_masses
            )

    def is_forageable(
        self, diet: DietType, vertical_occupancy: VerticalOccupancy
    ) -> bool:
        """Utility function to test if a consumer can access the resource pool.

        Args:
            diet: The diet type of the potential consumer
            vertical_occupancy: The vertical occupancy of the potential consumer.

        Returns:
            True if the resource pool is within both the diet and vertical occupancy of
            the functional group, otherwise False.
        """

        return ((diet & self.resource.diet_type).value > 0) and (
            (vertical_occupancy & self.resource.vertical_occupancy).value > 0
        )

    def __getitem__(self, cell_id) -> CellResource:
        """Indexing onto cell_id within the ArrayResource.

        This returns a CellResource object providing the required cell specific
        available mass.
        The total_consumed_mass attribute of the resources is however a view onto the
        specific cell in the ArrayResources.consumed_mass array, so that updates to the
        cell specific resource are automatically collated back into
        """
        return CellResource(
            resource=self.resource,
            available_elemental_masses=self.elemental_masses[cell_id],
            consumed_total_mass=self.consumed_total_mass,
            vertical_occupancy=self.resource.vertical_occupancy,
            lignin_proportion=self.lignin_proportion[cell_id]
            if self.lignin_proportion is not None
            else 0.0,
            cell_id=cell_id,
        )

    def __repr__(self) -> str:
        """Object representation."""

        if self.pft is None:
            return f"ResourcePool({self.resource.pool_array})"

        return f"ResourcePool({self.resource.pool_array}, pft={self.pft})"


class CellResource(Resource):
    """A per-cell resource for consumption.

    This class implements the Resource protocol for the AnimalModel but also provides
    data collection from individual cell consumption back up to spatially structured
    pools managed in ResourcePool instances.

    Args:
        resource: The array resource being targeted by the instance.
        available_elemental_masses: An array of the elemental masses available for
            consumption.
        vertical_occupancy: A VerticalOccupancy enum value indicating the vertical
            availability of the resource to consumers.
        cell_id: The cell_id being targeted by this resource.
        lignin_proportion: The lignin proportion of the array resource
            [kg{lignin C} kg{C}^-1]
        consumed_total_mass: A reference to the spatially structured array of consumed
            total biomass in the parent ResourcePool.
    """

    def __init__(
        self,
        resource: ArrayResource,
        available_elemental_masses: NDArray[np.floating],
        consumed_total_mass: NDArray[np.floating],
        vertical_occupancy: VerticalOccupancy,
        lignin_proportion: float,
        cell_id: int,
    ):
        self.resource = resource
        """The array resource being targeted by a CellResource instance."""
        self._mass_current = sum(available_elemental_masses)
        self.elemental_mass_ratios = available_elemental_masses / self._mass_current
        self.consumed_total_mass = consumed_total_mass
        self.vertical_occupancy = vertical_occupancy
        self.lignin_proportion = lignin_proportion
        self.cell_id = cell_id

    @property
    def mass_current(self):
        """The current available mass in the resource."""

        return self._mass_current

    def get_eaten(self, consumed_mass, consumer):
        """The get_eaten method for the PlantResource.

        Returns:
            A tuple where the first entry is the amount of CNP the animal ingests, the
            second entry is the amount animal losses to mechanical loss, and the third
            entry is the lignin proportion of the resource pool.
        """

        # Constrain by available mass.
        actual = min(self._mass_current, consumed_mass)

        # Handle zero or invalid request fast.
        if actual <= 0:
            zero = dict(C=0, N=0, P=0)
            return zero, zero, 0.0

        # Remove from the pool (this also refreshes CNP split).
        self._mass_current -= actual

        # Split consumed mass into ingested vs mechanical loss.
        # - Ingested mass that can be converted to tissue.
        ingested = actual * consumer.functional_group.mechanical_efficiency
        # - Mechanical loss mass (becomes waste routed by caller).
        waste = actual - ingested
        # - Record total consumption
        self.consumed_total_mass[self.cell_id] += actual

        # Translate ingested and waste biomasses to CNP dicts.
        consumed_cnp = dict(zip(["C", "N", "P"], self.elemental_mass_ratios * ingested))
        waste_cnp = dict(zip(["C", "N", "P"], self.elemental_mass_ratios * waste))

        return (consumed_cnp, waste_cnp, self.lignin_proportion)
