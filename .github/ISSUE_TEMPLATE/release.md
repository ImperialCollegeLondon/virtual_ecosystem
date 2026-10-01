---
name: New release
about: Make a new release of this project
title: ''
labels: ''
assignees: ''

---

**Why is a new release warranted?**
A clear and concise description of why you need to make a new release. Depending on your
release strategy this can be very simple, e.g. "we release weekly, and it is Monday"

**Have you done all the pre-release checks?**

- [ ] Continuous integration tests pass
- [ ] `ve_run` runs successfully with the example data
- [ ] The Jupyter notebooks in the documentation are up to date (navigate to
  `docs/source` and run `update_notebooks.sh`, check if anything changes)

**Things to include in the release pull request.**

- [ ] Fix any problems identified by the checks above
- [ ] Increment the model version (using `poetry version`)
