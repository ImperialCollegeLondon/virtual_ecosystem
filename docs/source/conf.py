"""Configuration file for the Sphinx documentation builder.

This file only contains a selection of the most common options. For a full
list see the documentation:
https://www.sphinx-doc.org/en/master/usage/configuration.html

-- Path setup --------------------------------------------------------------

If extensions (or modules to document with autodoc) are in another directory,
add these directories to sys.path here. If the directory is relative to the
documentation root, use os.path.abspath to make it absolute, like shown here.
"""

import os
import sys

# Import Matplotlib to avoid this message in notebooks:
# "Matplotlib is building the font cache; this may take a moment."
import matplotlib.pyplot  # noqa: F401

import virtual_rainforest as vr

# This path is required for automodule to be able to find and render the docstring
# example in the development section of the documentation. The path to the modules for
# the virtual_rainforest package itself do not needed to be included here, providing
# sphinx is run within the poetry shell. RTD runs sphinx-build in the same directory
# as this conf.py file, where we currently run it from the parent `docs` folder.

on_rtd = os.environ.get("READTHEDOCS") == "True"
if on_rtd:
    sys.path.append("development/documentation")
else:
    sys.path.append("source/development/documentation")


version = vr.__version__
release = version

# -- Project information -----------------------------------------------------

project = "Virtual Rainforest"
copyright = (
    "2022, Rob Ewers, David Orme, Olivia Daniels, Jacob Cook, "
    "Jaideep Joshi, Taran Rallings, Vivienne Groner"
)
author = (
    "Rob Ewers, David Orme, Olivia Daniels, Jacob Cook, Jaideep Joshi, "
    "Taran Rallings, Vivienne Groner"
)


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "autodocsumm",
    "sphinx.ext.napoleon",
    "sphinx.ext.mathjax",
    "sphinx.ext.autosummary",
    # "sphinx.ext.autosectionlabel",  # Generates hard to trace exception
    "sphinxcontrib.bibtex",
    "myst_nb",
    # "sphinx_astrorefs",  # Gives author year references
    "sphinx_rtd_theme",
]
autodoc_default_flags = ["members"]
autosummary_generate = True

# Set auto labelling to section level
autosectionlabel_prefix_document = True
autosectionlabel_maxdepth = 2

# Myst configuration
myst_enable_extensions = ["dollarmath", "deflist"]
myst_heading_anchors = 3

# Enable mhchem for chemical formulae
mathjax3_config = {
    "tex": {
        "extensions": ["mhchem.js"],
        # 'inlineMath': [['$', '$']]
    }
}

# Turn off ugly rendering of class attributes
napoleon_use_ivar = True

# Suppress signature expansion of arguments
autodoc_preserve_defaults = True

bibtex_bibfiles = ["refs.bib"]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = [
    "development/training/.pytest_cache/*",
]

master_doc = "index"

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.

html_theme = "sphinx_rtd_theme"  # 'sphinx_material'

html_theme_options = {
    "logo_only": False,
    "display_version": True,
    "prev_next_buttons_location": "top",
    "style_external_links": False,
    "style_nav_header_background": "grey",
    # Toc options
    "collapse_navigation": False,
    "sticky_navigation": True,
    "navigation_depth": 0,
    "includehidden": False,
    "titles_only": True,
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

html_sidebars = {
    "**": ["logo-text.html", "globaltoc.html", "localtoc.html", "searchbox.html"]
}
