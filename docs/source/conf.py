"""Configuration file for the Sphinx documentation builder.

This file only contains a selection of the most common options. For a full
list see the documentation:
https://www.sphinx-doc.org/en/master/usage/configuration.html

-- Path setup --------------------------------------------------------------

If extensions (or modules to document with autodoc) are in another directory,
add these directories to sys.path here. If the directory is relative to the
documentation root, use os.path.abspath to make it absolute, like shown here.
"""

import datetime
import sys
import warnings
from dataclasses import dataclass, field
from pathlib import Path

# Import Matplotlib to avoid this message in notebooks:
# "Matplotlib is building the font cache; this may take a moment."
import matplotlib.pyplot  # noqa: F401
import sphinxcontrib.bibtex.plugin
from sphinx.deprecation import RemovedInSphinx90Warning
from sphinxcontrib.bibtex.style.referencing import BracketStyle
from sphinxcontrib.bibtex.style.referencing.author_year import AuthorYearReferenceStyle

import virtual_ecosystem as ve
from virtual_ecosystem.core import variables

# Silence sphinx 9 warnings.
warnings.filterwarnings("ignore", category=RemovedInSphinx90Warning)

# This path is required for automodule to be able to find and render the docstring
# example in the development section of the documentation. The path to the modules for
# the virtual_ecosystem package itself do not needed to be included here, providing
# sphinx is run within the poetry shell. RTD runs sphinx-build in the same directory
# as this conf.py file, where we currently run it from the parent `docs` folder, so
# adding an absolute path is more reliable.
sys.path.append(str(Path(__file__).parent / "development/documentation"))


version = ve.__version__
release = version

# Update the variables file
varfile = Path(__file__).parent / "variables.rst"
variables.output_known_variables(varfile)


# -- Project information -----------------------------------------------------
# Ideally the copyright would have a link to the team page, but neither an RST link, nor
# an HTML <a> link works - they just get rendered as is.

project = "Virtual Ecosystem"
copyright = f"{datetime.date.today().year}, The Virtual Ecosystem project team"
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
    "sphinx.ext.viewcode",
    "sphinx.ext.todo",
    "sphinxcontrib.bibtex",
    "sphinxcontrib.mermaid",
    "myst_nb",
    "sphinx_rtd_theme",
    "sphinx_external_toc",
    "sphinx_design",
    "hoverxref.extension",
]
autodoc_default_flags = ["members"]
autosummary_generate = True

# autodoc_typehints = "description"
autodoc_typehints_format = "short"
python_use_unqualified_type_names = True
# autodoc_type_aliases = {
#   "FILEPATH_PLACEHOLDER": "virtual_ecosystem.core.configuration.FILEPATH_PLACEHOLDER",
# }


# Set up the external table of contents file path and configure
external_toc_path = "_toc.yaml"
external_toc_exclude_missing = False

# Display TODO lists:
todo_include_todos = True


# Set up a bracketed citation style, register it with sphinxcontrib.bibtex, and then set
# that style as the default.
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

bibtex_reference_style = "author_year_round"

# Turn on nitpicky reference checking to ensure that all internal links and intersphinx
# links are resolvable. Then ignore a whole bunch of annoying broken links.
nitpicky = True
nitpick_ignore = [
    # Numpy references aren't always found
    ("py:class", "NDArray"),
    ("py:class", "numpy.int64"),
    ("py:class", "numpy.float32"),
    ("py:class", "numpy.float64"),
    ("py:class", "numpy.bool_"),
    ("py:class", "np.int_"),
    ("py:class", "np.str_"),
    ("py:class", "np.bool_"),
    ("py:class", "np.floating"),
    ("py:class", "np.float64"),
    ("py:class", "np.datetime64"),
    ("py:class", "np.ndarray"),
    ("py:class", "np.timedelta64"),
    ("py:class", "timedelta64"),
    ("py:class", "InitVar"),
    ("py:class", "dataclasses.InitVar"),
    ("py:class", "Quantity"),
    ("py:class", "numpy._typing._array_like._ScalarType_co"),
    ("py:class", "numpy._typing._array_like._ScalarT"),
    ("py:class", "xr.DataArray"),
    # God only knows why this is needed. We don't refer to pint.util.Quantity and it
    # isn't in the pint objects.inv, so why the hell is intersphinx trying to build
    # references to it.
    ("py:class", "pint.util.Quantity"),
    # Something off about JSONSchema intersphinx mapping?
    ("py:obj", "virtual_ecosystem.core.schema.ValidatorWithDefaults.ID_OF"),
    # HACK - sphinx seems to thing GRID_STRUCTURE_SIG is a tuple not a type alias
    ("py:obj", "virtual_ecosystem.core.grid.GRID_STRUCTURE_SIG.__repr__"),
    ("py:obj", "virtual_ecosystem.core.grid.GRID_STRUCTURE_SIG.count"),
    ("py:obj", "virtual_ecosystem.core.grid.GRID_STRUCTURE_SIG.index"),
    ("py:exc", "ParserError"),
    ("py:exc", "BadZipFile"),
    # Absolutely mystifying sphinx failure to link to pyrealm objects in plants_model.py
    # when it resolves those objects without issue in other plants model modules.
    ("py:class", "PModel"),
    ("py:class", "Canopy"),
    ("py:class", "Flora"),
    ("py:class", "PModelConst"),
    ("py:class", "CoreConst"),
    ("py:class", "StemAllocation"),
    ("py:class", "StemStoichiometry"),
    ("py:class", "pydantic.types.PathType"),
    # Something about the pydantic annotated pattern generates a ton of peculiar
    # intersphinx noise.
    ("py:class", "pathlib.Annotated"),
    ("py:class", "path_type=file"),
    ("py:class", "file"),
    ("py:class", "FieldInfo"),
    ("py:class", "NoneType"),
    ("py:class", "PosixPath"),
    ("py:class", "virtual_ecosystem.core.configuration.placeholder_validator"),
    ("py:class", "PydanticUndefined"),
    # Actually just generally intersphinx is janky when it comes to pydantic
    ("py:class", "annotated_types.Gt"),
    ("py:class", "PositiveFloat"),
    ("py:class", "PositiveInt"),
    ("py:class", "annotated_types.Lt"),
    ("py:class", "annotated_types.MinLen"),
    ("py:class", "annotated_types.Gt"),
    ("py:class", "annotated_types.Ge"),
    ("py:class", "annotated_types.Le"),
    ("py:class", "annotated_types.Ge"),
    ("py:class", "annotated_types.Le"),
    ("py:class", "NegativeFloat"),
    ("py:class", "date"),
    ("py:class", "_PydanticGeneralMetadata"),
    # Sphinx seems to insist that pydantic model types are classes, when they can be
    # global Literals
    ("py:class", "SUBSTRATES"),
    ("py:class", "REQUIRED_MICROBIAL_GROUPS"),
    ("py:class", "HIGHER_TAXONOMIC_GROUPS"),
    ("py:class", "dir"),
    # FOR PITY'S SAKE, SPHINX - why can you not find DIRPATH_PLACEHOLDER when you _can_
    # find FILEPATH_PLACEHOLDER, which is defined in the same way, in the same file and
    # when both do actually appear in the API docs? It's right there.
    ("py:class", "DIRPATH_PLACEHOLDER"),
    ("py:class", "PyrealmCoreConst"),
    # Typing on animal.model_config
    ("py:class", "virtual_ecosystem.models.animal.animal_traits.Annotated"),
    ("py:class", "virtual_ecosystem.models.animal.model_config.serialise_diet_type"),
    ("py:class", "virtual_ecosystem.models.animal.model_config.deserialise_diet_type"),
    ("py:class", "always"),
    # This broke when pandas upgraded to 3.0. We should review this once we've upgraded
    # to that major version
    ("py:class", "pandas.core.frame.DataFrame"),
]

intersphinx_mapping = {
    "numpy": ("https://numpy.org/doc/stable/", None),
    "python": ("https://docs.python.org/3/", None),
    "xarray": ("https://docs.xarray.dev/en/stable/", None),
    "shapely": ("https://shapely.readthedocs.io/en/stable/", None),
    "jsonschema": ("https://python-jsonschema.readthedocs.io/en/stable/", None),
    "pint": ("https://pint.readthedocs.io/en/stable/", None),
    "pyrealm": ("https://pyrealm.readthedocs.io/en/stable/", None),
    "pandas": ("http://pandas.pydata.org/pandas-docs/stable/", None),
    "pydantic": ("https://docs.pydantic.dev/latest/", None),
}

# Turn on figure numbering - this slows down build time a surprising amount!
numfig = True

# Set auto labelling to section level
autosectionlabel_prefix_document = True
autosectionlabel_maxdepth = 2

# Myst configuration
myst_enable_extensions = ["dollarmath", "deflist", "colon_fence"]
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

# master_doc = "index"

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.

html_theme = "sphinx_rtd_theme"  # 'sphinx_material'

html_theme_options = {
    "logo_only": False,
    "version_selector": True,
    "prev_next_buttons_location": "top",
    "style_external_links": False,
    "style_nav_header_background": "grey",
    # Toc options
    "collapse_navigation": False,
    "sticky_navigation": True,
    "navigation_depth": 4,
    "includehidden": True,
    "titles_only": False,
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

# These paths are relative to html_static_path
html_css_files = [
    "css/custom.css",
]

html_sidebars = {
    "**": ["logo-text.html", "globaltoc.html", "localtoc.html", "searchbox.html"]
}

# Configure hoverxref
hoverxref_roles = ["term"]

hoverxref_role_types = {"term": "tooltip"}

# Allow for longer runtime
nb_execution_mode = "force"
nb_execution_timeout = 300
