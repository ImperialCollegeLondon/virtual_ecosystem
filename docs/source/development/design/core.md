# Design notes for the `core` module

## Configuration

### Config file format

We need a system to configure the options used by the VR modules. There are a variety of
file formats for config storage.

The basic requirements are:

- **Human readable**. This rules out JSON, which is really for data serialisation and is
  unpleasant to read.
- **Allows comments**. Again, JSON falls foul of this. There are commented extensions of
  JSON but we've already ruled it out on other grounds.
- **Allows deep nested config**. Essentially, we want a config file to be able to
  specify - for example - `plant.functional_types.max_height`. This rules out INI files
  \- this is kind of a shame because the `configparser` module handles these elegantly,
  but INI files only allow a single level of nesting. We _could_ split up config files
  to ensure only one level is needed but that results in either having to reduce nesting
  or have odd and rather arbitrary sets of files.

At this point, the contenders are really `yaml` and `toml`. The `yaml` format is more
widely used but the complexities of `yaml` mean that it has some unusual behaviour and
security implications - there is a recommended `safe_loader` for example! So, for these
reasons make use of the `toml` file format for configuration of the virtual rainforest.

### Configuration system

The config system should provide a way to:

- load a config file into a dictionary:
  (config\['plant'\]\['functional_types'\]\['max_height'\]
- or possibly something like a dataclass for dotted notation:
  (config.plant.functional_types.max_height)
- validate the config against some kind of template
- It is likely that different configurations may re-use config subsections in different
  combinations, so the config system should be capable of loading configs from
  **multiple** files, so that a complete config can be built up or updated from multiple
  files, rather than having to compile a single monolithic file for each permutation.

### Design

The system should have:

- A `config_loader` function to read a particular file, optionally validating it
  against a matching config template.
- A central `Config` class, which can be built up using `ConfigLoader`.
