---
jupyter:
  jupytext:
    cell_metadata_filter: all,-trusted
    main_language: python
    notebook_metadata_filter: settings,mystnb,language_info,execution
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.19.2
---

# Identifying bugs in the `virtual_ecosystem`

This section is intended to help you if you are running the Virtual Ecosystem without
crashes, but are coming across output values that make no apparent sense. It consists of
two notebooks, originally developed by Lingda Lu, demonstrating the process for
identifying bugs in the simulation based on the output to the
{class}`~virtual_ecosystem.core.data.Data` object. The [first
notebook](./litter_validation.ipynb) shows the process of identifying the bug. The
[second notebook](./litter_validation_fixed.ipynb) shows the process of verifying that
the bug has been fixed.
