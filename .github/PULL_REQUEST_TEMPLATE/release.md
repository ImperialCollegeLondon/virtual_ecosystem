# Description

This is a template to make a PR to make the changes to `develop` needed to make a new
release. We would recommend adding a brief description here of why a new release is
warranted. You must ensure that you have done the following things for a new release to
be possible

## Key checklist

- [ ] Incremented the model version (using `poetry version`)
- [ ] All continuous integration tests pass (these run automatically as part of this PR)
- [ ] `ve_run` runs successfully with the example data
- [ ] The Jupyter notebooks in the documentation are up to date (this can be done by
  navigating to `docs/source` and running `update_notebooks.sh`)
