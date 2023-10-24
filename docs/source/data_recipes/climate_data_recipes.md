# Climate data recipes

This section provides examples for climate data downloading and simple pre-processing.

The [Copernicus climate data store](./CDS_toolbox_template.md) section contains a list
of recommended data sets to run the Virtual Rainforest and describes how to download
climate data from the Copernicus
[Climate Data Store](https://cds.climate.copernicus.eu/) (CDS)
and basic pre-processing options using the
[CDS toolbox](https://cds.climate.copernicus.eu/cdsapp#!/toolbox).

```{note}
At present, the pre-processing does not include scaling or topographic adjustment.
```

This [code example](../../../virtual_rainforest/example_data/climate_dummy.py)
illustrates how to perform simple manipulations to adjust ERA5-Land data to use in the
Virtual Rainforest. This includes reading climate data from NetCDF, converting
the data into an input formate that is suitable for the abiotic module (e.g. Kelvin to
Celsius conversion), adding further required variables, and writing the output in a new
netcdf file. This does also not include scaling or topographic adjustment.
