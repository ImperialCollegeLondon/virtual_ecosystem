"""Testing of the ``array_resources`` module."""

from __future__ import annotations

from itertools import chain
from types import SimpleNamespace

import numpy as np
from xarray import DataArray


def test_proof_of_concept_workflow():
    """Run a simple proof of concept of array resources."""

    from virtual_ecosystem.core.data import Data
    from virtual_ecosystem.core.grid import Grid
    from virtual_ecosystem.core.variables import VariableMetadata
    from virtual_ecosystem.models.animal.animal_traits import VerticalOccupancy
    from virtual_ecosystem.models.animal.array_resources import (
        ArrayResource,
        ArrayResourceDefinition,
    )

    # Create a Data object
    data = Data(Grid(cell_nx=3, cell_ny=4))

    # Modify the known_variables to allow some test variables
    for v in (
        "leaf_mass",
        "leaf_mass_consumed",
        "subcanopy_mass",
        "subcanopy_mass_consumed",
    ):
        data.known_variables[v] = VariableMetadata(
            name=v, description="", unit="", variable_type="float", axis=["spatial"]
        )

    # Define variables containing CNP masses in 20:2:1 ratio for a leaf mass resource
    # with 3 PFTs and a subcanopy vegetation mass with only cell id.
    pfts = np.array(["pioneer", "canopy", "emergent"])
    cell_ids = np.arange(data.grid.n_cells)
    elements = np.array(["C", "N", "P"])

    leaf_mass = DataArray(
        np.ones((data.grid.n_cells, elements.size, pfts.size)),
        dims=("cell_id", "element", "pft"),
        coords=dict(
            cell_id=cell_ids,
            element=elements,
            pft=pfts,
        ),
    ) * DataArray([20, 2, 1], dims="element", coords=dict(element=elements))

    subcanopy_mass = leaf_mass.sel(pft="pioneer").drop_vars("pft")

    data.add_from_dict(
        dict(
            leaf_mass=leaf_mass,
            subcanopy_mass=subcanopy_mass,
        )
    )

    # Define the array resources in the model source
    array_resource_definitions = [
        ArrayResourceDefinition(
            pool_array="leaf_mass",
            consumed_array="leaf_mass_consumed",
            vertical_occupancy=VerticalOccupancy.CANOPY,
            partition_by_pft=True,
        ),
        ArrayResourceDefinition(
            pool_array="subcanopy_mass",
            consumed_array="subcanopy_mass_consumed",
            vertical_occupancy=VerticalOccupancy.GROUND,
        ),
    ]

    # At run time, create the ArrayResource instances for each definition
    array_resources = [
        ArrayResource(definition=defn, data=data) for defn in array_resource_definitions
    ]

    # The consumed mass arrays should have been created
    assert "leaf_mass_consumed" in data
    assert "subcanopy_mass_consumed" in data

    # Get the resource pools from each resource and collapse into a flat list of
    # resource pools
    resource_pools = list(
        chain.from_iterable([res.get_pools(data=data) for res in array_resources])
    )

    assert len(resource_pools) == 4

    # Faked consumer namespace and hence a list of four consumers
    consumer = SimpleNamespace(
        functional_group=SimpleNamespace(
            mechanical_efficiency=0.9, conversion_efficiency=0.6
        )
    )

    consumers = [consumer] * 4

    rng = np.random.default_rng()

    # Starting an update, need to set the pool resources:
    for pool in resource_pools:
        pool.set_resources()

    # Testing consumption - running within an update
    for cell_id in np.arange(12):
        # Get the cell level resource for this cell from each array resource
        cell_resources = [res_pool[cell_id] for res_pool in resource_pools]

        # All consumers feed on all four resources
        for herbivore in consumers:
            for resource in cell_resources:
                resource.get_eaten(consumed_mass=rng.random(), consumer=herbivore)

    # After the loop finishes all ArrayResource instances must have non-zero consumed
    # mass.
    for res_pool in resource_pools:
        assert np.all(np.greater(res_pool.consumed_total_mass, 0))

    # The consumed mass arrays should all be zero still

    assert np.allclose(data["leaf_mass_consumed"], 0)
    assert np.allclose(data["subcanopy_mass_consumed"], 0)

    # Now use write_consumption to push the consumption value out to the Data object.
    # Note that the PFT specific resources are writing to different parts of the same
    # data array.
    for res_pool in resource_pools:
        res_pool.write_consumption()

    # The consumed masses in data should now be > 0.
    assert np.all(np.greater(data["leaf_mass_consumed"], 0))
    assert np.all(np.greater(data["subcanopy_mass_consumed"], 0))

    # And then, before starting the next loop:

    for res_pool in resource_pools:
        res_pool.set_resources()

    # The consumed masses in pool should now be > 0.
    # TODO - do we need to set consumed mass in data to zero? It will just be
    #        overwritten but the next write_consumption.
    for res_pool in resource_pools:
        assert np.allclose(res_pool.consumed_total_mass, 0)
