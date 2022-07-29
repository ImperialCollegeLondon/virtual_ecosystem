# Description

Please include a summary of the change and which issue is fixed. Please also include relevant motivation and context. List any dependencies that are required for this change.

Fixes # (issue)

## Type of change

Please add a line in the relevant section of [CHANGELOG.md](https://github.com/ImperialCollegeLondon/virtual_rainforest/CHANGELOG.md) to document the change (include PR #) - note reverse order of PR #s. If necessary, also add to the list of breaking changes.

- [ ] New feature (non-breaking change which adds functionality)
- [ ] Optimization (back-end change that speeds up the code)
- [ ] Bug fix (non-breaking change which fixes an issue)


# Key checklist:

- [ ] Make sure you've run the `pre-commit` checks: `$ pre-commit run -a`
- [ ] All tests pass: `$ python run-tests.py --unit`
- [ ] The documentation builds: `$ cd docs` and then `$ make clean; make html`

You can run all three at once, using `$ python run-tests.py --quick`.

## Further checks:

- [ ] Code is commented, particularly in hard-to-understand areas
- [ ] Tests added that prove fix is effective or that feature works
