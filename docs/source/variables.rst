1- aerodynamic_resistance_surface
=================================

================== =================================
name               aerodynamic_resistance_surface   
description        Aerodynamic resistance at surface
unit                                                
variable_type                                       
axis               []                               
initialised_by     None                             
required_init_by   []                               
updated_by         ['hydrology']                    
required_update_by []                               
================== =================================

2- air_heat_conductivity
========================

================== =====================
name               air_heat_conductivity
description        Air heat conductivity
unit                                    
variable_type                           
axis               []                   
initialised_by     None                 
required_init_by   []                   
updated_by         ['abiotic']          
required_update_by []                   
================== =====================

3- air_temperature
==================

================== =============================
name               air_temperature              
description        Air temperature profile      
unit               C                            
variable_type                                   
axis               []                           
initialised_by     None                         
required_init_by   []                           
updated_by         ['abiotic', 'abiotic_simple']
required_update_by []                           
================== =============================

4- air_temperature_ref
======================

================== ==========================================
name               air_temperature_ref                       
description        Air temperature at reference height (2m)  
unit               C                                         
variable_type                                                
axis               []                                        
initialised_by     None                                      
required_init_by   ['abiotic', 'abiotic_simple', 'hydrology']
updated_by         []                                        
required_update_by []                                        
================== ==========================================

5- albedo_shortwave
===================

================== ======================
name               albedo_shortwave      
description        Shortwave light albedo
unit               -                     
variable_type                            
axis               []                    
initialised_by     None                  
required_init_by   []                    
updated_by         []                    
required_update_by []                    
================== ======================

6- albedo_vis
=============

================== ====================
name               albedo_vis          
description        Visible light albedo
unit               -                   
variable_type                          
axis               []                  
initialised_by     None                
required_init_by   []                  
updated_by         []                  
required_update_by []                  
================== ====================

7- animal_respiration
=====================

================== =======================================================
name               animal_respiration                                     
description        Animal respiration aggregated over all functional types
unit               ppm                                                    
variable_type                                                             
axis               []                                                     
initialised_by     None                                                   
required_init_by   []                                                     
updated_by         []                                                     
required_update_by []                                                     
================== =======================================================

8- atmospheric_co2
==================

================== =====================================
name               atmospheric_co2                      
description        Atmospheric CO2 concentration profile
unit               ppm                                  
variable_type                                           
axis               []                                   
initialised_by     None                                 
required_init_by   []                                   
updated_by         ['abiotic_simple']                   
required_update_by []                                   
================== =====================================

9- atmospheric_co2_ref
======================

================== ================================================================
name               atmospheric_co2_ref                                             
description        Atmospheric CO2 concentration at reference height (above canopy)
unit               ppm                                                             
variable_type                                                                      
axis               []                                                              
initialised_by     None                                                            
required_init_by   []                                                              
updated_by         []                                                              
required_update_by []                                                              
================== ================================================================

10- atmospheric_pressure
========================

================== ============================
name               atmospheric_pressure        
description        Atmospheric pressure profile
unit               kPa                         
variable_type                                  
axis               []                          
initialised_by     None                        
required_init_by   []                          
updated_by         ['abiotic_simple']          
required_update_by []                          
================== ============================

11- atmospheric_pressure_ref
============================

================== =============================================
name               atmospheric_pressure_ref                     
description        Atmospheric pressure at reference height (2m)
unit               kPa                                          
variable_type                                                   
axis               []                                           
initialised_by     None                                         
required_init_by   ['hydrology']                                
updated_by         []                                           
required_update_by []                                           
================== =============================================

12- baseflow
============

================== =============
name               baseflow     
description        Base flow    
unit                            
variable_type                   
axis               []           
initialised_by     None         
required_init_by   []           
updated_by         ['hydrology']
required_update_by []           
================== =============

13- bulk_aerodynamic_resistance
===============================

================== ===========================
name               bulk_aerodynamic_resistance
description        Bulk aerodynamic resistance
unit               s m-1                      
variable_type                                 
axis               []                         
initialised_by     None                       
required_init_by   []                         
updated_by         []                         
required_update_by []                         
================== ===========================

14- bulk_density
================

================== ====================
name               bulk_density        
description        Bulk density of soil
unit               kg m-3              
variable_type                          
axis               []                  
initialised_by     None                
required_init_by   ['soil']            
updated_by         []                  
required_update_by []                  
================== ====================

15- canopy_absorption
=====================

================== ========================================================
name               canopy_absorption                                       
description        Shortwave radiation absorbed by individual canopy layers
unit               J m-2                                                   
variable_type                                                              
axis               []                                                      
initialised_by     None                                                    
required_init_by   []                                                      
updated_by         []                                                      
required_update_by []                                                      
================== ========================================================

16- canopy_height
=================

================== =============
name               canopy_height
description        Canopy height
unit               m            
variable_type                   
axis               []           
initialised_by     None         
required_init_by   []           
updated_by         []           
required_update_by []           
================== =============

17- canopy_temperature
======================

================== =======================================
name               canopy_temperature                     
description        Canopy temperature of individual layers
unit               C                                      
variable_type                                             
axis               []                                     
initialised_by     None                                   
required_init_by   []                                     
updated_by         ['abiotic']                            
required_update_by []                                     
================== =======================================

18- clay_fraction
=================

================== ========================
name               clay_fraction           
description        Fraction of clay in soil
unit                                       
variable_type                              
axis               []                      
initialised_by     None                    
required_init_by   ['soil']                
updated_by         []                      
required_update_by []                      
================== ========================

19- conductivity_from_ref_height
================================

================== ==================================
name               conductivity_from_ref_height      
description        Conductivity from reference height
unit                                                 
variable_type                                        
axis               []                                
initialised_by     None                              
required_init_by   []                                
updated_by         ['abiotic']                       
required_update_by []                                
================== ==================================

20- decomposed_carcasses
========================

================== ================================================================
name               decomposed_carcasses                                            
description        Rate of decomposed carcass biomass flow from animals into litter
unit               kg C m^-3 day^-1                                                
variable_type                                                                      
axis               []                                                              
initialised_by     None                                                            
required_init_by   []                                                              
updated_by         []                                                              
required_update_by []                                                              
================== ================================================================

21- decomposed_excrement
========================

================== ===============================================
name               decomposed_excrement                           
description        Rate of excrement flow from animals into litter
unit               kg C m^-3 day^-1                               
variable_type                                                     
axis               []                                             
initialised_by     None                                           
required_init_by   []                                             
updated_by         []                                             
required_update_by []                                             
================== ===============================================

22- elevation
=============

================== =========================
name               elevation                
description        Elevation above sea level
unit               m                        
variable_type                               
axis               []                       
initialised_by     None                     
required_init_by   ['hydrology']            
updated_by         []                       
required_update_by []                       
================== =========================

23- evapotranspiration
======================

================== ==================
name               evapotranspiration
description        Evapotranspiration
unit               -                 
variable_type                        
axis               []                
initialised_by     None              
required_init_by   []                
updated_by         ['plants']        
required_update_by []                
================== ==================

24- friction_velocity
=====================

================== =================
name               friction_velocity
description        Friction velocity
unit               m s-1            
variable_type                       
axis               []               
initialised_by     None             
required_init_by   []               
updated_by         []               
required_update_by []               
================== =================

25- ground_heat_flux
====================

================== ================
name               ground_heat_flux
description        Ground heat flux
unit               J m-2           
variable_type                      
axis               []              
initialised_by     None            
required_init_by   []              
updated_by         []              
required_update_by []              
================== ================

26- groundwater_storage
=======================

================== ===================
name               groundwater_storage
description        Groundwater Storage
unit                                  
variable_type                         
axis               []                 
initialised_by     None               
required_init_by   []                 
updated_by         ['hydrology']      
required_update_by []                 
================== ===================

27- latent_heat_flux_canopy
===========================

================== ===================================
name               latent_heat_flux_canopy            
description        Latent heat flux from canopy layers
unit               J m-2                              
variable_type                                         
axis               []                                 
initialised_by     None                               
required_init_by   []                                 
updated_by         []                                 
required_update_by []                                 
================== ===================================

28- latent_heat_flux_soil
=========================

================== ===================================
name               latent_heat_flux_soil              
description        Latent heat flux from surface layer
unit               J m-2                              
variable_type                                         
axis               []                                 
initialised_by     None                               
required_init_by   []                                 
updated_by         []                                 
required_update_by []                                 
================== ===================================

29- latent_heat_vapourisation
=============================

================== ============================
name               latent_heat_vapourisation   
description        Latent heat of vapourisation
unit                                           
variable_type                                  
axis               []                          
initialised_by     None                        
required_init_by   []                          
updated_by         ['hydrology']               
required_update_by []                          
================== ============================

30- layer_absorbed_irradiation
==============================

================== ==========================
name               layer_absorbed_irradiation
description        layer_absorbed_irradiation
unit                                         
variable_type                                
axis               []                        
initialised_by     None                      
required_init_by   []                        
updated_by         ['plants']                
required_update_by []                        
================== ==========================

31- layer_fapar
===============

================== ===========
name               layer_fapar
description        layer_fapar
unit                          
variable_type                 
axis               []         
initialised_by     None       
required_init_by   []         
updated_by         ['plants'] 
required_update_by []         
================== ===========

32- layer_heights
=================

================== ========================
name               layer_heights           
description        Heights of canopy layers
unit               m                       
variable_type                              
axis               []                      
initialised_by     None                    
required_init_by   []                      
updated_by         ['plants']              
required_update_by []                      
================== ========================

33- layer_leaf_mass
===================

================== ===============
name               layer_leaf_mass
description        layer_leaf_mass
unit                              
variable_type                     
axis               []             
initialised_by     None           
required_init_by   []             
updated_by         ['plants']     
required_update_by []             
================== ===============

34- leaf_air_heat_conductivity
==============================

================== ==========================
name               leaf_air_heat_conductivity
description        Leaf air heat conductivity
unit                                         
variable_type                                
axis               []                        
initialised_by     None                      
required_init_by   []                        
updated_by         ['abiotic']               
required_update_by []                        
================== ==========================

35- leaf_area_index
===================

================== ===============
name               leaf_area_index
description        Leaf area index
unit               m m            
variable_type                     
axis               []             
initialised_by     None           
required_init_by   ['hydrology']  
updated_by         ['plants']     
required_update_by []             
================== ===============

36- leaf_vapour_conductivity
============================

================== ========================
name               leaf_vapour_conductivity
description        Leaf vapour conductivity
unit                                       
variable_type                              
axis               []                      
initialised_by     None                    
required_init_by   []                      
updated_by         ['abiotic']             
required_update_by []                      
================== ========================

37- lignin_above_structural
===========================

================== ================================================
name               lignin_above_structural                         
description        Lignin content of above ground structural litter
unit                                                               
variable_type                                                      
axis               []                                              
initialised_by     None                                            
required_init_by   ['litter']                                      
updated_by         ['litter']                                      
required_update_by []                                              
================== ================================================

38- lignin_below_structural
===========================

================== ================================================
name               lignin_below_structural                         
description        Lignin content of above ground structural litter
unit                                                               
variable_type                                                      
axis               []                                              
initialised_by     None                                            
required_init_by   ['litter']                                      
updated_by         ['litter']                                      
required_update_by []                                              
================== ================================================

39- lignin_woody
================

================== ==============================
name               lignin_woody                  
description        Lignin content of woody litter
unit                                             
variable_type                                    
axis               []                            
initialised_by     None                          
required_init_by   ['litter']                    
updated_by         ['litter']                    
required_update_by []                            
================== ==============================

40- litter_C_mineralisation_rate
================================

================== ===========================================
name               litter_C_mineralisation_rate               
description        Rate of carbon addition to soil from litter
unit               kg C m^-3 day^-1                           
variable_type                                                 
axis               []                                         
initialised_by     None                                       
required_init_by   []                                         
updated_by         ['litter']                                 
required_update_by []                                         
================== ===========================================

41- litter_pool_above_metabolic
===============================

================== ==================================
name               litter_pool_above_metabolic       
description        Above ground metabolic litter pool
unit               kg C m^-2                         
variable_type                                        
axis               []                                
initialised_by     None                              
required_init_by   ['litter']                        
updated_by         ['litter']                        
required_update_by []                                
================== ==================================

42- litter_pool_above_structural
================================

================== ===================================
name               litter_pool_above_structural       
description        Above ground structural litter pool
unit               kg C m^-2                          
variable_type                                         
axis               []                                 
initialised_by     None                               
required_init_by   ['litter']                         
updated_by         ['litter']                         
required_update_by []                                 
================== ===================================

43- litter_pool_below_metabolic
===============================

================== ==================================
name               litter_pool_below_metabolic       
description        Below ground metabolic litter pool
unit               kg C m^-2                         
variable_type                                        
axis               []                                
initialised_by     None                              
required_init_by   ['litter']                        
updated_by         ['litter']                        
required_update_by []                                
================== ==================================

44- litter_pool_below_structural
================================

================== ===================================
name               litter_pool_below_structural       
description        Below ground structural litter pool
unit               kg C m^-2                          
variable_type                                         
axis               []                                 
initialised_by     None                               
required_init_by   ['litter']                         
updated_by         ['litter']                         
required_update_by []                                 
================== ===================================

45- litter_pool_woody
=====================

================== =================
name               litter_pool_woody
description        Woody litter pool
unit               kg C m^-2        
variable_type                       
axis               []               
initialised_by     None             
required_init_by   ['litter']       
updated_by         ['litter']       
required_update_by []               
================== =================

46- longwave_canopy
===================

================== ================================================
name               longwave_canopy                                 
description        Longwave radiation from individual canopy layers
unit               J m-2                                           
variable_type                                                      
axis               []                                              
initialised_by     None                                            
required_init_by   []                                              
updated_by         []                                              
required_update_by []                                              
================== ================================================

47- longwave_soil
=================

================== =====================================
name               longwave_soil                        
description        Longwave radiation from surface layer
unit               J m-2                                
variable_type                                           
axis               []                                   
initialised_by     None                                 
required_init_by   []                                   
updated_by         []                                   
required_update_by []                                   
================== =====================================

48- matric_potential
====================

================== ================
name               matric_potential
description        Matric potential
unit                               
variable_type                      
axis               []              
initialised_by     None            
required_init_by   []              
updated_by         ['hydrology']   
required_update_by []              
================== ================

49- mean_annual_temperature
===========================

================== ===========================================================
name               mean_annual_temperature                                    
description        Mean annual temperature = temperature of deepest soil layer
unit               C                                                          
variable_type                                                                 
axis               []                                                         
initialised_by     None                                                       
required_init_by   []                                                         
updated_by         []                                                         
required_update_by []                                                         
================== ===========================================================

50- molar_density_air
=====================

================== ==========================================
name               molar_density_air                         
description        Temperature-dependent molar density of air
unit               kg m-3                                    
variable_type                                                
axis               []                                        
initialised_by     None                                      
required_init_by   []                                        
updated_by         ['hydrology']                             
required_update_by []                                        
================== ==========================================

51- netradiation_surface
========================

================== ======================================
name               netradiation_surface                  
description        Net shortwave radiation at the surface
unit               J m-2                                 
variable_type                                            
axis               []                                    
initialised_by     None                                  
required_init_by   []                                    
updated_by         []                                    
required_update_by []                                    
================== ======================================

52- pH
======

================== ========
name               pH      
description        Soil pH 
unit               pH      
variable_type              
axis               []      
initialised_by     None    
required_init_by   ['soil']
updated_by         []      
required_update_by []      
================== ========

53- photosynthetic_photon_flux_density
======================================

================== ==================================
name               photosynthetic_photon_flux_density
description        Photosynthetic photon flux density
unit                                                 
variable_type                                        
axis               []                                
initialised_by     None                              
required_init_by   ['plants']                        
updated_by         []                                
required_update_by []                                
================== ==================================

54- plant_cohorts_cell_id
=========================

================== ========================
name               plant_cohorts_cell_id   
description        Cell ID of plant cohorts
unit                                       
variable_type                              
axis               []                      
initialised_by     None                    
required_init_by   ['plants']              
updated_by         []                      
required_update_by []                      
================== ========================

55- plant_cohorts_dbh
=====================

================== ==========================================
name               plant_cohorts_dbh                         
description        Diameter at breast height of plant cohorts
unit                                                         
variable_type                                                
axis               []                                        
initialised_by     None                                      
required_init_by   ['plants']                                
updated_by         []                                        
required_update_by []                                        
================== ==========================================

56- plant_cohorts_n
===================

================== =======================
name               plant_cohorts_n        
description        Number of plant cohorts
unit                                      
variable_type                             
axis               []                     
initialised_by     None                   
required_init_by   ['plants']             
updated_by         []                     
required_update_by []                     
================== =======================

57- plant_cohorts_pft
=====================

================== ======================================
name               plant_cohorts_pft                     
description        Plant functional type of plant cohorts
unit                                                     
variable_type                                            
axis               []                                    
initialised_by     None                                  
required_init_by   ['plants']                            
updated_by         []                                    
required_update_by []                                    
================== ======================================

58- plant_net_co2_assimilation
==============================

================== ==========================
name               plant_net_co2_assimilation
description        Plant net CO2 assimilation
unit               ppm                       
variable_type                                
axis               []                        
initialised_by     None                      
required_init_by   []                        
updated_by         []                        
required_update_by []                        
================== ==========================

59- ppfd
========

================== ================================================
name               ppfd                                            
description        Top of canopy photosynthetic photon flux density
unit               mol m-2                                         
variable_type                                                      
axis               []                                              
initialised_by     None                                            
required_init_by   []                                              
updated_by         []                                              
required_update_by []                                              
================== ================================================

60- precipitation
=================

================== =============
name               precipitation
description        Precipitation
unit               mm           
variable_type                   
axis               []           
initialised_by     None         
required_init_by   ['hydrology']
updated_by         []           
required_update_by []           
================== =============

61- precipitation_surface
=========================

================== ==================================
name               precipitation_surface             
description        Precipitation that reaches surface
unit               mm                                
variable_type                                        
axis               []                                
initialised_by     None                              
required_init_by   []                                
updated_by         ['hydrology']                     
required_update_by []                                
================== ==================================

62- relative_humidity
=====================

================== =========================
name               relative_humidity        
description        Relative humidity profile
unit               %                        
variable_type                               
axis               []                       
initialised_by     None                     
required_init_by   []                       
updated_by         ['abiotic_simple']       
required_update_by []                       
================== =========================

63- relative_humidity_ref
=========================

================== ==========================================
name               relative_humidity_ref                     
description        Relative humidity at reference height (2m)
unit               %                                         
variable_type                                                
axis               []                                        
initialised_by     None                                      
required_init_by   ['abiotic', 'abiotic_simple', 'hydrology']
updated_by         []                                        
required_update_by []                                        
================== ==========================================

64- river_discharge
===================

================== ===============
name               river_discharge
description        River discharge
unit               m3 s-1         
variable_type                     
axis               []             
initialised_by     None           
required_init_by   []             
updated_by         []             
required_update_by []             
================== ===============

65- river_discharge_rate
========================

================== ====================
name               river_discharge_rate
description        River discharge rate
unit                                   
variable_type                          
axis               []                  
initialised_by     None                
required_init_by   []                  
updated_by         ['hydrology']       
required_update_by []                  
================== ====================

66- roughness_length_momentum
=============================

================== =============================
name               roughness_length_momentum    
description        Roughness length for momentum
unit               m                            
variable_type                                   
axis               []                           
initialised_by     None                         
required_init_by   []                           
updated_by         []                           
required_update_by []                           
================== =============================

67- sensible_heat_flux
======================

================== ==========================================
name               sensible_heat_flux                        
description        Sensible heat flux from canopy and surface
unit               J m-2                                     
variable_type                                                
axis               []                                        
initialised_by     None                                      
required_init_by   []                                        
updated_by         []                                        
required_update_by []                                        
================== ==========================================

68- sensible_heat_flux_canopy
=============================

================== ==============================
name               sensible_heat_flux_canopy     
description        Sensible heat flux from canopy
unit               J m-2                         
variable_type                                    
axis               []                            
initialised_by     None                          
required_init_by   []                            
updated_by         []                            
required_update_by []                            
================== ==============================

69- sensible_heat_flux_soil
===========================

================== =====================================
name               sensible_heat_flux_soil              
description        Sensible heat flux from surface layer
unit               J m-2                                
variable_type                                           
axis               []                                   
initialised_by     None                                 
required_init_by   []                                   
updated_by         []                                   
required_update_by []                                   
================== =====================================

70- shortwave_in
================

================== ============================
name               shortwave_in                
description        Downward shortwave radiation
unit               J m-2                       
variable_type                                  
axis               []                          
initialised_by     None                        
required_init_by   []                          
updated_by         []                          
required_update_by []                          
================== ============================

71- soil_c_pool_lmwc
====================

================== ========================================
name               soil_c_pool_lmwc                        
description        Size of low molecular weight carbon pool
unit               kg C m-3                                
variable_type                                              
axis               []                                      
initialised_by     None                                    
required_init_by   ['soil']                                
updated_by         ['soil']                                
required_update_by []                                      
================== ========================================

72- soil_c_pool_maom
====================

================== ==============================================
name               soil_c_pool_maom                              
description        Size of mineral associated organic matter pool
unit               kg C m-3                                      
variable_type                                                    
axis               []                                            
initialised_by     None                                          
required_init_by   ['soil']                                      
updated_by         ['soil']                                      
required_update_by []                                            
================== ==============================================

73- soil_c_pool_microbe
=======================

================== ==============================
name               soil_c_pool_microbe           
description        Size of microbial biomass pool
unit               kg C m-3                      
variable_type                                    
axis               []                            
initialised_by     None                          
required_init_by   ['soil']                      
updated_by         ['soil']                      
required_update_by []                            
================== ==============================

74- soil_c_pool_pom
===================

================== ==============================
name               soil_c_pool_pom               
description        Size of microbial biomass pool
unit               kg C m-3                      
variable_type                                    
axis               []                            
initialised_by     None                          
required_init_by   ['soil']                      
updated_by         ['soil']                      
required_update_by []                            
================== ==============================

75- soil_enzyme_maom
====================

================== ================
name               soil_enzyme_maom
description        soil_enzyme_maom
unit                               
variable_type                      
axis               []              
initialised_by     None            
required_init_by   []              
updated_by         ['soil']        
required_update_by []              
================== ================

76- soil_enzyme_pom
===================

================== ===============
name               soil_enzyme_pom
description        soil_enzyme_pom
unit                              
variable_type                     
axis               []             
initialised_by     None           
required_init_by   []             
updated_by         ['soil']       
required_update_by []             
================== ===============

77- soil_evaporation
====================

================== ================
name               soil_evaporation
description        Soil evaporation
unit               mm              
variable_type                      
axis               []              
initialised_by     None            
required_init_by   []              
updated_by         ['hydrology']   
required_update_by []              
================== ================

78- soil_moisture
=================

================== ==================================================
name               soil_moisture                                     
description        Soil moisture as volumetric relative water content
unit               -                                                 
variable_type                                                        
axis               []                                                
initialised_by     None                                              
required_init_by   []                                                
updated_by         ['hydrology']                                     
required_update_by []                                                
================== ==================================================

79- soil_respiration
====================

================== ================
name               soil_respiration
description        Soil respiration
unit               ppm             
variable_type                      
axis               []              
initialised_by     None            
required_init_by   []              
updated_by         []              
required_update_by []              
================== ================

80- soil_temperature
====================

================== =============================
name               soil_temperature             
description        Soil temperature profile     
unit               C                            
variable_type                                   
axis               []                           
initialised_by     None                         
required_init_by   []                           
updated_by         ['abiotic', 'abiotic_simple']
required_update_by []                           
================== =============================

81- specific_heat_air
=====================

================== ====================
name               specific_heat_air   
description        Specific heat of air
unit               kJ kg-1             
variable_type                          
axis               []                  
initialised_by     None                
required_init_by   []                  
updated_by         []                  
required_update_by []                  
================== ====================

82- specific_humidity
=====================

================== ========================
name               specific_humidity       
description        Specific humidity of air
unit               g kg-1                  
variable_type                              
axis               []                      
initialised_by     None                    
required_init_by   []                      
updated_by         []                      
required_update_by []                      
================== ========================

83- stream_flow
===============

================== =====================
name               stream_flow          
description        Estimated stream flow
unit               mm per time step     
variable_type                           
axis               []                   
initialised_by     None                 
required_init_by   []                   
updated_by         []                   
required_update_by []                   
================== =====================

84- subsurface_flow
===================

================== ===============
name               subsurface_flow
description        Surface flow   
unit                              
variable_type                     
axis               []             
initialised_by     None           
required_init_by   []             
updated_by         ['hydrology']  
required_update_by []             
================== ===============

85- subsurface_flow_accumulated
===============================

================== ===========================
name               subsurface_flow_accumulated
description        Accumulated subsurface flow
unit                                          
variable_type                                 
axis               []                         
initialised_by     None                       
required_init_by   []                         
updated_by         ['hydrology']              
required_update_by []                         
================== ===========================

86- subsurface_runoff
=====================

================== =================
name               subsurface_runoff
description        Subsurface runoff
unit               mm               
variable_type                       
axis               []               
initialised_by     None             
required_init_by   []               
updated_by         []               
required_update_by []               
================== =================

87- sunshine_fraction
=====================

================== ===========================================
name               sunshine_fraction                          
description        Fraction of sunshine hours, between 0 and 1
unit               -                                          
variable_type                                                 
axis               []                                         
initialised_by     None                                       
required_init_by   []                                         
updated_by         []                                         
required_update_by []                                         
================== ===========================================

88- surface_runoff
==================

================== ==========================================
name               surface_runoff                            
description        Surface runoff generated in each grid cell
unit               mm                                        
variable_type                                                
axis               []                                        
initialised_by     None                                      
required_init_by   []                                        
updated_by         ['hydrology']                             
required_update_by []                                        
================== ==========================================

89- surface_runoff_accumulated
==============================

================== ==========================
name               surface_runoff_accumulated
description        Accumlated surface runoff 
unit               mm                        
variable_type                                
axis               []                        
initialised_by     None                      
required_init_by   []                        
updated_by         ['hydrology']             
required_update_by []                        
================== ==========================

90- surface_water
=================

================== ========================
name               surface_water           
description        Searchable surface water
unit               %                       
variable_type                              
axis               []                      
initialised_by     None                    
required_init_by   []                      
updated_by         []                      
required_update_by []                      
================== ========================

91- topofcanopy_radiation
=========================

================== ==========================================
name               topofcanopy_radiation                     
description        Top of canopy downward shortwave radiation
unit               J m-2                                     
variable_type                                                
axis               []                                        
initialised_by     None                                      
required_init_by   []                                        
updated_by         []                                        
required_update_by []                                        
================== ==========================================

92- total_river_discharge
=========================

================== =====================
name               total_river_discharge
description        Total river discharge
unit                                    
variable_type                           
axis               []                   
initialised_by     None                 
required_init_by   []                   
updated_by         ['hydrology']        
required_update_by []                   
================== =====================

93- vapour_pressure
===================

================== ===============
name               vapour_pressure
description        Vapour pressure
unit                              
variable_type                     
axis               []             
initialised_by     None           
required_init_by   []             
updated_by         ['abiotic']    
required_update_by []             
================== ===============

94- vapour_pressure_deficit
===========================

================== =============================
name               vapour_pressure_deficit      
description        Vapour pressure deficit      
unit                                            
variable_type                                   
axis               []                           
initialised_by     None                         
required_init_by   []                           
updated_by         ['abiotic', 'abiotic_simple']
required_update_by []                           
================== =============================

95- vertical_flow
=================

================== ==========================================
name               vertical_flow                             
description        Vertical flow of water through soil column
unit               mm per time step                          
variable_type                                                
axis               []                                        
initialised_by     None                                      
required_init_by   []                                        
updated_by         ['hydrology']                             
required_update_by []                                        
================== ==========================================

96- wind_above_canopy
=====================

================== =================
name               wind_above_canopy
description        Wind above canopy
unit               m s-1            
variable_type                       
axis               []               
initialised_by     None             
required_init_by   []               
updated_by         []               
required_update_by []               
================== =================

97- wind_below_canopy
=====================

================== ====================================
name               wind_below_canopy                   
description        Wind profile within and below canopy
unit               m s-1                               
variable_type                                          
axis               []                                  
initialised_by     None                                
required_init_by   []                                  
updated_by         []                                  
required_update_by []                                  
================== ====================================

98- wind_speed_ref
==================

================== ====================================
name               wind_speed_ref                      
description        Wind speed at reference height (10m)
unit               m s-1                               
variable_type                                          
axis               []                                  
initialised_by     None                                
required_init_by   ['hydrology']                       
updated_by         []                                  
required_update_by []                                  
================== ====================================
