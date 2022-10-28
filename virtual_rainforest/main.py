"""TODO - WRITE DOC STRING DESCRIBING MAIN FUNCTION."""

from typing import Union

from virtual_rainforest.core.config import validate_config
from virtual_rainforest.core.logger import LOGGER


def vr_run(
    cfg_paths: Union[str, list[str]], output_folder: str, out_file_name: str
) -> None:
    """TODO - DOCSSTRING FOR FUNCTION."""

    config = validate_config(cfg_paths, output_folder, out_file_name)

    print(config)

    LOGGER.info("Virtual rainforest model run completed!")
