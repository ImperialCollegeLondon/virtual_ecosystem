"""Fixtures for plants model testing."""

import io

import numpy as np
import pandas as pd
import pytest
from xarray import DataArray


@pytest.fixture
def flora(fixture_config):
    """Construct a minimal Flora object."""
    from virtual_ecosystem.models.plants.functional_types import get_flora_from_config

    flora = get_flora_from_config(fixture_config)

    return flora


@pytest.fixture
def fixture_plants_constants():
    """Shareable plants constants object."""

    from virtual_ecosystem.models.plants.constants import PlantsConsts

    return PlantsConsts()


@pytest.fixture
def fixture_exporter(fixture_config):
    """Construct a minimal CommunityDataExporter object.

    This exporter uses the default exporter settings that do not output plant community
    data files and so is not suitable for testing actual exporting, but is required to
    initialise a PlantsModel.
    """
    from virtual_ecosystem.models.plants.exporter import CommunityDataExporter

    exporter = CommunityDataExporter.from_config(fixture_config)

    return exporter


@pytest.fixture
def plants_data(fixture_core_components, flora):
    """Construct a minimal data object with plant cohort data."""
    from virtual_ecosystem.core.data import Data

    data = Data(grid=fixture_core_components.grid)
    n_cells = fixture_core_components.grid.n_cells

    # Add cohort configuration - this adds varying numbers of cohorts with different
    # canopy profiles to the four cells.
    cohort_csv = io.StringIO("""cell_id,n,pft,dbh
    0,400,broadleaf,1.0
    0,100,broadleaf,0.1
    0,100,shrub,0.01
    1,300,broadleaf,1.0
    1,100,broadleaf,0.1
    2,200,broadleaf,1.0
    2,100,shrub,0.01
    3,100,broadleaf,1.0
    3,100,broadleaf,0.1
    3,100,shrub,0.01""")

    cohorts = pd.read_csv(cohort_csv).to_xarray()

    for var in cohorts:
        data["plant_cohorts_" + var] = cohorts[var]

    data["plant_pft_propagules"] = DataArray(
        data=np.full((n_cells, flora.n_pfts), fill_value=100, dtype=np.integer),
        coords={
            "cell_id": fixture_core_components.grid.cell_id,
            "pft": flora.name,
        },
    )

    # Spatio-temporal data - DSR here is maintaining an earlier test value
    # of PPFD = 1000
    data["downward_shortwave_radiation"] = DataArray(
        data=np.full((n_cells, 12), fill_value=1000 / 2.04),
        coords={
            "cell_id": fixture_core_components.grid.cell_id,
            "time_index": np.arange(12),
        },
    )

    # Subcanopy vegetation masses kg C m2
    data["subcanopy_vegetation_biomass"] = DataArray(
        data=np.array([0.07] * n_cells),
        coords={"cell_id": fixture_core_components.grid.cell_id},
    )
    data["subcanopy_seedbank_biomass"] = DataArray(
        data=np.array([0.07] * n_cells),
        coords={"cell_id": fixture_core_components.grid.cell_id},
    )

    # Adding soil variables
    data["dissolved_ammonium"] = DataArray(np.array([5.0e-2] * n_cells))
    data["dissolved_nitrate"] = DataArray(np.array([7.5e-1] * n_cells))
    data["dissolved_phosphorus"] = DataArray(np.array([3.0e-3] * n_cells))
    data["ecto_supply_limit_n"] = DataArray(np.array([1.61e-3] * n_cells))
    data["arbuscular_supply_limit_n"] = DataArray(np.array([4.32e-3] * n_cells))
    data["ecto_supply_limit_p"] = DataArray(np.array([1.32e-4] * n_cells))
    data["arbuscular_supply_limit_p"] = DataArray(np.array([2.34e-4] * n_cells))

    # TODO - This elevation data is created so that the PlantsModel.calculate_turnover
    # function works in testing. Once that function has been replaced with something
    # more realistic this should be deleted
    data["elevation"] = DataArray(
        data=np.full((n_cells), fill_value=437.5),
        coords={
            "cell_id": fixture_core_components.grid.cell_id,
        },
    )

    # Canopy layer specific forcing variables from abiotic model
    layer_roles = fixture_core_components.layer_structure.layer_roles
    layer_shape = (
        fixture_core_components.layer_structure.n_layers,
        fixture_core_components.grid.n_cells,
    )

    # Setup the layers
    forcing_vars = (
        ("air_temperature", 20),
        ("vapour_pressure_deficit", 1000),
        ("atmospheric_pressure", 101325),
        ("atmospheric_co2", 400),
    )

    for var, value in forcing_vars:
        data[var] = DataArray(
            data=np.full(layer_shape, fill_value=value),
            dims=("layers", "cell_id"),
            coords={
                "layers": np.arange(len(layer_roles)),
                "layer_roles": ("layers", layer_roles),
                "cell_id": fixture_core_components.grid.cell_id,
            },
        )

    return data


@pytest.fixture
def fixture_canopy_layer_data(
    plants_data, fixture_plants_constants, flora, fixture_core_components
):
    """Shared canopy layer data.

    The fixture supplies a dictionary of data values expected from the canopy cohort
    data and subcanopy biomasses in the plants_data fixture. Each entry provides a tuple
    of the variable name to be tested and a dataarray containing the variables to be
    tested. Some variables have multiple test cases to allow different stages of the
    data population process to be checked.

    The expected values are derived here from first principles using pyrealm and direct
    calculations. This avoids hard coding test values and the point of this test is to
    check that the values obtained directly match what is assembled through the plants
    model.
    """

    from pyrealm.demography.canopy import Canopy
    from pyrealm.demography.community import Cohorts, Community

    # Package the community data up into cell groups
    community_data = plants_data[
        [
            "plant_cohorts_cell_id",
            "plant_cohorts_dbh",
            "plant_cohorts_pft",
            "plant_cohorts_n",
        ]
    ]
    cells = community_data.groupby("plant_cohorts_cell_id")

    # Build the pyrealm community for each cell
    communities = [
        Community(
            flora=flora,
            cell_area=fixture_core_components.grid.cell_area,
            cell_id=int(cell_id),
            cohorts=Cohorts(
                dbh_values=cell_data["plant_cohorts_dbh"].to_numpy(),
                n_individuals=cell_data["plant_cohorts_n"].to_numpy(),
                pft_names=cell_data["plant_cohorts_pft"].to_numpy(),
            ),
        )
        for cell_id, cell_data in cells
    ]

    # Fit the PPA solution for each cell
    canopies = [Canopy(cmnty, fit_ppa=True) for cmnty in communities]

    # Extract direct pyrealm canopy data for different variable test cases.
    lyr_struct = fixture_core_components.layer_structure

    # Create a dictionary of test cases of pairs of data object variable names and empty
    # layer structure data arrays from the template.
    expected = {
        test_case: (var_name, lyr_struct.from_template())
        for test_case, var_name in (
            ("layer_heights_canopy", "layer_heights"),  # canopy heights
            ("layer_heights_full", "layer_heights"),  #   + ground layer heights
            ("leaf_area_index_canopy", "leaf_area_index"),  # canopy lai
            ("leaf_area_index_full", "leaf_area_index"),  #   + subcanopy vegetation
            ("layer_fapar_canopy", "layer_fapar"),  # canopy fapar
            ("layer_fapar_full", "layer_fapar"),  #   + subcanopy vegetation
            ("layer_leaf_mass", "layer_leaf_mass"),
        )
    }

    # Fill in the plant canopy data
    for idx, (cmty, cnpy) in enumerate(zip(communities, canopies)):
        # Heights - need to add top of canopy and reference height and remove the zero
        #           that is always included in pyrealm list of heights.
        heights = np.concat(
            [
                [cnpy.max_stem_height + lyr_struct.above_canopy_height_offset],
                [cnpy.max_stem_height],
                cnpy.heights[:-1, 0],
            ]
        )

        cnpy_height_idx = np.arange(0, heights.size)
        expected["layer_heights_full"][1][cnpy_height_idx, idx] = heights
        expected["layer_heights_canopy"][1][cnpy_height_idx, idx] = heights

        # Populate the canopy LAI and fAPAR values
        cnpy_idx = np.arange(1, heights.size)
        expected["leaf_area_index_canopy"][1][cnpy_idx, idx] = (
            cnpy.community_data.average_layer_lai
        )
        expected["leaf_area_index_full"][1][cnpy_idx, idx] = (
            cnpy.community_data.average_layer_lai
        )
        expected["layer_fapar_canopy"][1][cnpy_idx, idx] = (
            cnpy.community_data.average_layer_fapar
        )
        expected["layer_fapar_full"][1][cnpy_idx, idx] = (
            cnpy.community_data.average_layer_fapar
        )

        # Leaf mass - calculate from stem leaf area
        # TODO - maybe pyrealm should provide stem_leaf_mass?
        expected["layer_leaf_mass"][1][cnpy_idx, idx] = (
            cnpy.cohort_data.stem_leaf_area
            * (1 / cmty.stem_traits.sla)
            * cmty.stem_traits.lai
            * cmty.cohorts.n_individuals
        ).sum(axis=1)

    # Fill soil and surface layer depths
    expected["layer_heights_full"][1][lyr_struct.index_surface] = (
        lyr_struct.surface_layer_height
    )
    expected["layer_heights_full"][1][lyr_struct.index_all_soil] = (
        lyr_struct.soil_layer_depths[:, None]
    )

    # Fill in subcanopy vegetation details
    # - calculate the through canopy transmission as 1 - sum of canopy fapar.
    through_canopy_transmission = 1 - expected["layer_fapar_canopy"][1].sum(axis=0)

    # - Beer Lambert transmission from subcanopy vegetation
    subcanopy_vegetation_lai = (
        plants_data["subcanopy_vegetation_biomass"]
        * fixture_plants_constants.subcanopy_specific_leaf_area
    )
    subcanopy_transmission = np.exp(
        -fixture_plants_constants.subcanopy_extinction_coef * subcanopy_vegetation_lai
    )

    # Update appropriate rows - add subcanopy vegetation leaf area to surface layer
    expected["leaf_area_index_full"][1][lyr_struct.index_surface] = (
        subcanopy_vegetation_lai
    )
    # Calculate fAPAR for subcanopy vegetation
    expected["layer_fapar_full"][1][lyr_struct.index_surface] = (
        through_canopy_transmission * (1 - subcanopy_transmission)
    )

    # Shortwave radiation is the fraction of canopy top DSR that is absorbed by each
    # layer plus what reaches the ground
    dsr_t0 = plants_data["downward_shortwave_radiation"][:, 0].drop_vars("time_index")
    dsr_by_layer = expected["layer_fapar_full"][1] * dsr_t0
    ground_incident_dsr = dsr_t0 - dsr_by_layer.sum(axis=0)
    dsr_by_layer[lyr_struct.index_topsoil] = ground_incident_dsr

    expected["shortwave_absorption"] = ("shortwave_absorption", dsr_by_layer)

    return expected


@pytest.fixture
def fxt_plants_model(
    plants_data,
    flora,
    fixture_core_components,
    fixture_plants_constants,
    fixture_exporter,
):
    """Return a simple PlantsModel instance."""

    from virtual_ecosystem.models.plants.plants_model import PlantsModel

    return PlantsModel(
        data=plants_data,
        core_components=fixture_core_components,
        flora=flora,
        exporter=fixture_exporter,
        model_constants=fixture_plants_constants,
    )
