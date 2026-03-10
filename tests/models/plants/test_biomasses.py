"""Tests for the plant stoichiometry module."""

from types import SimpleNamespace

import numpy as np
import pytest


@pytest.fixture
def fixture_community():
    """Provides a simple object with Community like structure."""

    class DummyCommunity:
        """Mock class for a plant community with two cohorts for testing."""

        def __init__(self):
            self.stem_allometry = SimpleNamespace(
                foliage_mass=np.array([50.0, 80.0]),
                stem_mass=np.array([100.0, 150.0]),
                reproductive_tissue_mass=np.array([20.0, 40.0]),
                fine_root_mass=np.array([10.0, 16.0]),
            )
            self.stem_traits = SimpleNamespace(
                zeta=0.1, sla=2.0, p_foliage_for_reproductive_tissue=0.5
            )

            self.n_cohorts = 2
            self.cohorts = type("Cohorts", (), {"pft_names": ["shrub", "broadleaf"]})

    return DummyCommunity()


@pytest.fixture
def fixture_stem_allocation():
    """Provides a simple object with StemAllocation like structure."""

    class DummyAllocation:
        """Mock class for allocation with predefined values for testing."""

        def __init__(self):
            self.delta_foliage_mass = np.array([20.0, 10.0])
            self.delta_stem_mass = np.array([10.0, 5.0])
            self.foliage_turnover = np.array([30.0, 15.0])
            self.reproductive_tissue_turnover = np.array([5.0, 2.0])
            self.fine_root_turnover = np.array([3.0, 1.5])

    return DummyAllocation()


ELEMENTS = ("N", "P")


@pytest.fixture
def fixture_biomasses(fixture_community):
    """Fixture providing a Biomasses instance."""

    from virtual_ecosystem.models.plants.biomasses import (
        Biomasses,
        Element,
        FoliageTissue,
        ReproductiveTissue,
        RootTissue,
        WoodTissue,
    )

    foliage = FoliageTissue(
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

    root = RootTissue(
        community=fixture_community,
        carbon_mass=fixture_community.stem_allometry.fine_root_mass.copy(),
        element_masses={
            "N": Element(
                name="n",
                ideal_ratio=np.array([5.0, 7.0]),
                actual_element_mass=np.array([10.0, 25.0]),
                turnover_ratio=np.array(
                    [5.0, 7.0]
                ),  # TODO - actually, this is misleading. It should be current Cx_ratio
            ),
            "P": Element(
                name="p",
                ideal_ratio=np.array([5.0, 7.0]),
                actual_element_mass=np.array([10.0, 25.0]),
                turnover_ratio=np.array([5.0, 7.0]),
            ),
        },
    )

    wood = WoodTissue(
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

    repro = ReproductiveTissue(
        community=fixture_community,
        carbon_mass=fixture_community.stem_allometry.reproductive_tissue_mass.copy(),
        element_masses={
            "N": Element(
                name="n",
                ideal_ratio=np.array([4.0, 5.0]),
                actual_element_mass=np.array([8.0, 12.0]),
                turnover_ratio=np.array(
                    [4.0, 5.0]
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
        extra_pft_traits=SimpleNamespace(),
    )


@pytest.mark.parametrize(
    argnames="tissue_name,mass_attribute",
    argvalues=(
        ("FoliageTissue", "foliage_mass"),
        ("RootTissue", "fine_root_mass"),
        ("WoodTissue", "stem_mass"),
        ("ReproductiveTissue", "reproductive_tissue_mass"),
    ),
)
def test_Tissue_from_pft_default_ratios(
    fixture_community, extra_pft_traits, tissue_name, mass_attribute
):
    """Test the default factory method generates a tissue with the correct masses."""

    import virtual_ecosystem.models.plants.biomasses as biomasses

    TissueClass = getattr(biomasses, tissue_name)

    tissue = TissueClass.from_pft_default_ratios(
        community=fixture_community,
        extra_pft_traits=extra_pft_traits,
        with_elements=ELEMENTS,
    )

    # Check carbon mass is equal to the appropriate mass attribute in the original
    # allometry.
    assert np.allclose(
        tissue.carbon_mass, getattr(fixture_community.stem_allometry, mass_attribute)
    )

    # Check that the generated element masses are at their ideal ratios.
    for ky in ELEMENTS:
        assert np.allclose(
            tissue.element_masses[ky].actual_element_mass,
            tissue.carbon_mass * (1 / tissue.element_masses[ky].ideal_ratio),
        )


# TODO - think about how to collapse these tests, like the one above. It will need to
#        capture the specific differences between tissues at turnover so might need a
#        switch/case at the end, but would remove a lot of overlap.


def test_FoliageTissue_functions(fixture_community, fixture_stem_allocation):
    """Test the FoliageTissue class functions."""

    from virtual_ecosystem.models.plants.biomasses import Element, FoliageTissue

    initial_element_masses = np.array([10.0, 20.0])
    # initial_foliage_mass = np.array([50.0, 80.0])
    # delta_foliage_mass = np.array([20.0, 10.0])
    # foliage_turnover = np.array([30.0, 15.0])
    ideal_ratio = np.array([5.0, 6.0])
    turnover_ratio = np.array([10.0, 12.0])

    tissue = FoliageTissue(
        community=fixture_community,
        carbon_mass=fixture_community.stem_allometry.foliage_mass.copy(),
        element_masses={
            "N": Element(
                name="n",
                ideal_ratio=ideal_ratio,
                actual_element_mass=initial_element_masses.copy(),
                turnover_ratio=turnover_ratio,
            ),
            "P": Element(
                name="p",
                ideal_ratio=ideal_ratio,
                actual_element_mass=initial_element_masses.copy(),
                turnover_ratio=turnover_ratio,
            ),
        },
    )

    # carbon mass = foliage mass
    assert np.allclose(
        tissue.carbon_mass, fixture_community.stem_allometry.foliage_mass
    )

    # deficit = element - (C / CN)
    expected_deficit = {
        ky: tissue.carbon_mass / elem.ideal_ratio - elem.actual_element_mass
        for ky, elem in tissue.element_masses.items()
    }

    calculated_deficits = tissue.deficit
    assert calculated_deficits.keys() == expected_deficit.keys()
    for ky in calculated_deficits:
        assert np.allclose(calculated_deficits[ky], expected_deficit[ky])

    # Cx ratio = C / element
    expected_cx = {
        ky: tissue.carbon_mass / elem.actual_element_mass
        for ky, elem in tissue.element_masses.items()
    }

    calculated_cx = tissue.Cx_ratio
    assert calculated_cx.keys() == expected_cx.keys()
    for ky in calculated_cx:
        assert np.allclose(tissue.Cx_ratio[ky], expected_cx[ky])

    # growth = ΔC / CN
    expected_growth = {
        ky: fixture_stem_allocation.delta_foliage_mass / elem.ideal_ratio
        for ky, elem in tissue.element_masses.items()
    }

    calculated_growth = tissue.elements_needed_for_growth(fixture_stem_allocation)
    assert calculated_growth.keys() == expected_growth.keys()
    for ky in calculated_growth:
        assert np.allclose(calculated_growth[ky], expected_growth[ky])

    # turnover = turnover * (1 / turnover Cx)
    # NOTE - TISSUE SPECIFIC DIFFERENCE - turnover tissue uses turnover Cx not
    #        current Cx
    expected_turnover = {
        ky: fixture_stem_allocation.foliage_turnover / elem.turnover_ratio
        for ky, elem in tissue.element_masses.items()
    }

    calculated_turnover = tissue.tissue_turnover(fixture_stem_allocation)
    assert calculated_turnover.keys() == expected_turnover.keys()
    for ky in calculated_turnover:
        assert np.allclose(calculated_turnover[ky], expected_turnover[ky])

    # Extract turnover
    extracted_turnover = tissue.extract_turnover(fixture_stem_allocation)

    # Check tissue masses have been decreased
    assert np.allclose(
        tissue.carbon_mass,
        fixture_community.stem_allometry.foliage_mass
        - fixture_stem_allocation.foliage_turnover,
    )

    for ky in calculated_turnover:
        assert np.allclose(
            tissue.element_masses[ky].actual_element_mass,
            initial_element_masses - expected_turnover[ky],
        )

    # Check returned elemental masses
    expected_turnover["C"] = fixture_stem_allocation.foliage_turnover
    assert expected_turnover.keys() == extracted_turnover.keys()
    for ky in extracted_turnover:
        assert np.allclose(
            expected_turnover[ky],
            extracted_turnover[ky],
        )

    # Foliage specific checks
    # - the turnover Cx ratios match the expected turnover ratios
    for ky, values in calculated_turnover.items():
        assert np.allclose(
            fixture_stem_allocation.foliage_turnover / values,
            tissue.element_masses[ky].turnover_ratio,
        )

    # - The remaining tissue will be relatively enriched (smaller Cx ratios) compared to
    #   the pre-turnover Cx ratios.
    #   50/10, 80/20  --> 30/3, 15/1.25 + 20/7, 65/18.75
    for ky, values in tissue.Cx_ratio.items():
        assert np.all(np.less(values, calculated_cx[ky]))


def test_RootTissue_functions(fixture_community, fixture_stem_allocation):
    """Test the RootTissue class functions."""

    from virtual_ecosystem.models.plants.biomasses import Element, RootTissue

    initial_element_masses = np.array([10.0, 20.0])
    # initial_foliage_mass = np.array([50.0, 80.0])
    # delta_foliage_mass = np.array([20.0, 10.0])
    # foliage_turnover = np.array([30.0, 15.0])
    ideal_ratio = np.array([5.0, 6.0])
    turnover_ratio = ideal_ratio

    tissue = RootTissue(
        community=fixture_community,
        carbon_mass=fixture_community.stem_allometry.fine_root_mass.copy(),
        element_masses={
            "N": Element(
                name="n",
                ideal_ratio=ideal_ratio,
                actual_element_mass=initial_element_masses.copy(),
                turnover_ratio=turnover_ratio,
            ),
            "P": Element(
                name="p",
                ideal_ratio=ideal_ratio,
                actual_element_mass=initial_element_masses.copy(),
                turnover_ratio=turnover_ratio,
            ),
        },
    )

    # carbon mass = fine root mass
    assert np.allclose(
        tissue.carbon_mass, fixture_community.stem_allometry.fine_root_mass
    )

    # deficit = element - (C / CN)
    expected_deficit = {
        ky: tissue.carbon_mass / elem.ideal_ratio - elem.actual_element_mass
        for ky, elem in tissue.element_masses.items()
    }

    calculated_deficits = tissue.deficit
    assert calculated_deficits.keys() == expected_deficit.keys()
    for ky in calculated_deficits:
        assert np.allclose(calculated_deficits[ky], expected_deficit[ky])

    # Cx ratio = C / element
    expected_cx = {
        ky: tissue.carbon_mass / elem.actual_element_mass
        for ky, elem in tissue.element_masses.items()
    }

    calculated_cx = tissue.Cx_ratio
    assert calculated_cx.keys() == expected_cx.keys()
    for ky in calculated_cx:
        assert np.allclose(tissue.Cx_ratio[ky], expected_cx[ky])

    # growth = ΔC / CN
    expected_growth = {
        ky: (
            fixture_stem_allocation.delta_foliage_mass
            * fixture_community.stem_traits.zeta
            * fixture_community.stem_traits.sla
        )
        / elem.ideal_ratio
        for ky, elem in tissue.element_masses.items()
    }

    calculated_growth = tissue.elements_needed_for_growth(fixture_stem_allocation)
    assert calculated_growth.keys() == expected_growth.keys()
    for ky in calculated_growth:
        assert np.allclose(calculated_growth[ky], expected_growth[ky])

    # turnover = turnover * (1 / actual Cx ratio)
    ### NOTE TISSUE SPECIFIC DIFFERENCE - turnover tissue just has the _current_ ratios
    expected_turnover = {
        ky: fixture_stem_allocation.fine_root_turnover / expected_cx[ky]
        for ky, elem in tissue.element_masses.items()
    }

    calculated_turnover = tissue.tissue_turnover(fixture_stem_allocation)
    assert calculated_turnover.keys() == expected_turnover.keys()
    for ky in calculated_turnover:
        assert np.allclose(calculated_turnover[ky], expected_turnover[ky])

    # Extract turnover
    extracted_turnover = tissue.extract_turnover(fixture_stem_allocation)

    # Check tissue masses have been decreased
    assert np.allclose(
        tissue.carbon_mass,
        fixture_community.stem_allometry.fine_root_mass
        - fixture_stem_allocation.fine_root_turnover,
    )

    for ky in calculated_turnover:
        assert np.allclose(
            tissue.element_masses[ky].actual_element_mass,
            initial_element_masses - expected_turnover[ky],
        )

    # Check returned elemental masses
    expected_turnover["C"] = fixture_stem_allocation.fine_root_turnover
    assert expected_turnover.keys() == extracted_turnover.keys()
    for ky in extracted_turnover:
        assert np.allclose(
            expected_turnover[ky],
            extracted_turnover[ky],
        )

    # Root specific checks
    # - Original Cx ratios maintained in remaining tissue after turnover.
    new_cx_ratios = tissue.Cx_ratio
    for ky, new_ratio in new_cx_ratios.items():
        assert np.allclose(new_ratio, calculated_cx[ky])


def test_ReproductiveTissue_functions(fixture_community, fixture_stem_allocation):
    """Test the ReproductiveTissue class functions."""

    from virtual_ecosystem.models.plants.biomasses import Element, ReproductiveTissue

    initial_element_masses = np.array([10.0, 20.0])
    # initial_foliage_mass = np.array([50.0, 80.0])
    # delta_foliage_mass = np.array([20.0, 10.0])
    # foliage_turnover = np.array([30.0, 15.0])
    ideal_ratio = np.array([5.0, 6.0])
    turnover_ratio = ideal_ratio

    tissue = ReproductiveTissue(
        community=fixture_community,
        carbon_mass=fixture_community.stem_allometry.reproductive_tissue_mass.copy(),
        element_masses={
            "N": Element(
                name="n",
                ideal_ratio=ideal_ratio,
                actual_element_mass=initial_element_masses.copy(),
                turnover_ratio=turnover_ratio,
            ),
            "P": Element(
                name="p",
                ideal_ratio=ideal_ratio,
                actual_element_mass=initial_element_masses.copy(),
                turnover_ratio=turnover_ratio,
            ),
        },
    )

    # carbon mass = reproductive tissuemass
    assert np.allclose(
        tissue.carbon_mass, fixture_community.stem_allometry.reproductive_tissue_mass
    )

    # deficit = element - (C / CN)
    expected_deficit = {
        ky: tissue.carbon_mass / elem.ideal_ratio - elem.actual_element_mass
        for ky, elem in tissue.element_masses.items()
    }

    calculated_deficits = tissue.deficit
    assert calculated_deficits.keys() == expected_deficit.keys()
    for ky in calculated_deficits:
        assert np.allclose(calculated_deficits[ky], expected_deficit[ky])

    # Cx ratio = C / element
    expected_cx = {
        ky: tissue.carbon_mass / elem.actual_element_mass
        for ky, elem in tissue.element_masses.items()
    }

    calculated_cx = tissue.Cx_ratio
    assert calculated_cx.keys() == expected_cx.keys()
    for ky in calculated_cx:
        assert np.allclose(tissue.Cx_ratio[ky], expected_cx[ky])

    # growth = ΔC / CN
    expected_growth = {
        ky: (
            fixture_stem_allocation.delta_foliage_mass
            * fixture_community.stem_traits.p_foliage_for_reproductive_tissue
        )
        / elem.ideal_ratio
        for ky, elem in tissue.element_masses.items()
    }

    calculated_growth = tissue.elements_needed_for_growth(fixture_stem_allocation)
    assert calculated_growth.keys() == expected_growth.keys()
    for ky in calculated_growth:
        assert np.allclose(calculated_growth[ky], expected_growth[ky])

    # turnover = turnover * (1 / actual Cx ratio)
    ### NOTE TISSUE SPECIFIC DIFFERENCE - turnover tissue just has the _current_ ratios
    expected_turnover = {
        ky: fixture_stem_allocation.reproductive_tissue_turnover / expected_cx[ky]
        for ky, elem in tissue.element_masses.items()
    }

    calculated_turnover = tissue.tissue_turnover(fixture_stem_allocation)
    assert calculated_turnover.keys() == expected_turnover.keys()
    for ky in calculated_turnover:
        assert np.allclose(calculated_turnover[ky], expected_turnover[ky])

    # Extract turnover
    extracted_turnover = tissue.extract_turnover(fixture_stem_allocation)

    # Check tissue masses have been decreased
    assert np.allclose(
        tissue.carbon_mass,
        fixture_community.stem_allometry.reproductive_tissue_mass
        - fixture_stem_allocation.reproductive_tissue_turnover,
    )

    for ky in calculated_turnover:
        assert np.allclose(
            tissue.element_masses[ky].actual_element_mass,
            initial_element_masses - expected_turnover[ky],
        )

    # Check returned elemental masses
    expected_turnover["C"] = fixture_stem_allocation.reproductive_tissue_turnover
    assert expected_turnover.keys() == extracted_turnover.keys()
    for ky in extracted_turnover:
        assert np.allclose(
            expected_turnover[ky],
            extracted_turnover[ky],
        )

    # Root specific checks
    # - Original Cx ratios maintained in remaining tissue after turnover.
    new_cx_ratios = tissue.Cx_ratio
    for ky, new_ratio in new_cx_ratios.items():
        assert np.allclose(new_ratio, calculated_cx[ky])


def test_WoodTissue_functions(fixture_community, fixture_stem_allocation):
    """Test the WoodTissue class functions."""

    from virtual_ecosystem.models.plants.biomasses import Element, WoodTissue

    initial_element_masses = np.array([10.0, 20.0])
    # initial_foliage_mass = np.array([50.0, 80.0])
    # delta_foliage_mass = np.array([20.0, 10.0])
    # foliage_turnover = np.array([30.0, 15.0])
    ideal_ratio = np.array([5.0, 6.0])
    turnover_ratio = ideal_ratio

    tissue = WoodTissue(
        community=fixture_community,
        carbon_mass=fixture_community.stem_allometry.stem_mass.copy(),
        element_masses={
            "N": Element(
                name="n",
                ideal_ratio=ideal_ratio,
                actual_element_mass=initial_element_masses.copy(),
                turnover_ratio=turnover_ratio,
            ),
            "P": Element(
                name="p",
                ideal_ratio=ideal_ratio,
                actual_element_mass=initial_element_masses.copy(),
                turnover_ratio=turnover_ratio,
            ),
        },
    )

    # carbon mass = stem mass
    assert np.allclose(tissue.carbon_mass, fixture_community.stem_allometry.stem_mass)

    # deficit = element - (C / CN)
    expected_deficit = {
        ky: tissue.carbon_mass / elem.ideal_ratio - elem.actual_element_mass
        for ky, elem in tissue.element_masses.items()
    }

    calculated_deficits = tissue.deficit
    assert calculated_deficits.keys() == expected_deficit.keys()
    for ky in calculated_deficits:
        assert np.allclose(calculated_deficits[ky], expected_deficit[ky])

    # Cx ratio = C / element
    expected_cx = {
        ky: tissue.carbon_mass / elem.actual_element_mass
        for ky, elem in tissue.element_masses.items()
    }

    calculated_cx = tissue.Cx_ratio
    assert calculated_cx.keys() == expected_cx.keys()
    for ky in calculated_cx:
        assert np.allclose(tissue.Cx_ratio[ky], expected_cx[ky])

    # growth = ΔC / CN
    expected_growth = {
        ky: fixture_stem_allocation.delta_stem_mass / elem.ideal_ratio
        for ky, elem in tissue.element_masses.items()
    }

    calculated_growth = tissue.elements_needed_for_growth(fixture_stem_allocation)
    assert calculated_growth.keys() == expected_growth.keys()
    for ky in calculated_growth:
        assert np.allclose(calculated_growth[ky], expected_growth[ky])

    # turnover = zero
    ### NOTE TISSUE SPECIFIC DIFFERENCE - turnover tissue just has the _current_ ratios
    expected_turnover = {
        ky: np.zeros_like(expected_cx[ky]) for ky, elem in tissue.element_masses.items()
    }

    calculated_turnover = tissue.tissue_turnover(fixture_stem_allocation)
    assert calculated_turnover.keys() == expected_turnover.keys()
    for ky in calculated_turnover:
        assert np.allclose(calculated_turnover[ky], expected_turnover[ky])

    # Extract turnover
    extracted_turnover = tissue.extract_turnover(fixture_stem_allocation)

    # Check tissue masses has not been decreased
    ### NOTE TISSUE SPECIFIC DIFFERENCE -
    assert np.allclose(
        tissue.carbon_mass,
        fixture_community.stem_allometry.stem_mass,
    )

    for ky in calculated_turnover:
        assert np.allclose(
            tissue.element_masses[ky].actual_element_mass,
            initial_element_masses,
        )

    # Check returned elemental masses
    expected_turnover["C"] = np.zeros_like(fixture_community.stem_allometry.stem_mass)
    assert expected_turnover.keys() == extracted_turnover.keys()
    for ky in extracted_turnover:
        assert np.allclose(
            expected_turnover[ky],
            extracted_turnover[ky],
        )


def test_Biomasses_from_community(fixture_community, extra_pft_traits):
    """Test the default biomass generation."""
    from virtual_ecosystem.models.plants.biomasses import (
        Biomasses,
        FoliageTissue,
        ReproductiveTissue,
        RootTissue,
        WoodTissue,
    )

    biomasses = Biomasses.default_init(
        community=fixture_community,
        extra_pft_traits=extra_pft_traits,
        with_elements=["N", "P"],
        tissues=[FoliageTissue, ReproductiveTissue, WoodTissue, RootTissue],
    )

    # Check the biomasses are all populated correctly
    for tissue_name, allom_attr in (
        ("foliage", "foliage_mass"),
        ("wood", "stem_mass"),
        ("reproductive", "reproductive_tissue_mass"),
        ("root", "fine_root_mass"),
    ):
        assert np.allclose(
            biomasses.get_tissue(tissue_name).carbon_mass,
            getattr(fixture_community.stem_allometry, allom_attr),
        )

    # Check the biomasses are all populated correctly and the element masses are at the
    # ideal ratios
    for tissue_name, allom_attr in (
        ("foliage", "foliage_mass"),
        ("wood", "stem_mass"),
        ("reproductive", "reproductive_tissue_mass"),
        ("root", "fine_root_mass"),
    ):
        tissue = biomasses.get_tissue(tissue_name)

        assert np.allclose(
            tissue.carbon_mass,
            getattr(fixture_community.stem_allometry, allom_attr),
        )

        for elem in biomasses.elements:
            element = tissue.element_masses[elem]
            assert np.allclose(
                element.actual_element_mass, tissue.carbon_mass / element.ideal_ratio
            )


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

        assert np.allclose(calculated_element_masses[elem], np.add.reduce(masses))

        # total deficit = sum ideal - actual across tissues.
        deficit = [
            (t.carbon_mass / t.element_masses[elem].ideal_ratio)
            - t.element_masses[elem].actual_element_mass
            for t in fixture_biomasses.tissues
        ]

        assert np.allclose(calculated_element_deficits[elem], np.add.reduce(deficit))


def test_account_for_growth_updates_element_masses_and_surplus(
    fixture_community, fixture_biomasses, fixture_stem_allocation
):
    """Test that accounting for growth updates element masses and surplus correctly."""

    before = [t.as_array() for t in fixture_biomasses.tissues]

    fixture_biomasses.account_for_growth(fixture_stem_allocation)
    after = [t.as_array() for t in fixture_biomasses.tissues]

    # Each tissue should increase by element_needed_for_growth and the total surplus
    # should decrease accordingly
    expected_surplus = np.zeros(
        (fixture_community.n_cohorts, len(fixture_biomasses.elements))
    )

    for b, a, t in zip(before, after, fixture_biomasses.tissues):
        # Test tissue increase
        needed = t.elements_needed_for_growth(fixture_stem_allocation)
        needed_array = np.stack(list(needed.values()))
        expected = b + needed_array
        assert np.allclose(a, expected)

        # Accumulate decrease in surplus
        expected_surplus -= needed_array

    # Test accumulated surplus decrease
    assert np.allclose(
        np.stack(list(fixture_biomasses.element_surplus.values())), expected_surplus
    )


# def test_account_for_element_loss_turnover(stem_stoichiometry):
#     """Test account for element loss function in StemStoichiometry."""

#     stem_stoichiometry.account_for_element_loss_turnover(DUMMY_ALLOC)

#     expected = np.zeros(DUMMY_COMMUNITY.n_cohorts)
#     for t in stem_stoichiometry.tissues:
#         expected -= t.element_turnover(DUMMY_ALLOC)

#     assert np.allclose(stem_stoichiometry.element_surplus, expected)


# def test_distribute_deficit(stem_stoichiometry):
#     """Test the distribution of a negative element surplus (deficit) across
#     tissues."""

#     cohort = 0

#     # Set actual element masses to full ideal values
#     for tissue in stem_stoichiometry.tissues:
#         tissue.actual_element_mass[cohort] = (
#             tissue.carbon_mass[cohort] / tissue.ideal_ratio[cohort]
#         )

#     # Introduce a deficit in element surplus (negative value)
#     deficit_to_distribute = (
#         -0.4 * stem_stoichiometry.total_element_mass[cohort]
#     )  # 40% deficit
#     stem_stoichiometry.element_surplus[cohort] = deficit_to_distribute

#     # Record actual masses before distribution
#     before = np.array(
#         [t.actual_element_mass[cohort] for t in stem_stoichiometry.tissues]
#     )

#     # Compute shares based on initial actual masses
#     initial_masses = before.copy()
#     total_mass = initial_masses.sum()
#     expected_losses = initial_masses / total_mass * -deficit_to_distribute

#     # Distribute the deficit
#     stem_stoichiometry.distribute_deficit(cohort)

#     # Record actual masses after distribution
#     after = np.array(
#         [t.actual_element_mass[cohort] for t in stem_stoichiometry.tissues]
#     )
#     total_loss = before.sum() - after.sum()

#     # Assertions
#     assert np.all(after < before), "Each tissue should have decreased"
#     assert stem_stoichiometry.element_surplus[cohort] == 0.0, (
#         "Deficit should be fully distributed"
#     )
#     assert np.allclose(before - after, expected_losses, rtol=1e-12, atol=1e-12), (
#         "Losses should match expected proportional distribution"
#     )
#     assert np.isclose(total_loss, -deficit_to_distribute, rtol=1e-12, atol=1e-12), (
#         "Total loss should match the distributed deficit"
#     )


# def test_distribute_partial_surplus(stem_stoichiometry):
#     """Test distribution of a partial surplus across tissues with deficits."""

#     cohort = 0

#     # Set actual element masses to 50% of ideal to guarantee a positive deficit
#     for tissue in stem_stoichiometry.tissues:
#         ideal_mass = tissue.carbon_mass[cohort] / tissue.ideal_ratio[cohort]
#         tissue.actual_element_mass[cohort] = 0.5 * ideal_mass

#     # Compute total deficit and partial surplus
#     total_deficit = stem_stoichiometry.tissue_deficit[cohort]
#     partial_surplus = total_deficit * 0.4
#     stem_stoichiometry.element_surplus[cohort] = partial_surplus

#     # Record actual masses before distribution
#     before = np.array(
#         [t.actual_element_mass[cohort] for t in stem_stoichiometry.tissues]
#     )
#     ideals = np.array(
#         [
#             t.carbon_mass[cohort] / t.ideal_ratio[cohort]
#             for t in stem_stoichiometry.tissues
#         ]
#     )

#     # Distribute the partial surplus
#     stem_stoichiometry.distribute_surplus(cohort)

#     # Record actual masses after distribution
#     after = np.array(
#         [t.actual_element_mass[cohort] for t in stem_stoichiometry.tissues]
#     )
#     total_gain = after.sum() - before.sum()

#     # Assertions
#     assert np.all(after > before), "Each tissue should have increased"
#     assert np.all(after <= ideals + 1e-12), "No tissue should exceed its ideal mass"
#     assert stem_stoichiometry.element_surplus[cohort] == 0.0, (
#         "Surplus should be fully consumed"
#     )
#     assert np.isclose(total_gain, partial_surplus, rtol=1e-12, atol=1e-12), (
#         "Total gain should match partial surplus"
#     )


# def test_distribute_surplus_full(stem_stoichiometry):
#     """Test distribution of a full surplus that exceeds all deficits."""

#     # lower actuals so there is a deficit
#     for t in stem_stoichiometry.tissues:
#         t.actual_element_mass[:] *= 0.1

#     cohort = 1
#     initial_deficits = np.array(
#           [t.deficit[cohort] for t in stem_stoichiometry.tissues]
#     )
#     total_deficit = initial_deficits.sum()

#     # give more than enough surplus to cover all deficits
#     stem_stoichiometry.element_surplus[cohort] = total_deficit * 2.0

#     stem_stoichiometry.distribute_surplus(cohort)

#     # all tissues should now be at their ideal ratios
#     for t in stem_stoichiometry.tissues:
#         expected = t.carbon_mass[cohort] / t.ideal_ratio[cohort]
#         assert np.isclose(t.actual_element_mass[cohort], expected)

#     # surplus should remain
#     assert stem_stoichiometry.element_surplus[cohort] > 0.0


# @pytest.mark.parametrize(
#     "method,surplus",
#     [
#         ("distribute_deficit", 5.0),
#         ("distribute_surplus", -5.0),
#     ],
# )
# def test_error_triggers(method, surplus, stem_stoichiometry):
#     """Test that errors are raised when surplus/deficit conditions are violated."""

#     stem_stoichiometry.element_surplus[0] = surplus
#     with pytest.raises(ValueError):
#         getattr(stem_stoichiometry, method)(0)
