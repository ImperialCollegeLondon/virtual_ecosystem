1- aerodynamic_resistance_surface
=================================

===================  ==============================
name                 aerodynamic_resistance_surface
description          Aerodynamic resistance surface
unit                 m2
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  []
required_by_init     []
updated_by           ['hydrology']
required_by_update   []
===================  ==============================

2- air_heat_conductivity
========================

===================  ====================================
name                 air_heat_conductivity
description          Air heat conductivity between layers
unit                 mol m-2 s-1
variable_type        float
axis                 ['space']
populated_by_init    ['abiotic']
populated_by_update  []
required_by_init     []
updated_by           ['abiotic']
required_by_update   []
===================  ====================================

3- air_temperature
==================

===================  =============================
name                 air_temperature
description          Air temperature profile
unit                 C
variable_type        float
axis                 ['space']
populated_by_init    ['abiotic', 'hydrology']
populated_by_update  ['abiotic_simple']
required_by_init     []
updated_by           ['abiotic', 'abiotic_simple']
required_by_update   ['hydrology']
===================  =============================

4- air_temperature_ref
======================

===================  ========================================
name                 air_temperature_ref
description          Air temperature at reference height (2m)
unit                 C
variable_type        float
axis                 ['space', 'time']
populated_by_init    []
populated_by_update  []
required_by_init     ['abiotic', 'abiotic_simple']
updated_by           []
required_by_update   ['abiotic', 'abiotic_simple']
===================  ========================================

5- atmospheric_co2
==================

===================  =====================================
name                 atmospheric_co2
description          Atmospheric CO2 concentration profile
unit                 ppm
variable_type        float
axis                 ['space']
populated_by_init    ['abiotic']
populated_by_update  ['abiotic_simple']
required_by_init     []
updated_by           ['abiotic_simple']
required_by_update   []
===================  =====================================

6- atmospheric_co2_ref
======================

===================  ================================================================
name                 atmospheric_co2_ref
description          Atmospheric CO2 concentration at reference height (above canopy)
unit                 ppm
variable_type        float
axis                 ['space', 'time']
populated_by_init    []
populated_by_update  []
required_by_init     []
updated_by           []
required_by_update   ['abiotic', 'abiotic_simple']
===================  ================================================================

7- atmospheric_pressure
=======================

===================  ============================
name                 atmospheric_pressure
description          Atmospheric pressure profile
unit                 kPa
variable_type        float
axis                 ['space']
populated_by_init    ['abiotic', 'hydrology']
populated_by_update  ['abiotic_simple']
required_by_init     []
updated_by           ['abiotic_simple']
required_by_update   ['hydrology']
===================  ============================

8- atmospheric_pressure_ref
===========================

===================  =============================================
name                 atmospheric_pressure_ref
description          Atmospheric pressure at reference height (2m)
unit                 kPa
variable_type        float
axis                 ['space', 'time']
populated_by_init    []
populated_by_update  []
required_by_init     []
updated_by           []
required_by_update   ['abiotic', 'abiotic_simple']
===================  =============================================

9- attenuation_coefficient
==========================

===================  ============================
name                 attenuation_coefficient
description          Wind attenuation coefficient
unit                 -
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  ['abiotic']
required_by_init     []
updated_by           ['abiotic']
required_by_update   []
===================  ============================

10- baseflow
============

===================  =============
name                 baseflow
description          Baseflow
unit                 mm
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  ['hydrology']
required_by_init     []
updated_by           ['hydrology']
required_by_update   []
===================  =============

11- bulk_density
================

===================  ====================
name                 bulk_density
description          Bulk density of soil
unit                 kg m-3
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  []
required_by_init     ['soil']
updated_by           []
required_by_update   []
===================  ====================

12- bypass_flow
===============

===================  =============
name                 bypass_flow
description          Bypass flow
unit                 mm
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  ['hydrology']
required_by_init     []
updated_by           ['hydrology']
required_by_update   []
===================  =============

13- canopy_absorption
=====================

===================  ========================================================
name                 canopy_absorption
description          Shortwave radiation absorbed by individual canopy layers
unit
variable_type        float
axis                 ['space']
populated_by_init    ['abiotic', 'plants']
populated_by_update  []
required_by_init     []
updated_by           ['plants']
required_by_update   ['abiotic']
===================  ========================================================

14- canopy_height
=================

===================  =============
name                 canopy_height
description          Canopy height
unit                 m
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  []
required_by_init     []
updated_by           []
required_by_update   []
===================  =============

15- canopy_temperature
======================

===================  =======================================
name                 canopy_temperature
description          Canopy temperature of individual layers
unit                 C
variable_type        float
axis                 ['space']
populated_by_init    ['abiotic']
populated_by_update  []
required_by_init     []
updated_by           ['abiotic']
required_by_update   []
===================  =======================================

16- clay_fraction
=================

===================  ============================
name                 clay_fraction
description          The fraction of clay in soil
unit                 -
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  []
required_by_init     ['soil']
updated_by           []
required_by_update   []
===================  ============================

17- conductivity_from_ref_height
================================

===================  ==================================
name                 conductivity_from_ref_height
description          Conductivity from reference height
unit                 mol m-2 s-1
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  ['abiotic']
required_by_init     []
updated_by           ['abiotic']
required_by_update   []
===================  ==================================

18- conductivity_from_soil
==========================

===================  ======================
name                 conductivity_from_soil
description          Conductivity from soil
unit                 mol m-2 s-1
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  []
required_by_init     []
updated_by           []
required_by_update   []
===================  ======================

19- decomposed_carcasses
========================

===================  ================================================================
name                 decomposed_carcasses
description          Rate of decomposed carcass biomass flow from animals into litter
unit                 kg C m^-3 day^-1
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  []
required_by_init     []
updated_by           ['animal']
required_by_update   []
===================  ================================================================

20- decomposed_excrement
========================

===================  ===============================================
name                 decomposed_excrement
description          Rate of excrement flow from animals into litter
unit                 kg C m^-3 day^-1
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  []
required_by_init     []
updated_by           ['animal']
required_by_update   []
===================  ===============================================

21- diabatic_correction_heat_above
==================================

===================  ================================================
name                 diabatic_correction_heat_above
description          Diabatic correction factor for heat above canopy
unit                 -
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  ['abiotic']
required_by_init     []
updated_by           ['abiotic']
required_by_update   []
===================  ================================================

22- diabatic_correction_heat_canopy
===================================

===================  =============================================
name                 diabatic_correction_heat_canopy
description          Diabatic correction factor for heat in canopy
unit                 -
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  ['abiotic']
required_by_init     []
updated_by           ['abiotic']
required_by_update   []
===================  =============================================

23- diabatic_correction_momentum_above
======================================

===================  ====================================================
name                 diabatic_correction_momentum_above
description          Diabatic correction factor for momentum above canopy
unit                 -
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  ['abiotic']
required_by_init     []
updated_by           ['abiotic']
required_by_update   []
===================  ====================================================

24- diabatic_correction_momentum_canopy
=======================================

===================  =================================================
name                 diabatic_correction_momentum_canopy
description          Diabatic correction factor for momentum in canopy
unit                 -
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  ['abiotic']
required_by_init     []
updated_by           ['abiotic']
required_by_update   []
===================  =================================================

25- elevation
=============

===================  =========================
name                 elevation
description          Elevation above sea level
unit                 m
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  []
required_by_init     ['hydrology']
updated_by           []
required_by_update   []
===================  =========================

26- evapotranspiration
======================

===================  ==================
name                 evapotranspiration
description          Evapotranspiration
unit                 mm
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  []
required_by_init     []
updated_by           ['plants']
required_by_update   ['hydrology']
===================  ==================

27- friction_velocity
=====================

===================  =================
name                 friction_velocity
description          Friction velocity
unit                 m s-1
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  ['abiotic']
required_by_init     []
updated_by           ['abiotic']
required_by_update   []
===================  =================

28- ground_heat_flux
====================

===================  ================
name                 ground_heat_flux
description          Ground heat flux
unit                 W m-2
variable_type        float
axis                 ['space']
populated_by_init    ['abiotic']
populated_by_update  []
required_by_init     []
updated_by           ['abiotic']
required_by_update   []
===================  ================

29- groundwater_storage
=======================

===================  ===================
name                 groundwater_storage
description          Groundwater Storage
unit                 mm
variable_type        float
axis                 ['space']
populated_by_init    ['hydrology']
populated_by_update  []
required_by_init     []
updated_by           ['hydrology']
required_by_update   []
===================  ===================

30- latent_heat_flux
====================

===================  ========================
name                 latent_heat_flux
description          Latent heat flux profile
unit                 W m-2
variable_type        float
axis                 ['space']
populated_by_init    ['abiotic']
populated_by_update  []
required_by_init     []
updated_by           ['abiotic']
required_by_update   []
===================  ========================

31- latent_heat_flux_soil
=========================

===================  ===================================
name                 latent_heat_flux_soil
description          Latent heat flux from topsoil layer
unit                 W m-2
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  ['abiotic']
required_by_init     []
updated_by           ['abiotic']
required_by_update   []
===================  ===================================

32- latent_heat_vapourisation
=============================

===================  ============================
name                 latent_heat_vapourisation
description          Latent heat of vapourisation
unit                 kJ kg-1
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  ['hydrology']
required_by_init     []
updated_by           ['hydrology']
required_by_update   []
===================  ============================

33- layer_fapar
===============

===================  ==========================================================================================
name                 layer_fapar
description          The fraction of absorbed photosynthetically active radiation (f_APAR) in each model layer.
unit                 -
variable_type        float
axis                 ['space']
populated_by_init    ['plants']
populated_by_update  []
required_by_init     []
updated_by           ['plants']
required_by_update   []
===================  ==========================================================================================

34- layer_heights
=================

===================  ==========================================
name                 layer_heights
description          Heights of model layers
unit                 m
variable_type        float
axis                 ['space']
populated_by_init    ['plants']
populated_by_update  []
required_by_init     ['abiotic', 'hydrology']
updated_by           ['plants']
required_by_update   ['abiotic', 'abiotic_simple', 'hydrology']
===================  ==========================================

35- layer_leaf_mass
===================

===================  =======================================
name                 layer_leaf_mass
description          The leaf mass within each canopy layer.
unit                 kg
variable_type        float
axis                 ['space']
populated_by_init    ['plants']
populated_by_update  []
required_by_init     []
updated_by           ['plants']
required_by_update   []
===================  =======================================

36- leaf_air_heat_conductivity
==============================

===================  ==========================
name                 leaf_air_heat_conductivity
description          Leaf air heat conductivity
unit                 mol m-2 s-1
variable_type        float
axis                 ['space']
populated_by_init    ['abiotic']
populated_by_update  []
required_by_init     []
updated_by           ['abiotic']
required_by_update   []
===================  ==========================

37- leaf_area_index
===================

===================  ==========================================
name                 leaf_area_index
description          Leaf area index
unit                 m m-1
variable_type        float
axis                 ['space']
populated_by_init    ['plants']
populated_by_update  []
required_by_init     ['abiotic']
updated_by           ['plants']
required_by_update   ['abiotic', 'abiotic_simple', 'hydrology']
===================  ==========================================

38- leaf_vapour_conductivity
============================

===================  ========================
name                 leaf_vapour_conductivity
description          Leaf vapour conductivity
unit                 mol m-2 s-1
variable_type        float
axis                 ['space']
populated_by_init    ['abiotic']
populated_by_update  []
required_by_init     []
updated_by           ['abiotic']
required_by_update   []
===================  ========================

39- lignin_above_structural
===========================

===================  ==========================================================
name                 lignin_above_structural
description          Proportion of above ground structural pool which is lignin
unit                 -
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  []
required_by_init     ['litter']
updated_by           ['litter']
required_by_update   ['litter']
===================  ==========================================================

40- lignin_below_structural
===========================

===================  ==========================================================
name                 lignin_below_structural
description          Proportion of below ground structural pool which is lignin
unit                 -
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  []
required_by_init     ['litter']
updated_by           ['litter']
required_by_update   ['litter']
===================  ==========================================================

41- lignin_woody
================

===================  ============================================
name                 lignin_woody
description          Proportion of dead wood pool which is lignin
unit                 -
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  []
required_by_init     ['litter']
updated_by           ['litter']
required_by_update   ['litter']
===================  ============================================

42- litter_C_mineralisation_rate
================================

===================  ===========================================
name                 litter_C_mineralisation_rate
description          Rate of carbon addition to soil from litter
unit                 kg C m^-3 day^-1
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  ['litter']
required_by_init     []
updated_by           ['litter']
required_by_update   []
===================  ===========================================

43- litter_pool_above_metabolic
===============================

===================  ==================================
name                 litter_pool_above_metabolic
description          Above ground metabolic litter pool
unit                 kg C m^-2
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  []
required_by_init     ['litter']
updated_by           ['litter']
required_by_update   ['litter']
===================  ==================================

44- litter_pool_above_structural
================================

===================  ===================================
name                 litter_pool_above_structural
description          Above ground structural litter pool
unit                 kg C m^-2
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  []
required_by_init     ['litter']
updated_by           ['litter']
required_by_update   ['litter']
===================  ===================================

45- litter_pool_below_metabolic
===============================

===================  ==================================
name                 litter_pool_below_metabolic
description          Below ground metabolic litter pool
unit                 kg C m^-2
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  []
required_by_init     ['litter']
updated_by           ['litter']
required_by_update   ['litter']
===================  ==================================

46- litter_pool_below_structural
================================

===================  ===================================
name                 litter_pool_below_structural
description          Below ground structural litter pool
unit                 kg C m^-2
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  []
required_by_init     ['litter']
updated_by           ['litter']
required_by_update   ['litter']
===================  ===================================

47- litter_pool_woody
=====================

===================  =================
name                 litter_pool_woody
description          Woody litter pool
unit                 kg C m^-2
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  []
required_by_init     ['litter']
updated_by           ['litter']
required_by_update   ['litter']
===================  =================

48- longwave_canopy
===================

===================  ================================================
name                 longwave_canopy
description          Longwave radiation from individual canopy layers
unit                 W m-2
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  []
required_by_init     []
updated_by           []
required_by_update   []
===================  ================================================

49- longwave_emission_soil
==========================

===================  =====================================
name                 longwave_emission_soil
description          Longwave radiation from topsoil layer
unit                 W m-2
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  ['abiotic']
required_by_init     []
updated_by           ['abiotic']
required_by_update   []
===================  =====================================

50- matric_potential
====================

===================  ================
name                 matric_potential
description          Matric potential
unit                 kPa
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  ['hydrology']
required_by_init     []
updated_by           ['hydrology']
required_by_update   []
===================  ================

51- mean_annual_temperature
===========================

===================  ===========================================================
name                 mean_annual_temperature
description          Mean annual temperature = temperature of deepest soil layer
unit                 C
variable_type        float
axis                 ['space', 'time']
populated_by_init    []
populated_by_update  []
required_by_init     []
updated_by           []
required_by_update   []
===================  ===========================================================

52- mean_mixing_length
======================

===================  ==================
name                 mean_mixing_length
description          Mean mixing length
unit                 m
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  ['abiotic']
required_by_init     []
updated_by           ['abiotic']
required_by_update   []
===================  ==================

53- molar_density_air
=====================

===================  ==========================================
name                 molar_density_air
description          Temperature-dependent molar density of air
unit                 kg m-3
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  ['abiotic', 'hydrology']
required_by_init     []
updated_by           ['abiotic', 'hydrology']
required_by_update   []
===================  ==========================================

54- pH
======

===================  =================================
name                 pH
description          Soil pH values for each grid cell
unit                 pH
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  []
required_by_init     ['soil']
updated_by           []
required_by_update   []
===================  =================================

55- photosynthetic_photon_flux_density
======================================

===================  =======================================================
name                 photosynthetic_photon_flux_density
description          Top of canopy photosynthetic photon flux density (PPFD)
unit                 µmol m-2 s-1
variable_type        float
axis                 ['space', 'time']
populated_by_init    []
populated_by_update  []
required_by_init     ['plants']
updated_by           []
required_by_update   ['plants']
===================  =======================================================

56- plant_cohorts_cell_id
=========================

===================  ======================================
name                 plant_cohorts_cell_id
description          Cell ID of plant cohorts
unit                 -
variable_type        int
axis                 ['as_yet_undefined_cohort_setup_axis']
populated_by_init    []
populated_by_update  []
required_by_init     ['plants']
updated_by           []
required_by_update   ['plants']
===================  ======================================

57- plant_cohorts_dbh
=====================

===================  =========================================================
name                 plant_cohorts_dbh
description          Diameter at breast height of individuals in plant cohorts
unit                 m
variable_type        float
axis                 ['as_yet_undefined_cohort_setup_axis']
populated_by_init    []
populated_by_update  []
required_by_init     ['plants']
updated_by           []
required_by_update   ['plants']
===================  =========================================================

58- plant_cohorts_n
===================

===================  =======================================
name                 plant_cohorts_n
description          Number of individuals in a plant cohort
unit                 -
variable_type        int
axis                 ['as_yet_undefined_cohort_setup_axis']
populated_by_init    []
populated_by_update  []
required_by_init     ['plants']
updated_by           []
required_by_update   ['plants']
===================  =======================================

59- plant_cohorts_pft
=====================

===================  ======================================
name                 plant_cohorts_pft
description          Plant functional type of plant cohorts
unit                 -
variable_type        str
axis                 ['as_yet_undefined_cohort_setup_axis']
populated_by_init    []
populated_by_update  []
required_by_init     ['plants']
updated_by           []
required_by_update   ['plants']
===================  ======================================

60- plant_net_co2_assimilation
==============================

===================  ==========================
name                 plant_net_co2_assimilation
description          Plant net CO2 assimilation
unit                 ppm
variable_type
axis                 []
populated_by_init    []
populated_by_update  []
required_by_init     []
updated_by           []
required_by_update   []
===================  ==========================

61- population_densities
========================

===================  =======================================
name                 population_densities
description          Density of animal populations.
unit                 ???
variable_type        float
axis                 ['community_id', 'functional_group_id']
populated_by_init    ['animal']
populated_by_update  []
required_by_init     []
updated_by           []
required_by_update   []
===================  =======================================

62- precipitation
=================

===================  ============================================
name                 precipitation
description          Precipitation input at the top of the canopy
unit                 mm
variable_type        float
axis                 ['space', 'time']
populated_by_init    []
populated_by_update  []
required_by_init     []
updated_by           []
required_by_update   ['hydrology']
===================  ============================================

63- precipitation_surface
=========================

===================  ==================================
name                 precipitation_surface
description          Precipitation that reaches surface
unit                 mm
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  ['hydrology']
required_by_init     []
updated_by           ['hydrology']
required_by_update   []
===================  ==================================

64- relative_humidity
=====================

===================  =========================
name                 relative_humidity
description          Relative humidity profile
unit                 %
variable_type        float
axis                 ['space']
populated_by_init    ['abiotic', 'hydrology']
populated_by_update  ['abiotic_simple']
required_by_init     []
updated_by           ['abiotic_simple']
required_by_update   ['hydrology']
===================  =========================

65- relative_humidity_ref
=========================

===================  ==========================================
name                 relative_humidity_ref
description          Relative humidity at reference height (2m)
unit                 %
variable_type        float
axis                 ['space', 'time']
populated_by_init    []
populated_by_update  []
required_by_init     ['abiotic', 'abiotic_simple']
updated_by           []
required_by_update   ['abiotic', 'abiotic_simple']
===================  ==========================================

66- relative_turbulence_intensity
=================================

===================  =============================
name                 relative_turbulence_intensity
description          Relative turbulence intensity
unit                 -
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  ['abiotic']
required_by_init     []
updated_by           ['abiotic']
required_by_update   []
===================  =============================

67- river_discharge_rate
========================

===================  ====================
name                 river_discharge_rate
description          River discharge rate
unit                 m3 s-1
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  ['hydrology']
required_by_init     []
updated_by           ['hydrology']
required_by_update   []
===================  ====================

68- roughness_length_momentum
=============================

===================  =============================
name                 roughness_length_momentum
description          Roughness length for momentum
unit                 m
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  []
required_by_init     []
updated_by           []
required_by_update   []
===================  =============================

69- saturated_vapour_pressure_ref
=================================

===================  ==================================================
name                 saturated_vapour_pressure_ref
description          Saturated vapour pressure at reference height (2m)
unit                 kPa
variable_type        float
axis                 ['space', 'time']
populated_by_init    []
populated_by_update  []
required_by_init     []
updated_by           []
required_by_update   []
===================  ==================================================

70- sensible_heat_flux
======================

===================  ==========================
name                 sensible_heat_flux
description          Sensible heat flux profile
unit                 W m-2
variable_type        float
axis                 ['space']
populated_by_init    ['abiotic']
populated_by_update  []
required_by_init     []
updated_by           ['abiotic']
required_by_update   []
===================  ==========================

71- sensible_heat_flux_soil
===========================

===================  =====================================
name                 sensible_heat_flux_soil
description          Sensible heat flux from topsoil layer
unit                 W m-2
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  ['abiotic']
required_by_init     []
updated_by           ['abiotic']
required_by_update   []
===================  =====================================

72- shortwave_radiation_surface
===============================

===================  ==================================
name                 shortwave_radiation_surface
description          Shortwave radiation at the surface
unit                 W m-2
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  []
required_by_init     []
updated_by           []
required_by_update   []
===================  ==================================

73- soil_absorption
===================

===================  =============================================
name                 soil_absorption
description          Shortwave radiation absorbed by topsoil layer
unit                 W m-2
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  ['abiotic']
required_by_init     []
updated_by           ['abiotic']
required_by_update   []
===================  =============================================

74- soil_c_pool_lmwc
====================

===================  =====================================
name                 soil_c_pool_lmwc
description          Soil low molecular weight carbon pool
unit                 kg C m-3
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  []
required_by_init     ['soil']
updated_by           ['soil']
required_by_update   ['soil']
===================  =====================================

75- soil_c_pool_maom
====================

===================  ===========================================
name                 soil_c_pool_maom
description          Soil mineral associated organic matter pool
unit                 kg C m-3
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  []
required_by_init     ['soil']
updated_by           ['soil']
required_by_update   ['soil']
===================  ===========================================

76- soil_c_pool_microbe
=======================

===================  ====================================
name                 soil_c_pool_microbe
description          Soil microbial biomass (carbon) pool
unit                 kg C m-3
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  []
required_by_init     ['soil']
updated_by           ['soil']
required_by_update   ['soil']
===================  ====================================

77- soil_c_pool_necromass
=========================

===================  ============================
name                 soil_c_pool_necromass
description          Necrotic organic matter pool
unit                 kg C m-3
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  []
required_by_init     []
updated_by           ['soil']
required_by_update   []
===================  ============================

78- soil_c_pool_pom
===================

===================  ===============================
name                 soil_c_pool_pom
description          Particulate organic matter pool
unit                 kg C m-3
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  []
required_by_init     ['soil']
updated_by           ['soil']
required_by_update   ['soil']
===================  ===============================

79- soil_enzyme_maom
====================

===================  ==========================================================================
name                 soil_enzyme_maom
description          Amount of enzyme class which breaks down mineral associated organic matter
unit                 kg C m^-3
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  []
required_by_init     ['soil']
updated_by           ['soil']
required_by_update   ['soil']
===================  ==========================================================================

80- soil_enzyme_pom
===================

===================  ===================================================================
name                 soil_enzyme_pom
description          Amount of enzyme class which breaks down particulate organic matter
unit                 kg C m^-3
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  []
required_by_init     ['soil']
updated_by           ['soil']
required_by_update   ['soil']
===================  ===================================================================

81- soil_evaporation
====================

===================  ================
name                 soil_evaporation
description          Soil evaporation
unit                 mm
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  ['hydrology']
required_by_init     []
updated_by           ['hydrology']
required_by_update   []
===================  ================

82- soil_moisture
=================

===================  =============
name                 soil_moisture
description          Soil moisture
unit                 mm
variable_type        float
axis                 ['space']
populated_by_init    ['hydrology']
populated_by_update  []
required_by_init     []
updated_by           ['hydrology']
required_by_update   ['hydrology']
===================  =============

83- soil_respiration
====================

===================  ================
name                 soil_respiration
description          Soil respiration
unit                 ppm
variable_type
axis                 ['space']
populated_by_init    []
populated_by_update  []
required_by_init     []
updated_by           []
required_by_update   []
===================  ================

84- soil_temperature
====================

===================  =============================
name                 soil_temperature
description          Soil temperature profile
unit                 C
variable_type        float
axis                 ['space']
populated_by_init    ['abiotic', 'abiotic_simple']
populated_by_update  []
required_by_init     []
updated_by           ['abiotic', 'abiotic_simple']
required_by_update   []
===================  =============================

85- soil_vapour_pressure
========================

===================  ====================
name                 soil_vapour_pressure
description          Soil vapour pressure
unit                 kPa
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  []
required_by_init     []
updated_by           []
required_by_update   []
===================  ====================

86- specific_heat_air
=====================

===================  ====================
name                 specific_heat_air
description          Specific heat of air
unit                 kJ kg-1
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  ['abiotic']
required_by_init     []
updated_by           ['abiotic']
required_by_update   []
===================  ====================

87- specific_humidity
=====================

===================  ========================
name                 specific_humidity
description          Specific humidity of air
unit                 g kg-1
variable_type
axis                 ['space']
populated_by_init    []
populated_by_update  []
required_by_init     []
updated_by           []
required_by_update   []
===================  ========================

88- stomatal_conductance
========================

===================  ====================
name                 stomatal_conductance
description          Stomatal conductance
unit                 mol m-2 s-1
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  []
required_by_init     []
updated_by           []
required_by_update   ['abiotic']
===================  ====================

89- stream_flow
===============

===================  =====================
name                 stream_flow
description          Estimated stream flow
unit                 mm per time step
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  []
required_by_init     []
updated_by           []
required_by_update   []
===================  =====================

90- subsurface_flow
===================

===================  ===============
name                 subsurface_flow
description          Subsurface flow
unit                 mm
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  ['hydrology']
required_by_init     []
updated_by           ['hydrology']
required_by_update   []
===================  ===============

91- subsurface_flow_accumulated
===============================

===================  ===========================
name                 subsurface_flow_accumulated
description          Accumulated subsurface flow
unit                 mm
variable_type        float
axis                 ['space']
populated_by_init    ['hydrology']
populated_by_update  []
required_by_init     []
updated_by           ['hydrology']
required_by_update   ['hydrology']
===================  ===========================

92- surface_runoff
==================

===================  ==========================================
name                 surface_runoff
description          Surface runoff generated in each grid cell
unit                 mm
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  ['hydrology']
required_by_init     []
updated_by           ['hydrology']
required_by_update   []
===================  ==========================================

93- surface_runoff_accumulated
==============================

===================  ==========================
name                 surface_runoff_accumulated
description          Accumlated surface runoff
unit                 mm
variable_type        float
axis                 ['space']
populated_by_init    ['hydrology']
populated_by_update  []
required_by_init     []
updated_by           ['hydrology']
required_by_update   ['hydrology']
===================  ==========================

94- topofcanopy_radiation
=========================

===================  ==========================================
name                 topofcanopy_radiation
description          Top of canopy downward shortwave radiation
unit                 W m-2
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  []
required_by_init     ['abiotic']
updated_by           []
required_by_update   ['abiotic']
===================  ==========================================

95- total_animal_respiration
============================

===================  =======================================================
name                 total_animal_respiration
description          Animal respiration aggregated over all functional types
unit                 ppm
variable_type        float
axis                 ['space']
populated_by_init    ['animal']
populated_by_update  []
required_by_init     []
updated_by           ['animal']
required_by_update   []
===================  =======================================================

96- total_river_discharge
=========================

===================  =====================
name                 total_river_discharge
description          Total river discharge
unit                 mm
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  ['hydrology']
required_by_init     []
updated_by           ['hydrology']
required_by_update   []
===================  =====================

97- vapour_pressure
===================

===================  =======================
name                 vapour_pressure
description          Vapour pressure profile
unit                 kPa
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  ['abiotic']
required_by_init     []
updated_by           ['abiotic']
required_by_update   []
===================  =======================

98- vapour_pressure_deficit
===========================

===================  ===============================
name                 vapour_pressure_deficit
description          Vapour pressure deficit profile
unit                 kPa
variable_type        float
axis                 ['space']
populated_by_init    ['abiotic']
populated_by_update  ['abiotic_simple']
required_by_init     []
updated_by           ['abiotic', 'abiotic_simple']
required_by_update   []
===================  ===============================

99- vapour_pressure_deficit_ref
===============================

===================  ================================================
name                 vapour_pressure_deficit_ref
description          Vapour pressure deficit at reference height (2m)
unit                 kPa
variable_type        float
axis                 ['space', 'time']
populated_by_init    ['abiotic', 'abiotic_simple']
populated_by_update  []
required_by_init     []
updated_by           []
required_by_update   ['abiotic', 'abiotic_simple']
===================  ================================================

100- vapour_pressure_ref
========================

===================  ========================================
name                 vapour_pressure_ref
description          Vapour pressure at reference height (2m)
unit                 kPa
variable_type        float
axis                 ['space', 'time']
populated_by_init    ['abiotic', 'abiotic_simple']
populated_by_update  []
required_by_init     []
updated_by           []
required_by_update   []
===================  ========================================

101- vertical_flow
==================

===================  ==========================================
name                 vertical_flow
description          Vertical flow of water through soil column
unit                 mm per time step (currently day)
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  ['hydrology']
required_by_init     []
updated_by           ['hydrology']
required_by_update   []
===================  ==========================================

102- wind_speed
===============

===================  ====================================
name                 wind_speed
description          Wind profile within and below canopy
unit                 m s-1
variable_type        float
axis                 ['space']
populated_by_init    ['hydrology']
populated_by_update  ['abiotic']
required_by_init     []
updated_by           ['abiotic']
required_by_update   ['hydrology']
===================  ====================================

103- wind_speed_ref
===================

===================  ====================================
name                 wind_speed_ref
description          Wind speed at reference height (10m)
unit                 m s-1
variable_type        float
axis                 ['space', 'time']
populated_by_init    []
populated_by_update  []
required_by_init     []
updated_by           []
required_by_update   ['abiotic']
===================  ====================================

104- zero_displacement_height
=============================

===================  ========================
name                 zero_displacement_height
description          Zero displacement height
unit                 m
variable_type        float
axis                 ['space']
populated_by_init    []
populated_by_update  ['abiotic']
required_by_init     []
updated_by           ['abiotic']
required_by_update   []
===================  ========================
