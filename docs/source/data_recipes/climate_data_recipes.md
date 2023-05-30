# Climate data recipes

This section provides examples for climate data downloading and simple pre-processing.

The [Copernicus climate data store](./CDS_toolbox_template.md) section describes how to
download climate data from the Copernicus
[Climate Data Store](https://cds.climate.copernicus.eu/) (CDS)
and basic pre-processing options using the
[CDS toolbox](https://cds.climate.copernicus.eu/cdsapp#!/toolbox).
At present, the pre-processing does not include scaling or topographic adjustment.

The [Create dummy climate data](./ERA5_preprocessing_example.md) section illustrates
how to perform simple manipulations to adjust ERA5 data to use in the Virtual
Rainforest. This includes reading climate data from NetCDF, converting
the data into an input formate that is suitable for the abiotic module (e.g. Kelvin to
Celsius conversion), adding further required variables, and writing the output in a new
netcdf file. This does not include scaling or topographic adjustment.
