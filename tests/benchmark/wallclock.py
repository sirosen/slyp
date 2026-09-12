"""
Wall-time benchmarking.

Run via ``tox run -e wallclock``.
"""

import argparse
import inspect
import pathlib
import shutil
import subprocess
import sys
import tempfile
import timeit

CACHE_DIR = ".slyp_cache"


def run(cwd: pathlib.Path, *args: str) -> None:
    subprocess.run(
        [sys.executable, "-m", "slyp", *args],
        cwd=cwd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


def populate_corpus(dir: pathlib.Path) -> None:
    # a somewhat random, but fixed, distribution of stdlib module copies
    for modname, n_copies in (
        ("textwrap", 100),
        ("configparser", 30),
        ("functools", 80),
    ):
        source = inspect.getsource(__import__(modname)).encode()
        for i in range(n_copies):
            # every copy gets a "marker" comment so that they never hash the same
            (dir / f"mod_{i}.py").write_bytes(source + f"\n# {i}\n".encode())


def measure(cwd: pathlib.Path, repeat: int, *args: str, cold: bool) -> float:
    def setup() -> None:
        if cold:
            shutil.rmtree(cwd / CACHE_DIR, ignore_errors=True)
        else:
            run(cwd, *args)

    timer = timeit.Timer(lambda: run(cwd, *args), setup)
    return min(timer.repeat(repeat=repeat, number=1))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-r", "--repeat", type=int, default=5)
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as tmpdir:
        corpus = pathlib.Path(tmpdir)
        populate_corpus(corpus)

        no_cache = measure(corpus, args.repeat, "--no-cache", cold=True)
        cold = measure(corpus, args.repeat, cold=True)
        warm = measure(corpus, args.repeat, cold=False)

    delta_cold = (cold / no_cache) - 1
    delta_warm = (warm / no_cache) - 1

    print()
    print(f"best of {args.repeat}")
    print()
    print(f"no-cache:              {no_cache:8.3f}s")
    print(f"cold-cache (populate)  {cold:8.3f}s  {delta_cold:+7.1%} vs no-cache")
    print(f"warm-cache             {warm:8.3f}s  {delta_warm:+7.1%} vs no-cache")


if __name__ == "__main__":
    main()
