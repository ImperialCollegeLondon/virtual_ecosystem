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


def test_Element_append():
    """Tests the append() method of Element."""

    from virtual_ecosystem.models.plants.biomasses import Element

    e1 = Element(
        name="N",
        ideal_ratio=np.arange(10),
        actual_element_mass=np.arange(10),
        turnover_ratio=np.arange(10),
    )

    e2 = Element(
        name="N",
        ideal_ratio=np.arange(10),
        actual_element_mass=np.arange(10),
        turnover_ratio=np.arange(10),
    )

    e1.append(e2)

    assert e1.ideal_ratio.shape == (20,)
    assert e1.actual_element_mass.shape == (20,)
    assert e1.turnover_ratio.shape == (20,)


def test_Tissue_append(fixture_community):
    """Tests the shared append() method of TissueABC."""

    from virtual_ecosystem.models.plants.biomasses import Element, FoliageTissue

    foliage_1 = FoliageTissue(
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

    foliage_2 = FoliageTissue(
        community=fixture_community,
        carbon_mass=fixture_community.stem_allometry.foliage_mass.copy(),
        element_masses={
            "N": Element(
                name="n",
                ideal_ratio=np.array([5.1, 6.1]),
                actual_element_mass=np.array([5.1, 20.1]),
                turnover_ratio=np.array([10.1, 12.1]),
            ),
            "P": Element(
                name="p",
                ideal_ratio=np.array([5.1, 6.1]),
                actual_element_mass=np.array([5.1, 20.1]),
                turnover_ratio=np.array([10.1, 12.1]),
            ),
        },
    )

    foliage_1.append(foliage_2)

    assert np.allclose(
        foliage_1.carbon_mass, np.tile(fixture_community.stem_allometry.foliage_mass, 2)
    )

    for elem in foliage_1.element_masses.values():
        assert np.allclose(elem.ideal_ratio, np.array([5.0, 6.0, 5.1, 6.1]))
        assert np.allclose(elem.actual_element_mass, np.array([5.0, 20.0, 5.1, 20.1]))
        assert np.allclose(elem.turnover_ratio, np.array([10.0, 12.0, 10.1, 12.1]))


def test_Biomasses_append(fixture_biomasses):
    """Test the Biomasses append() method."""

    fixture_biomasses.append(fixture_biomasses)


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


def test_account_for_element_loss_turnover(
    fixture_community, fixture_biomasses, fixture_stem_allocation
):
    """Test account for element loss function in Biomasses."""

    fixture_biomasses.account_for_element_loss_turnover(fixture_stem_allocation)

    expected_surplus = np.zeros(
        (fixture_community.n_cohorts, len(fixture_biomasses.elements))
    )

    for t in fixture_biomasses.tissues:
        turnover_loss = t.tissue_turnover(fixture_stem_allocation)
        expected_surplus -= np.stack(list(turnover_loss.values()))

    assert np.allclose(
        np.stack(list(fixture_biomasses.element_surplus.values())), expected_surplus
    )


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
        FoliageTissue,
        WoodTissue,
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

    foliage = FoliageTissue(
        community=fixture_community,
        # Note that this only has two cohorts - not sure Tissue will retain community
        # as an argument.
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

    wood = WoodTissue(
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
        extra_pft_traits=SimpleNamespace(),
    )

    # Set the element pools to balance
    biomasses.element_surplus = {
        ky: initial_pool[idx] for idx, ky in enumerate(biomasses.elements)
    }

    # Run the method.
    biomasses.balance_elements()

    # Check the expectations.
    foliage = biomasses.get_tissue("foliage").as_array()
    assert np.allclose(foliage, expected_foliage)

    wood = biomasses.get_tissue("wood").as_array()
    assert np.allclose(wood, expected_wood)

    pool = np.stack(list(biomasses.element_surplus.values()))
    assert np.allclose(pool, expected_pool)
