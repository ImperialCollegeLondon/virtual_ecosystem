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

# Calibrating the Virtual Ecosystem

This section aims to explain what to do if you experience unexpected values in outputs
or crashes from running the Virtual Ecosystem. The best approach to take depends on
exactly what the issue you are running into is:

* if the model runs successfully, but the values it is producing make no sense then we
  would recommend first trying to [identify the bug by plotting the simulation
  output](./calibration/bug_identification.md).
* if the model crashes, but does so in a gracefully manner (i.e. generates easy to read
  log messages rather than a complex exception trace), then the simulation
  log is the first place to look, as it should give specific information about what went
  wrong. Often that may point towards an input that has unexpected values and where
  fixing the inputs will resolve the problem.
* if the steps above don't resolve your issue or the model crash produces an exception
  trace rather than a log message, you will need to [debug the
  model](./calibration/debugging.md) - watch it running and see what variables change
  when and how these might lead to errors.
