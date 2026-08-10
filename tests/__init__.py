"""tests — pytest suite for refractiveindex_GUI.

Smoke tests only: verify the GUI imports, the bundled + local DBs
load, materials can be loaded on all platforms, and the v0.5.6
cross-platform patches (PanedWindow type, maximize helper) are
present.

CI runs these under MPLBACKEND=Agg on a 3 OS x 3 Python matrix
(see .github/workflows/ci.yml). No real Tk window is opened.
"""