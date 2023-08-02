#!/usr/bin/env python3
"""This is a wrapper script for invoking qsub with the correct arguments."""
import math
import sys
from os import execvp


def main(mem_mb: int, job_script: str) -> None:
    """The main entry point to this script."""
    # qsub wants memory requirement in whole gigabytes
    mem_gb = max(1, math.ceil(mem_mb / 1000))

    execvp(
        "qsub",
        (
            "qsub",
            "-lwalltime=00:05:00",
            f"-lselect=1:ncpus=1:mem={mem_gb}gb",
            job_script,
        ),
    )


if __name__ == "__main__":
    # TODO: Display help if args not given
    assert len(sys.argv) == 3
    main(int(sys.argv[1]), sys.argv[2])
