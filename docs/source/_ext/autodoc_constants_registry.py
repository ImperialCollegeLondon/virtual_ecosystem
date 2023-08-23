"""Script defining a custom autodoc directive to document the constants registry."""

from docutils import nodes
from docutils.parsers.rst import Directive
from sphinx.application import Sphinx

from virtual_rainforest.core.constants import CONSTANTS_REGISTRY


def setup(app: Sphinx) -> None:
    """Setup the sphinx app to include our custom directive."""
    app.add_directive("autodoc_constants_registry", AutoDocConstantsRegistry)


class AutoDocConstantsRegistry(Directive):
    """Directive to allow the constants registry to be converted to sensible rst."""

    has_content = True

    def run(self) -> list[str]:
        """TODO - Work out what the docstring should be here."""
        content = []

        for model_name, classes_dict in CONSTANTS_REGISTRY.items():
            for class_name in classes_dict.keys():
                class_rst = generate_constants_class_rst(model_name, class_name)
                content.extend(class_rst)

        return content


def generate_constants_class_rst(model_name: str, class_name: str) -> list[str]:
    """Generate rst appropriate to document each constants class.

    TODO - Add description of arguments, and returns
    """

    rst_nodes = []

    # Add a title for the class
    class_title = nodes.title(text=f"{model_name}: {class_name}")
    rst_nodes.append(class_title)

    return rst_nodes
