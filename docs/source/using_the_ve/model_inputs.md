---
jupytext:
  formats: md:myst
  main_language: python
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.17.3
kernelspec:
  display_name: Python 3 (ipykernel)
  language: python
  name: python3
language_info:
  codemirror_mode:
    name: ipython
    version: 3
  file_extension: .py
  mimetype: text/x-python
  name: python
  nbconvert_exporter: python
  pygments_lexer: ipython3
  version: 3.11.9
---

# Model inputs

```{warning}

This is draft text

```

There are basically four ways to get inputs into models:

1. **Model configuration values**

    These are values that are set in the model configuration TOML files. An example
    would be the maximum number of canopy layers in the  simulation.

    *Format*: entries in a TOML configuration file.

    *Validation*: Currently these values have some simple validation because loading
    TOML does this automatically - it is really just that numbers are numbers and
    strings are strings, but the VE model code should then have more sophisticated value
    checking (for example that a file path exists or that a number isn't negative).

    *Documentation*: Essentially no systematic documentation. Users *can* read the model
    schemas to found out names and types but that is not acceptable for most users and
    so we need actual human readable descriptions of the model schema with example
    inputs. We do provide examples in the `example_data` but it needs linking in,
    probably at the top of the model implementation pages.

    *Output*: These are fixed in the configuration - they don't output.

2. **Model constants**

    These are per model sets of values, generally things that take a single value that
    is held constant across the whole simulation, but potentially something slightly
    more complex (sets of coefficients). An example would be the `wind_reference_height`
    in the `abiotic` model.

    In some ways (potentially very many ways) these are like a concealed set of model
    configuration values and we possibly (probably?) (certainly?) should long-term move
    integrate these.

    *Format*: This is not well documented but model constants are configured through the
    model TOML configuration file. The problem here is that the structure of the TOML
    required for constants is *not* included in the `model_schema.json`: the names and
    types of constants are simply not there.

    *Validation*: Constant values are handled by the constant loading process - which
    currently only checks for missing or mistyped constant names - and then any further
    value validation (e.g. sign, bounds etc) is down to model specific checking.

    *Documentation*: The constants objects *are* documented but only in the API
    documentation. For example:
    <https://virtual-ecosystem.readthedocs.io/en/latest/api/models/abiotic/abiotic_constants.html>

    *Output*: These are fixed in the configuration- they don't output.

3. **Model data variables**

    This is using the formal sense of variables that go into the central model `Data`
    object. These are data arrays that are structured along one or more of the Virtual
    Ecosystem dimensions and are things like the temperature or litter biomass. At the
    moment have we four critical dimensions within the VE:

    * `spatial`: This is actually a kind of aggregate dimension, because spatial data
      can use `cell_id` or `x` and `y` coordinates - they two things map onto each
      other.
    * `time`: There is some difficulty here - there is a principle time dimension that
      is 1 value per model update in the configuration, but some models (`abiotic`
      principally) may work with faster data.
    * `vertical_layer`: Many variables have vertical structure - principally canopy and
      abiotic data but other variables may occupy some vertical layers. It is not usual
      for input data to require a vertical layer dimension, because the structure is
      defined at model startup by the configuration, but output variables may well have
      this dimension.
    * `pft`: Some data requires values per plant functional type. An example is the
      initial number of propagules per PFT in grid cells.

    *Format*: These data will be loaded through the `core.data.variable` syntax in the
    TOML and will typically be be stored as NetCDF files, providing dimension
    coordinates.

    *Validation*: The dimensions are *supposed* to be checked on loading, but at the
    moment this is only really implemented for `spatial` coordinates (any netcdf
    variable that has a `cell_id` variable or a paired `x` and `y` variable. We don't
    currently check the `time` axis or `pft` axis. The validation of the values is
    currently left up to individual models - we don't currently have a centralised
    bounds checking of these values, although it is something we've discussed.

    *Documentation*: The variables are documented in `data_variables.toml` - which is
    included in the documentation as
    <https://virtual-ecosystem.readthedocs.io/en/latest/virtual_ecosystem/implementation/variables.html>.
    However, the `axis` field in that data is **not to be trusted** - we have not
    systematically reviewed that data and there isn't any internal checking that the
    stated axes are what is on the data.

    *Output*: These variables are written out in NetCDF files with the same axis
    structures as the inputs. The model configuration dictates which variables get
    written out when (just at the end? at each time step?).

4. **Other data**

    Some data goes in by other means and I've lumped these together here:

   * The PFT trait definition file: this is a CSV file of required trait values per PFT.
     The required trait values are not currently documented anywhere except list of
     names in the plant model configuration schema, which is not documentation. The
     validation is inconsistent - some traits are validated through `pyrealm` but VE
     traits can actually be missing or non-numeric.

   * The plant cohort structure: this again can be a CSV file and the structure is
     documented. At the moment this data goes in through the Data object (as in 3.
     above) but actually this is kind of a kludge as it really doesn't use any of the
     core dimensions mentioned above and is only read once from Data. It might be better
     as a separate input CSV file from the plant configuration.

   * Microbial community documentation us very similar to the PFT problem in that the
     parameters associated with microbial groups and soil enzymes are not really
     documented anywhere. They are included in the soil model schema, but there's
     minimal information there, and it's really not readable. The actual values used
     (for the example run) are stored in a toml file, but this file doesn't store any
     details about where these example values have been taken from.
