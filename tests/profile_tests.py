#!/usr/bin/env python
"""
Used to find the slowest methods.
"""

import cProfile
import pstats
import io
import pytest   # or unittest if you use that


def main():
    profiler = cProfile.Profile()
    profiler.enable()

    # --- run your tests normally ---
    pytest.main(["tests"])

    profiler.disable()

    # --- output sorted results ---
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats("cumtime")
    ps.print_stats(40)  # top 40 slowest functions
    print(s.getvalue())


if __name__ == "__main__":
    main()
