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
from dataclasses import dataclass, field

# Import Matplotlib to avoid this message in notebooks:
# "Matplotlib is building the font cache; this may take a moment."
import matplotlib.pyplot  # noqa: F401
import sphinxcontrib.bibtex.plugin
from sphinxcontrib.bibtex.style.referencing import BracketStyle
from sphinxcontrib.bibtex.style.referencing.author_year import AuthorYearReferenceStyle

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

# Add path to folder containing custom extensions
sys.path.append(os.path.abspath("./_ext"))

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
    "sphinx.ext.intersphinx",
    "sphinx.ext.mathjax",
    "sphinx.ext.autosummary",
    # "sphinx.ext.autosectionlabel",  # Generates hard to trace exception
    "sphinxcontrib.bibtex",
    "sphinxcontrib.mermaid",
    "myst_nb",
    "sphinx_rtd_theme",
    "autodoc_constants_registry",
]
autodoc_default_flags = ["members"]
autosummary_generate = True


def bracket_style() -> BracketStyle:
    """Function that defines round brackets citation style."""
    return BracketStyle(
        left="(",
        right=")",
    )


@dataclass
class MyReferenceStyle(AuthorYearReferenceStyle):
    """Dataclass that allows new bracket style to be passed to the constructor."""

    bracket_parenthetical: BracketStyle = field(default_factory=bracket_style)
    bracket_textual: BracketStyle = field(default_factory=bracket_style)
    bracket_author: BracketStyle = field(default_factory=bracket_style)
    bracket_label: BracketStyle = field(default_factory=bracket_style)
    bracket_year: BracketStyle = field(default_factory=bracket_style)


sphinxcontrib.bibtex.plugin.register_plugin(
    "sphinxcontrib.bibtex.style.referencing", "author_year_round", MyReferenceStyle
)

# Configure referencing style
bibtex_reference_style = "author_year_round"

# Reference checking
nitpicky = True
nitpick_ignore = [
    ("py:class", "jsonschema.validators.Draft202012Validator"),
    ("py:class", "numpy.int64"),
    ("py:class", "numpy.float32"),
    # TODO - Delete this once Vivienne has merged this feature into develop
    ("py:class", "virtual_rainforest.models.abiotic.energy_balance.EnergyBalance"),
]
intersphinx_mapping = {
    "numpy": ("https://numpy.org/doc/stable/", None),
    "python": ("https://docs.python.org/3/", None),
    "xarray": ("https://docs.xarray.dev/en/stable/", None),
    "shapely": ("https://shapely.readthedocs.io/en/stable/", None),
    "jsonschema": ("https://python-jsonschema.readthedocs.io/en/stable/", None),
    # TODO - This is pinned to a particular pint version as the package is making
    # changes to how it handles typing, at some point it should be unpinned, i.e. set to
    # stable
    "pint": ("https://pint.readthedocs.io/en/0.21/", None),
}


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
