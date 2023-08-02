#!/usr/bin/env python3
"""This is a wrapper script for invoking qsub with the correct arguments."""
import math
import sys
from os import execvp


def get_runtime_str(runtime_min: int) -> str:
    """Convert the runtime in whole minutes to HH:MM:SS."""
    hours, mins = divmod(runtime_min, 60)
    return f"{hours:02}:{mins:02}:00"


def main(mem_mb: int, runtime_min: int, job_script: str) -> None:
    """The main entry point to this script."""
    # qsub wants memory requirement in whole gigabytes
    mem_gb = max(1, math.ceil(mem_mb / 1000))

    execvp(
        "qsub",
        (
            "qsub",
            f"-lwalltime={get_runtime_str(runtime_min)}",
            f"-lselect=1:ncpus=1:mem={mem_gb}gb",
            job_script,
        ),
    )


if __name__ == "__main__":
    # TODO: Display help if args not given
    assert len(sys.argv) == 4
    main(int(sys.argv[1]), int(sys.argv[2]), sys.argv[-1])
