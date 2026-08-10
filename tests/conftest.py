"""pytest configuration for refractiveindex_GUI smoke tests.

Forces matplotlib to use the Agg backend before any test (or nk_GUI.py)
imports matplotlib. This is critical on Linux CI runners, which don't
have a real display server. Without MPLBACKEND=Agg, the matplotlib
default-backend selection would either fail or grab a Tk display we
don't want.
"""

import os

# Set the env var BEFORE any matplotlib import happens. This must run
# at conftest load time, not at test function time.
os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib

matplotlib.use("Agg")