"""Tests for the biomasses_new module."""

from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
from numpy.testing import assert_allclose

ELEMENTS = ((1, "n"), (2, "p"))


@pytest.fixture
def fixture_biomass_components():
    """Provides a tuple of biomass components."""

    cohorts = pd.DataFrame(
        dict(
            # TODO - revisit the ratio names and maybe automate the creation of
            #        consistent names when loading traits to simplify the biomass
            #        interface.
            zeta=[0.1, 0.1],
            sla=[2.0, 2.0],
            p_foliage_for_reproductive_tissue=[0.5, 0.5],
            pft_names=["shrub", "broadleaf"],
            foliage_c_n_ratio=[5.0, 6.0],  # Why do these start differently!
            leaf_turnover_c_n_ratio=[10.0, 12.0],
            foliage_c_p_ratio=[5.0, 6.0],
            leaf_turnover_c_p_ratio=[10.0, 12.0],
            # stem_c_n_ratio=[5.0, 6.0],
            deadwood_c_n_ratio=[5.0, 6.0],
            # stem_c_p_ratio=[5.0, 6.0],
            deadwood_c_p_ratio=[5.0, 6.0],
            root_turnover_c_n_ratio=[5.0, 6.0],
            root_turnover_c_p_ratio=[5.0, 6.0],
            plant_reproductive_tissue_turnover_c_n_ratio=[5.0, 6.0],
            plant_reproductive_tissue_turnover_c_p_ratio=[5.0, 6.0],
        )
    )

    stem_allometry = SimpleNamespace(
        foliage_mass=np.array([50.0, 80.0]),
        stem_mass=np.array([100.0, 150.0]),
        fine_root_mass=np.array([10.0, 16.0]),
        fruit_mass=np.array([10.0, 20.0]),
        seed_mass=np.array([10.0, 20.0]),
    )

    stem_allocation = SimpleNamespace(
        foliage_turnover=np.array([30.0, 15.0]),
        branch_turnover=np.array([0, 0]),
        fine_root_turnover=np.array([3.0, 1.5]),
        fruit_turnover=np.array([2.5, 1.0]),
        seed_turnover=np.array([2.5, 1.0]),
    )

    growth_increments = SimpleNamespace(
        delta_foliage_mass=np.array([20.0, 10.0]),
        delta_stem_mass=np.array([10.0, 5.0]),
        delta_fine_root_mass=np.array([10.0, 5.0]),
        delta_fruit_mass=np.array([2.0, 1.0]),
        delta_seed_mass=np.array([2.0, 1.0]),
    )

    return cohorts, stem_allometry, stem_allocation, growth_increments


@pytest.fixture
def fixture_biomasses(fixture_community):
    """Fixture providing a Biomasses instance."""

    from virtual_ecosystem.models.plants.biomasses import (
        Biomasses,
        Element,
        FoliageBiomass,
        ReproductiveBiomass,
        RootBiomass,
        StemBiomass,
    )

    foliage = FoliageBiomass(
        community=fixture_community,
        carbon_mass=fixture_community.stem_allometry.foliage_mass.copy(),
        element_masses={
            "N": Element(
                name="n",
                ideal_ratio=np.array([5.0, 6.0]),
                actual_element_mass=np.array([5.0, 20.0]),
                turnover_ratio=np.array([10.0, 12.0]),
            ),
            "P": Element(
                name="p",
                ideal_ratio=np.array([5.0, 6.0]),
                actual_element_mass=np.array([5.0, 20.0]),
                turnover_ratio=np.array([10.0, 12.0]),
            ),
        },
    )

    root = RootBiomass(
        community=fixture_community,
        carbon_mass=fixture_community.stem_allometry.fine_root_mass.copy(),
        element_masses={
            "N": Element(
                name="n",
                ideal_ratio=np.array([5.0, 7.0]),
                actual_element_mass=np.array([10.0, 25.0]),
                turnover_ratio=np.array(
                    [
                        5.0,
                        7.0,
                    ]
                ),  # TODO - this is misleading. It should be current Cx_ratio
            ),
            "P": Element(
                name="p",
                ideal_ratio=np.array([5.0, 7.0]),
                actual_element_mass=np.array([10.0, 25.0]),
                turnover_ratio=np.array([5.0, 7.0]),
            ),
        },
    )

    wood = StemBiomass(
        community=fixture_community,
        carbon_mass=fixture_community.stem_allometry.stem_mass.copy(),
        element_masses={
            "N": Element(
                name="n",
                ideal_ratio=np.array([10.0, 8.0]),
                actual_element_mass=np.array([5.0, 30.0]),
                turnover_ratio=np.array([10.0, 8.0]),
            ),
            "P": Element(
                name="p",
                ideal_ratio=np.array([10.0, 8.0]),
                actual_element_mass=np.array([5.0, 30.0]),
                turnover_ratio=np.array([10.0, 8.0]),
            ),  # TODO - This is sort of misleading, since the mass is zero, if we
            # have turnover (branchfall etc) it would probably be at the current
            # Cx_ratio
        },
    )

    repro = ReproductiveBiomass(
        community=fixture_community,
        carbon_mass=fixture_community.stem_allometry.reproductive_tissue_mass.copy(),
        element_masses={
            "N": Element(
                name="n",
                ideal_ratio=np.array([4.0, 5.0]),
                actual_element_mass=np.array([8.0, 12.0]),
                turnover_ratio=np.array(
                    [
                        4.0,
                        5.0,
                    ]
                ),  # TODO - again, this is misleading. It should be current Cx_ratio
            ),
            "P": Element(
                name="p",
                ideal_ratio=np.array([4.0, 5.0]),
                actual_element_mass=np.array([8.0, 12.0]),
                turnover_ratio=np.array([4.0, 5.0]),
            ),
        },
    )

    return Biomasses(
        tissues=[foliage, repro, wood, root],
        community=fixture_community,
    )


# def test_Biomasses_append(fixture_biomasses):
#     """Test the Biomasses append() method.

#     This should double the length of the mass arrays. The Element.append() and
#     BiomassTissueABC.append() methods are tested above, so this tests a subset of the
#     attributes at each level.
#     """

#     # Quick check that the initial values have len 2
#     for tissue in fixture_biomasses.tissues:
#         assert len(tissue.carbon_mass) == 2

#     # Append the biomasses fixture onto itself
#     fixture_biomasses.append(fixture_biomasses)

#     # Check tissue, element and surplus arrays are now len 4.
#     for tissue in fixture_biomasses.tissues:
#         assert len(tissue.carbon_mass) == 4

#         for elem in tissue.element_masses.values():
#             assert len(elem.actual_element_mass) == 4

#     for surplus in fixture_biomasses.element_surplus.values():
#         assert len(surplus) == 4


@pytest.mark.parametrize(
    argnames=("tissue_class"),
    argvalues=(
        pytest.param(
            "FoliageBiomass",
            id="foliage",
        ),
        pytest.param(
            "RootBiomass",
            id="root",
        ),
        pytest.param(
            "StemBiomass",
            id="stem",
        ),
        pytest.param(
            "FruitBiomass",
            id="fruit",
        ),
        pytest.param(
            "SeedBiomass",
            id="seed",
        ),
    ),
)
def test_BiomassTissue__init__and_methods(
    fixture_biomass_components,
    tissue_class,
):
    """Test default factory method gives a biomass tissue with the correct masses."""

    import virtual_ecosystem.models.plants.biomasses_new as biomasses

    cohorts, allometry, allocation, growth_increments = fixture_biomass_components

    # Get the class for the parameterisation
    BiomassTissueClass = getattr(biomasses, tissue_class)

    # Get the attributes
    mass_attr = BiomassTissueClass.mass_attr
    turnover_mass_attr = BiomassTissueClass.turnover_mass_attr
    growth_mass_attr = BiomassTissueClass.growth_mass_attr
    ideal_ratio_attr = BiomassTissueClass.ideal_ratio_attr
    turnover_ratio_attr = BiomassTissueClass.turnover_ratio_attr

    # Initialise
    tissue = BiomassTissueClass(
        cohorts=cohorts,
        allometry=allometry,
    )

    # Check carbon mass is equal to the appropriate mass attribute in the original
    # allometry.
    assert_allclose(tissue.elemental_masses[:, 0], getattr(allometry, mass_attr))

    # Check that the generated element masses are at their expected ideal ratios from
    # the cohort traits
    for idx, elem in ELEMENTS:
        assert_allclose(
            tissue.elemental_masses[:, idx],
            tissue.elemental_masses[:, 0]
            * (1 / cohorts[ideal_ratio_attr.replace("ELEM", elem)]),
        )

    # Deficits should all be zero.
    assert_allclose(tissue.deficits, np.zeros_like(tissue.elemental_masses))

    # Cx_ratio property should be equal to ideals
    assert_allclose(tissue.Cx_ratio, tissue.ideal_ratios)

    # Create a tissue with non-default ratios
    deficits = np.ones_like(tissue.elemental_masses)
    deficits[:, 0] = 0  # no deficit in carbon

    depleted_tissue = BiomassTissueClass(
        cohorts=cohorts,
        allometry=allometry,
        initial_masses=tissue.elemental_masses - deficits,
    )

    # Deficits property on the tissue should equal the removed deficits.
    assert_allclose(depleted_tissue.deficits, deficits)

    # Replace deficits masses
    depleted_tissue.add_elemental_masses(deficits)

    # Deficits should now all be zero.
    assert_allclose(
        depleted_tissue.deficits, np.zeros_like(depleted_tissue.elemental_masses)
    )

    # Turnover:
    #   Calculate the values directly - this is really a bit circular but there's not an
    #   obvious better test
    pre_turnover_masses = tissue.elemental_masses.copy()
    calculated_turnover = tissue.get_turnover(allocation)

    # Calculate from attributes
    expected_carbon = getattr(allocation, turnover_mass_attr)
    columns = [expected_carbon]
    for _, elem in ELEMENTS:
        columns.append(
            expected_carbon
            / cohorts[turnover_ratio_attr.replace("ELEM", elem)].to_numpy()
        )

    # Turnover as expected
    assert_allclose(calculated_turnover, np.stack(columns, axis=1))

    # Check no mass actually removed
    assert_allclose(tissue.elemental_masses, pre_turnover_masses)

    # Growth:
    calculated_growth = tissue.apply_growth(growth_increments)

    #   Again calculate the values directly - this is really a bit circular but there's
    #   not an obvious better test
    expected_carbon = getattr(growth_increments, growth_mass_attr)
    columns = [expected_carbon]
    for _, elem in ELEMENTS:
        columns.append(
            expected_carbon / cohorts[ideal_ratio_attr.replace("ELEM", elem)].to_numpy()
        )

    # Growth as expected
    expected_growth = np.stack(columns, axis=1)
    assert_allclose(calculated_growth, expected_growth)

    # Biomasses are now larger
    assert_allclose(tissue.elemental_masses, pre_turnover_masses + expected_growth)


@pytest.mark.parametrize(
    argnames="tissue_class",
    argvalues=(
        pytest.param("FoliageBiomass", id="foliage"),
        pytest.param("RootBiomass", id="root"),
        pytest.param("StemBiomass", id="stem"),
        pytest.param("FruitBiomass", id="fruit"),
        pytest.param("SeedBiomass", id="seed"),
    ),
)
def test_BiomassTissue_append(fixture_biomass_components, tissue_class):
    """Tests the shared append() method of BiomassTissueABC."""

    import virtual_ecosystem.models.plants.biomasses_new as biomasses

    cohorts, allometry, _, _ = fixture_biomass_components

    BiomassTissueClass = getattr(biomasses, tissue_class)

    # Generate two biomass objects, one with twice the masses
    biomasses_1 = BiomassTissueClass(cohorts=cohorts, allometry=allometry)
    biomasses_2 = BiomassTissueClass(cohorts=cohorts, allometry=allometry)
    biomasses_2.elemental_masses *= 2

    # Append
    biomasses_1.append(biomasses_2)

    # Check shapes
    for attr in ("elemental_masses", "ideal_ratios", "turnover_ratios"):
        assert getattr(biomasses_1, attr).shape == (4, 3)

    # Check biomass values
    biomass_array = biomasses_1.elemental_masses
    assert_allclose(biomass_array[2:, :] / biomass_array[:2, :], np.ones((2, 3)) * 2)

    # Check cx ratios unaltered - all masses doubled in new cohorts.
    cx_ratios = biomasses_1.Cx_ratio
    assert_allclose(cx_ratios[2:, :], cx_ratios[:2, :])


def test_Biomasses_from_cohorts(fixture_biomass_components):
    """Test the default biomass generation."""
    from virtual_ecosystem.models.plants.biomasses_new import (
        Biomasses,
        FoliageBiomass,
        FruitBiomass,
        RootBiomass,
        SeedBiomass,
        StemBiomass,
    )

    cohorts, allometry, _, _ = fixture_biomass_components

    biomasses = Biomasses.from_cohorts(
        cohorts=cohorts,
        allometry=allometry,
        tissues=[FoliageBiomass, FruitBiomass, SeedBiomass, StemBiomass, RootBiomass],
    )

    for tissue_name, allom_attr in (
        ("foliage", "foliage_mass"),
        ("stem", "stem_mass"),
        ("root", "fine_root_mass"),
        ("fruit", "fruit_mass"),
        ("seed", "seed_mass"),
    ):
        tissue = biomasses.get_tissue(tissue_name)

        # Check the carbon biomasses are all populated correctly
        assert_allclose(
            tissue.elemental_masses[:, 0],
            getattr(allometry, allom_attr),
        )

        # Check the element masses are at the ideal ratios
        # for elem in biomasses.elements:
        #     element = tissue.element_masses[elem]
        #     assert_allclose(
        #         element.actual_element_mass, tissue.carbon_mass / element.ideal_ratio
        #     )


def test_total_element_mass_and_deficit(fixture_biomasses):
    """Test the total element mass and deficit calculations in StemStoichiometry."""

    # Get the outputs from the two methods
    calculated_element_masses = fixture_biomasses.total_element_masses
    calculated_element_deficits = fixture_biomasses.tissue_deficit

    for elem in fixture_biomasses.elements:
        # total element = sum across tissues
        masses = [
            t.element_masses[elem].actual_element_mass
            for t in fixture_biomasses.tissues
        ]

        assert_allclose(calculated_element_masses[elem], np.add.reduce(masses))

        # total deficit = sum ideal - actual across tissues.
        deficit = [
            (t.carbon_mass / t.element_masses[elem].ideal_ratio)
            - t.element_masses[elem].actual_element_mass
            for t in fixture_biomasses.tissues
        ]

        assert_allclose(calculated_element_deficits[elem], np.add.reduce(deficit))


def test_apply_growth_updates_element_masses_and_surplus(
    fixture_community,
    fixture_biomasses,
    fixture_stem_allocation,
    fixture_growth_increments,
):
    """Test that accounting for growth updates element masses and surplus correctly."""

    before = [t.as_array() for t in fixture_biomasses.tissues]

    fixture_biomasses.apply_growth(growth_increments=fixture_growth_increments)
    after = [t.as_array() for t in fixture_biomasses.tissues]

    # Each tissue should increase by element_needed_for_growth and the total surplus
    # should decrease accordingly
    expected_surplus = np.zeros(
        (
            len(fixture_community.cohorts),
            len(fixture_biomasses.elements),
        )
    )

    for b, a, t in zip(before, after, fixture_biomasses.tissues):
        # Test tissue increase
        needed = t.apply_growth(growth_increments=fixture_growth_increments)
        needed_array = np.stack(list(needed.values()))
        expected = b + needed_array
        assert_allclose(a, expected)

        # Accumulate decrease in surplus
        expected_surplus -= needed_array

    # Test accumulated surplus decrease
    assert_allclose(
        np.stack(list(fixture_biomasses.element_surplus.values())), expected_surplus
    )


def test_apply_turnover(fixture_community, fixture_biomasses, fixture_stem_allocation):
    """Test apply_turnover function in Biomasses."""

    # Check surplus is zero going in
    expected_surplus = {
        el: np.zeros(len(fixture_community.cohorts))
        for el in fixture_biomasses.elements
    }

    for el in fixture_biomasses.elements:
        assert_allclose(fixture_biomasses.element_surplus[el], expected_surplus[el])

    # Apply the turnover
    turnover = fixture_biomasses.apply_turnover(fixture_stem_allocation)

    # Calculate expectations from tissues
    for t in fixture_biomasses.tissues:
        tissue_turnover = t.get_turnover(fixture_stem_allocation)
        for idx, el in enumerate(fixture_biomasses.elements):
            expected_surplus[el] -= tissue_turnover[el]
            # Check the return values match up (not currently checking C here in
            # row zero)
            assert_allclose(tissue_turnover[el], turnover[t.tissue_name][idx + 1])

    # Check surplus matches
    for el in fixture_biomasses.elements:
        assert_allclose(fixture_biomasses.element_surplus[el], expected_surplus[el])


BALANCE_FOLIAGE_C = np.array([100.0, 200.0, 300.0, 400.0])
BALANCE_FOLIAGE_CN = np.repeat([5], 4)
BALANCE_FOLIAGE_CP = np.repeat([10], 4)
BALANCE_WOOD_C = np.array([200.0, 400.0, 600.0, 800.0])
BALANCE_WOOD_CN = np.repeat([10], 4)
BALANCE_WOOD_CP = np.repeat([20], 4)
BALANCE_POOL_SHAPE = (2, 4)


@pytest.fixture
def fixture_balance_elements_test_cases(which):
    """Fixture to return a test case for the balance_elements method.

    If which is a single integer, it provides the single test case that simulates a
    particular behaviour across 4 cohorts. If a list of integers is passed to which then
    the selected cases are combined to check that the method functions when handling
    mixed conditions.


    The return value is a tuple of six arrays providing data to populate a Biomass
    object with two tissues (foliage and wood) for two elements (N,P):

        initial_foliage: A 2 x N array of initial NP masses for foliage.
        initial_wood: The same for wood
        initial_pool: A 2 x N of the current biomass surplus pools for NP
        expected_foliage: The expected foliage tissue level masses after balancing
        expected_wood: The same for wood
        expected_pool: The expected biomass surplus pools after balancing.
    """
    test_cases = [
        (  # [0] T ideal, P empty --> no change
            np.array(
                [
                    BALANCE_FOLIAGE_C / BALANCE_FOLIAGE_CN,
                    BALANCE_FOLIAGE_C / BALANCE_FOLIAGE_CP,
                ]
            ),
            np.array(
                [
                    BALANCE_WOOD_C / BALANCE_WOOD_CN,
                    BALANCE_WOOD_C / BALANCE_WOOD_CP,
                ]
            ),
            np.zeros(BALANCE_POOL_SHAPE, dtype=float),
            np.array(
                [
                    BALANCE_FOLIAGE_C / BALANCE_FOLIAGE_CN,
                    BALANCE_FOLIAGE_C / BALANCE_FOLIAGE_CP,
                ]
            ),
            np.array(
                [
                    BALANCE_WOOD_C / BALANCE_WOOD_CN,
                    BALANCE_WOOD_C / BALANCE_WOOD_CP,
                ]
            ),
            np.zeros(BALANCE_POOL_SHAPE, dtype=float),
        ),
        (  # [1] T deficit, P empty --> no change
            np.array(
                [
                    BALANCE_FOLIAGE_C / BALANCE_FOLIAGE_CN,
                    BALANCE_FOLIAGE_C / BALANCE_FOLIAGE_CP,
                ]
            )
            - 5,
            np.array(
                [
                    BALANCE_WOOD_C / BALANCE_WOOD_CN,
                    BALANCE_WOOD_C / BALANCE_WOOD_CP,
                ]
            )
            - 5,
            np.zeros(BALANCE_POOL_SHAPE, dtype=float),
            np.array(
                [
                    BALANCE_FOLIAGE_C / BALANCE_FOLIAGE_CN,
                    BALANCE_FOLIAGE_C / BALANCE_FOLIAGE_CP,
                ]
            )
            - 5,
            np.array(
                [
                    BALANCE_WOOD_C / BALANCE_WOOD_CN,
                    BALANCE_WOOD_C / BALANCE_WOOD_CP,
                ]
            )
            - 5,
            np.zeros(BALANCE_POOL_SHAPE, dtype=float),
        ),
        (  # [2] T deficit, P exact surplus --> T filled, P empty
            np.array(
                [
                    BALANCE_FOLIAGE_C / BALANCE_FOLIAGE_CN,
                    BALANCE_FOLIAGE_C / BALANCE_FOLIAGE_CP,
                ]
            )
            - 5,
            np.array(
                [
                    BALANCE_WOOD_C / BALANCE_WOOD_CN,
                    BALANCE_WOOD_C / BALANCE_WOOD_CP,
                ]
            )
            - 5,
            np.full(BALANCE_POOL_SHAPE, 10, dtype=float),
            np.array(
                [
                    BALANCE_FOLIAGE_C / BALANCE_FOLIAGE_CN,
                    BALANCE_FOLIAGE_C / BALANCE_FOLIAGE_CP,
                ]
            ),
            np.array(
                [
                    BALANCE_WOOD_C / BALANCE_WOOD_CN,
                    BALANCE_WOOD_C / BALANCE_WOOD_CP,
                ]
            ),
            np.zeros(BALANCE_POOL_SHAPE, dtype=float),
        ),
        (  # [3] T deficit, P slight surplus --> T part filled, P empty
            np.array(
                [
                    BALANCE_FOLIAGE_C / BALANCE_FOLIAGE_CN,
                    BALANCE_FOLIAGE_C / BALANCE_FOLIAGE_CP,
                ]
            )
            - 5,
            np.array(
                [
                    BALANCE_WOOD_C / BALANCE_WOOD_CN,
                    BALANCE_WOOD_C / BALANCE_WOOD_CP,
                ]
            )
            - 5,
            np.full(BALANCE_POOL_SHAPE, 6, dtype=float),
            np.array(
                [
                    BALANCE_FOLIAGE_C / BALANCE_FOLIAGE_CN,
                    BALANCE_FOLIAGE_C / BALANCE_FOLIAGE_CP,
                ]
            )
            - 2,
            np.array(
                [
                    BALANCE_WOOD_C / BALANCE_WOOD_CN,
                    BALANCE_WOOD_C / BALANCE_WOOD_CP,
                ]
            )
            - 2,
            np.zeros(BALANCE_POOL_SHAPE, dtype=float),
        ),
        (  # [4] T deficit, P over surplus --> T filled, P not empty
            np.array(
                [
                    BALANCE_FOLIAGE_C / BALANCE_FOLIAGE_CN,
                    BALANCE_FOLIAGE_C / BALANCE_FOLIAGE_CP,
                ]
            )
            - 5,
            np.array(
                [
                    BALANCE_WOOD_C / BALANCE_WOOD_CN,
                    BALANCE_WOOD_C / BALANCE_WOOD_CP,
                ]
            )
            - 5,
            np.full(BALANCE_POOL_SHAPE, 16, dtype=float),
            np.array(
                [
                    BALANCE_FOLIAGE_C / BALANCE_FOLIAGE_CN,
                    BALANCE_FOLIAGE_C / BALANCE_FOLIAGE_CP,
                ]
            ),
            np.array(
                [
                    BALANCE_WOOD_C / BALANCE_WOOD_CN,
                    BALANCE_WOOD_C / BALANCE_WOOD_CP,
                ]
            ),
            np.full(BALANCE_POOL_SHAPE, 6, dtype=float),
        ),
        (  # [5] T ideal, P small deficit --> T deficit, P empty
            np.array(
                [
                    BALANCE_FOLIAGE_C / BALANCE_FOLIAGE_CN,
                    BALANCE_FOLIAGE_C / BALANCE_FOLIAGE_CP,
                ]
            ),
            np.array(
                [
                    BALANCE_WOOD_C / BALANCE_WOOD_CN,
                    BALANCE_WOOD_C / BALANCE_WOOD_CP,
                ]
            ),
            np.full(BALANCE_POOL_SHAPE, -10, dtype=float),
            np.array(
                [
                    BALANCE_FOLIAGE_C / BALANCE_FOLIAGE_CN,
                    BALANCE_FOLIAGE_C / BALANCE_FOLIAGE_CP,
                ]
            )
            - 5,
            np.array(
                [
                    BALANCE_WOOD_C / BALANCE_WOOD_CN,
                    BALANCE_WOOD_C / BALANCE_WOOD_CP,
                ]
            )
            - 5,
            np.zeros(BALANCE_POOL_SHAPE, dtype=float),
        ),
        (  # [6] T ideal, P exact deficit --> T zero, P empty
            np.array(
                [
                    BALANCE_FOLIAGE_C / BALANCE_FOLIAGE_CN,
                    BALANCE_FOLIAGE_C / BALANCE_FOLIAGE_CP,
                ]
            ),
            np.array(
                [
                    BALANCE_WOOD_C / BALANCE_WOOD_CN,
                    BALANCE_WOOD_C / BALANCE_WOOD_CP,
                ]
            ),
            -np.array(
                [
                    BALANCE_FOLIAGE_C / BALANCE_FOLIAGE_CN
                    + BALANCE_WOOD_C / BALANCE_WOOD_CN,
                    BALANCE_FOLIAGE_C / BALANCE_FOLIAGE_CP
                    + BALANCE_WOOD_C / BALANCE_WOOD_CP,
                ],
            ),
            np.zeros(BALANCE_POOL_SHAPE, dtype=float),
            np.zeros(BALANCE_POOL_SHAPE, dtype=float),
            np.zeros(BALANCE_POOL_SHAPE, dtype=float),
        ),
        (  # [7] T ideal, P over deficit --> T zero, P not empty
            np.array(
                [
                    BALANCE_FOLIAGE_C / BALANCE_FOLIAGE_CN,
                    BALANCE_FOLIAGE_C / BALANCE_FOLIAGE_CP,
                ]
            ),
            np.array(
                [
                    BALANCE_WOOD_C / BALANCE_WOOD_CN,
                    BALANCE_WOOD_C / BALANCE_WOOD_CP,
                ]
            ),
            -2
            * np.array(
                [
                    BALANCE_FOLIAGE_C / BALANCE_FOLIAGE_CN
                    + BALANCE_WOOD_C / BALANCE_WOOD_CN,
                    BALANCE_FOLIAGE_C / BALANCE_FOLIAGE_CP
                    + BALANCE_WOOD_C / BALANCE_WOOD_CP,
                ],
            ),
            np.zeros(BALANCE_POOL_SHAPE, dtype=float),
            np.zeros(BALANCE_POOL_SHAPE, dtype=float),
            -1
            * np.array(
                [
                    BALANCE_FOLIAGE_C / BALANCE_FOLIAGE_CN
                    + BALANCE_WOOD_C / BALANCE_WOOD_CN,
                    BALANCE_FOLIAGE_C / BALANCE_FOLIAGE_CP
                    + BALANCE_WOOD_C / BALANCE_WOOD_CP,
                ],
            ),
        ),
    ]

    if isinstance(which, int):
        return test_cases[which]

    # Concatenate the selected inputs and return
    selected = [test_cases[w] for w in which]
    return [np.concatenate(params, axis=1) for params in zip(*selected)]


@pytest.mark.parametrize("which", (0, 1, 2, 3, 4, 5, 6, 7, [0, 1, 2, 3, 4, 5, 6, 7]))
def test_balance_elements(
    fixture_community, fixture_balance_elements_test_cases, which
):
    """Test the balancing of elements across tissues.

    The parameterisation passes the 'which' argument to the
    fixture_balance_elements_test_cases fixture, which uses which to return either one
    of or a combination of test cases. This is largely a trick to define individual
    tests of particular behaviour and then easily combine those individual cases into a
    test that the method handles a mixture of scenarios across cohorts.
    """

    from virtual_ecosystem.models.plants.biomasses import (
        Biomasses,
        Element,
        FoliageBiomass,
        StemBiomass,
    )

    # Unpack the inputs from the fixture
    (
        initial_foliage,
        initial_wood,
        initial_pool,
        expected_foliage,
        expected_wood,
        expected_pool,
    ) = fixture_balance_elements_test_cases

    n_cases = 1 if isinstance(which, int) else len(which)

    # Turnover not relevant to this test
    turnover_ratios = np.repeat(np.nan, n_cases)

    foliage = FoliageBiomass(
        community=fixture_community,
        # Note that this only has two cohorts
        # - not sure BiomassTissue will retain community as an argument.
        carbon_mass=np.tile(BALANCE_FOLIAGE_C, n_cases),
        element_masses={
            "N": Element(
                name="n",
                ideal_ratio=np.tile(BALANCE_FOLIAGE_CN, n_cases),
                actual_element_mass=initial_foliage[0],
                turnover_ratio=turnover_ratios,
            ),
            "P": Element(
                name="p",
                ideal_ratio=np.tile(BALANCE_FOLIAGE_CP, n_cases),
                actual_element_mass=initial_foliage[1],
                turnover_ratio=turnover_ratios,
            ),
        },
    )

    wood = StemBiomass(
        community=fixture_community,
        carbon_mass=np.tile(BALANCE_WOOD_C, n_cases),
        element_masses={
            "N": Element(
                name="n",
                ideal_ratio=np.tile(BALANCE_WOOD_CN, n_cases),
                actual_element_mass=initial_wood[0],
                turnover_ratio=turnover_ratios,
            ),
            "P": Element(
                name="p",
                ideal_ratio=np.tile(BALANCE_WOOD_CP, n_cases),
                actual_element_mass=initial_wood[1],
                turnover_ratio=turnover_ratios,
            ),
        },
    )

    biomasses = Biomasses(
        tissues=[foliage, wood],
        community=fixture_community,
    )

    # Set the element pools to balance
    biomasses.element_surplus = {
        ky: initial_pool[idx] for idx, ky in enumerate(biomasses.elements)
    }

    # Run the method.
    biomasses.balance_elements()

    # Check the expectations.
    foliage = biomasses.get_tissue("foliage").as_array()
    assert_allclose(foliage, expected_foliage)

    wood = biomasses.get_tissue("stem").as_array()
    assert_allclose(wood, expected_wood)

    pool = np.stack(list(biomasses.element_surplus.values()))
    assert_allclose(pool, expected_pool)


def test_add_elemental_masses_clips_negative_value(fixture_community, caplog):
    """Tiny floating-point negatives are clipped to zero after updates."""

    from virtual_ecosystem.models.plants.biomasses import Element, FoliageBiomass

    tissue = FoliageBiomass(
        community=fixture_community,
        carbon_mass=fixture_community.stem_allometry.foliage_mass.copy(),
        element_masses={
            "N": Element(
                name="n",
                ideal_ratio=np.array([5.0, 6.0]),
                actual_element_mass=np.array([1.0e-18, 20.0]),
                turnover_ratio=np.array([10.0, 12.0]),
            ),
            "P": Element(
                name="p",
                ideal_ratio=np.array([5.0, 6.0]),
                actual_element_mass=np.array([5.0, 20.0]),
                turnover_ratio=np.array([10.0, 12.0]),
            ),
        },
    )

    tissue.add_elemental_masses(
        {
            "N": np.array([-1.1e-18, 0.0]),
            "P": np.array([0.0, 0.0]),
        }
    )

    assert_allclose(tissue.element_masses["N"].actual_element_mass, [0.0, 20.0])
    assert "Clipping negative updated N biomass" in caplog.text
