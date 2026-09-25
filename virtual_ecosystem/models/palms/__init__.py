"""The :mod:`~virtual_ecosystem.models.palms` module provides
the :class:`~virtual_ecosystem.models.palms.palms_model.PalmsModel`
implementation for use in the Virtual Ecosystem.

This is a standalone growth-form model for palms, structured as a sibling of
:mod:`~virtual_ecosystem.models.plants`. It reuses much of the plants model
infrastructure (biomass tracking, canopy construction, subcanopy vegetation, fruit
decay and the community data exporter) but replaces the DBH-driven T Model
allometry and allocation equations with height-driven palm growth equations,
implemented in :mod:`~virtual_ecosystem.models.palms.palms`.

The main submodule is :mod:`~virtual_ecosystem.models.palms.palms_model` submodule,
which provides the :class:`~virtual_ecosystem.models.palms.palms_model.PalmsModel`
class as the main API to initialise and update the palms model.

The other submodules include:

* The :mod:`~virtual_ecosystem.models.palms.model_config` submodule provides
  configuration options for the model along with constants used in the model.

* The :mod:`~virtual_ecosystem.models.palms.palms` submodule provides local
  ``StemAllometry``, ``StemAllocation`` and ``GrowthIncrements`` classes analogous to
  :mod:`pyrealm.demography.tmodel`, implementing the palm growth form equations.

* The :mod:`~virtual_ecosystem.models.palms.communities` submodule provides the
  :class:`~virtual_ecosystem.models.palms.communities.PalmCommunities` class which
  maps each grid cell on to a representation of the palm community within that cell,
  built from cohort data keyed on stem height rather than diameter at breast height.

* The :mod:`~virtual_ecosystem.models.palms.functional_types` submodule provides a
  standalone ``PalmFloraValidator``, extending
  :class:`~virtual_ecosystem.models.plants.functional_types.VEFloraValidator` with
  the palm-specific ``palm_a``, ``palm_b`` and ``palm_stem_resp_fraction`` traits.
  This validator is kept separate from the shared tree PFT validator so that existing
  tree PFT definition CSVs do not need to be updated to include palm-only traits;
  palm PFT CSVs must include these three columns.
"""  # noqa: D205
