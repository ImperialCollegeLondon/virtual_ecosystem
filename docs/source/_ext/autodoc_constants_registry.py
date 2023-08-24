"""Script defining a custom autodoc directive to document the constants registry."""

from typing import Any

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
        classes_dict = get_classes_from_registry()
        content = []

        for class_name, class_obj in classes_dict.items():
            class_rst = generate_constants_class_rst(class_name, class_obj)
            content.extend(class_rst)

        return content


def generate_constants_class_rst(class_name: str, class_obj: Any) -> list[str]:
    """Generate rst appropriate to document each constants class.

    TODO - Add description of arguments, and returns
    """

    rst_nodes = []

    # Add a title for the class
    class_subtitle = nodes.subtitle(text=class_name)
    rst_nodes.append(class_subtitle)

    return rst_nodes


def get_classes_from_registry() -> dict[str, Any]:
    """TODO - Add a sensible docstring here."""

    flattened_class = {}

    for model_name in CONSTANTS_REGISTRY:
        for class_name in CONSTANTS_REGISTRY[model_name]:
            flattened_class.update(
                {class_name: CONSTANTS_REGISTRY[model_name][class_name]}
            )

    return flattened_class
