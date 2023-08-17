"""An integration test for the VR command-line interface."""
import shutil
from contextlib import nullcontext as does_not_raise
from pathlib import Path
from unittest.mock import patch


def test_vr_run(shared_datadir):
    """Test that the CLI can successfully run with example data."""
    from virtual_rainforest.entry_points import vr_run_cli

    args = [
        str(shutil.which("vr_run")),
        "--example",
        "--outpath",
        str(shared_datadir),
        "--merge",
        str(Path(shared_datadir) / "vr_full_model_configuration.toml"),
    ]
    with does_not_raise():
        with patch("virtual_rainforest.entry_points.sys.argv", args):
            vr_run_cli()
