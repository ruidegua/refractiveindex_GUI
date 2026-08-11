"""Cross-platform smoke tests for refractiveindex_GUI.

Verifies the GUI module imports cleanly on Windows / Linux / macOS,
the bundled `db/` and local `db_extra/` catalogs resolve correctly,
materials (system + local) load, the CSV export logic is sound, and
the v0.5.6 cross-platform patches (classic tk.PanedWindow,
_maximize_window helper) are present and working.

Tests run under `MPLBACKEND=Agg` so they don't need a display.
"""

from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path

# matplotlib.use('Agg') is configured in tests/conftest.py so it runs
# before any test module imports matplotlib. Don't set it here.

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent


# ────────────────────────────────────────────────────────────────
# Import + module structure
# ────────────────────────────────────────────────────────────────
def test_import():
    """nk_GUI module imports without raising on the current platform."""
    import nk_GUI
    assert hasattr(nk_GUI, "NkCurveGUI")
    assert hasattr(nk_GUI, "_load_material_data")


def test_import_does_not_break_pathlib():
    """DB_PATH and LOCAL_DB_PATH are pathlib.Path, not strings."""
    import nk_GUI
    assert isinstance(nk_GUI.DB_PATH, Path)
    assert isinstance(nk_GUI.LOCAL_DB_PATH, Path)


# ────────────────────────────────────────────────────────────────
# Database paths and catalogs
# ────────────────────────────────────────────────────────────────
def test_bundled_db_present():
    """The bundled db/catalog-nk.yml ships with the repo."""
    import nk_GUI
    assert (REPO_ROOT / "db" / "catalog-nk.yml").is_file(), (
        f"missing bundled catalog: {REPO_ROOT/'db/catalog-nk.yml'}"
    )
    assert nk_GUI.DB_PATH.is_dir()


def test_local_db_present():
    """db_extra/ catalog files ship with the repo."""
    import nk_GUI
    assert (REPO_ROOT / "db_extra" / "catalog-pu.yml").is_file()
    assert (REPO_ROOT / "db_extra" / "catalog-sc.yml").is_file()
    assert nk_GUI.LOCAL_DB_PATH.is_dir()


def test_local_catalogs_merged_into_index():
    """The Pu and Sc local shelves appear in INDEX_NK after merge."""
    import nk_GUI
    shelves = {sid for sid, _, _ in nk_GUI.INDEX_NK}
    assert "Pu" in shelves, f"Pu missing from INDEX_NK: {shelves}"
    assert "Sc" in shelves, f"Sc missing from INDEX_NK: {shelves}"


def test_db_source_resolution():
    """Title bar reports which DB is active -- bundled by default."""
    import nk_GUI
    # Default expected behavior: bundled db/ exists in this repo
    assert nk_GUI._DB_SOURCE.startswith("bundled"), (
        f"expected bundled DB, got {nk_GUI._DB_SOURCE!r}"
    )


# ────────────────────────────────────────────────────────────────
# Material loading -- system + local
# ────────────────────────────────────────────────────────────────
def test_load_system_material_si():
    """Si/Aspnes is a canonical system entry from db/."""
    import nk_GUI
    wl, n, k = nk_GUI._load_material_data("main", "Si", "Aspnes")
    assert len(wl) == 800
    assert wl[0] < wl[-1]
    # Si is dielectric with positive n and small k below bandgap
    assert (n > 0).all(), f"non-positive n in Si: {n.min()}"
    assert (k >= 0).all(), f"negative k in Si: {k.min()}"


def test_load_local_pu():
    """Pu/delta-Pu is a local db_extra/ entry (Dinh 2019)."""
    import nk_GUI
    wl, n, k = nk_GUI._load_material_data("Pu", "delta-Pu", "nk-Dinh2019")
    assert len(wl) == 800
    # Pu data is in 435-850 nm range
    assert wl[0] == pytest.approx(435.0, abs=0.5)
    assert wl[-1] == pytest.approx(850.0, abs=0.5)


def test_load_local_sc():
    """Sc/Sc-polycrystalline is a local db_extra/ entry (Sigrist 1987)."""
    import nk_GUI
    wl, n, k = nk_GUI._load_material_data(
        "Sc", "Sc-polycrystalline", "nk-Sigrist-Henke"
    )
    assert len(wl) == 800
    # Sc-Sigrist covers a huge wavelength range (henke.lbl.gov 1.24e-4 to 4.59 um)
    assert wl[0] != wl[-1]


def test_load_local_pu_oxide_48nm():
    """The second Pu-oxide shelf entry (47.95 nm) is also reachable."""
    import nk_GUI
    wl, n, k = nk_GUI._load_material_data("Pu", "Pu-oxide-48nm", "nk-48nm-Dinh2019")
    assert len(wl) == 800
    assert wl[0] < wl[-1]


def test_local_data_paths_resolve():
    """Local material data files actually exist on disk (regression for
    build_sc_db.py writing to db_extra/db/ instead of db_extra/).
    """
    import nk_GUI
    for shelf in ("Pu", "Sc"):
        for key, path in nk_GUI.INDEX_NK.items():
            sid, _, _ = key
            if sid != shelf:
                continue
            assert path.is_file(), (
                f"{key} -> {path} does not exist (catalog points to "
                f"wrong location)"
            )


# ────────────────────────────────────────────────────────────────
# CSV export logic (mirrors nk_GUI._export)
# ────────────────────────────────────────────────────────────────
def test_csv_export_round_trip(tmp_path):
    """CSV export format is stable: 3 cols, sorted ascending, 6 sig digits."""
    import nk_GUI
    import numpy as np
    wl, n, k = nk_GUI._load_material_data("main", "Si", "Aspnes")

    # Mirror the export logic from nk_GUI._export() (we skip filedialog)
    order = np.argsort(wl)
    wl_sorted = wl[order]
    n_sorted = n[order]
    k_sorted = k[order]
    out = tmp_path / "si_aspnes.csv"
    lines = ["wavelength_um,n,k"]
    for wl_nm, ni, ki in zip(wl_sorted, n_sorted, k_sorted):
        lines.append(f"{wl_nm / 1000.0:.6g},{ni:.6g},{ki:.6g}")
    out.write_text("\n".join(lines), encoding="utf-8")

    rows = out.read_text(encoding="utf-8").strip().splitlines()
    assert rows[0] == "wavelength_um,n,k"
    assert len(rows) == 801  # header + 800 points
    first_wl_um = float(rows[1].split(",")[0])
    last_wl_um = float(rows[-1].split(",")[0])
    assert first_wl_um < last_wl_um, "CSV must be sorted ascending"


# ────────────────────────────────────────────────────────────────
# v0.5.7 adaptive window geometry
# ────────────────────────────────────────────────────────────────
def test_geometry_1280x800_explicit():
    """The specific 1280x800 case (ThinkPad X1 Carbon, Surface Pro,
    older MacBook Air, etc.): default 1054x629, minsize 895x534,
    left pane 409 px. Window fits screen with decoration slack and
    the layout is not cramped.
    """
    import nk_GUI
    w, h, min_w, min_h = nk_GUI._compute_geometry(1280, 800)
    assert w == 1054, f"default_w: got {w}, expected 1054"
    assert h == 629, f"default_h: got {h}, expected 629"
    assert min_w == 895, f"minsize_w: got {min_w}, expected 895"
    assert min_h == 534, f"minsize_h: got {min_h}, expected 534"
    # Fits screen with slack
    assert w <= 1280 - 40
    assert h <= 800 - 60
    # Minsize is reachable
    assert min_w <= w
    assert min_h <= h
    # Left pane + sash + right minsize fits in minsize width
    left_w = nk_GUI._left_panel_width(1280)
    assert left_w == 409, f"left_w: got {left_w}, expected 409"
    assert left_w + 4 + 400 <= min_w  # 400 = right pane minsize


def test_geometry_1920x1080_capped():
    """Full-HD desktop: default stays in the 1800x1100 envelope so the
    window doesn't sprawl, left pane keeps the historical 430."""
    import nk_GUI
    w, h, _, _ = nk_GUI._compute_geometry(1920, 1080)
    assert w <= 1800
    assert h <= 1100
    assert w <= 1920 - 40
    assert h <= 1080 - 60
    assert nk_GUI._left_panel_width(1920) == 430


def test_geometry_1024x600_small_screen():
    """Tiny laptop / netbook: default shrinks to 836x500, left pane to
    327 px so the right pane keeps room for the plots."""
    import nk_GUI
    w, h, _, _ = nk_GUI._compute_geometry(1024, 600)
    assert w >= 720
    assert h >= 500
    assert w <= 1024 - 40
    assert h <= 600 - 60
    assert nk_GUI._left_panel_width(1024) == 327


def test_geometry_4k_capped_at_max():
    """4K display: capped at the 1800x1100 envelope."""
    import nk_GUI
    w, h, _, _ = nk_GUI._compute_geometry(3840, 2160)
    assert w == 1800
    assert h == 1100


def test_geometry_invariant_fits_screen():
    """For a sweep of common screen sizes, default fits the usable area
    and the layout (left + sash + right minsize 400) fits in minsize.
    """
    import nk_GUI
    for sw, sh in [(800, 500), (1024, 600), (1280, 800), (1366, 768),
                   (1440, 900), (1680, 1050), (1920, 1080), (2560, 1440),
                   (3840, 2160)]:
        w, h, min_w, min_h = nk_GUI._compute_geometry(sw, sh)
        assert w <= sw - 40, f"{w} > {sw}-40 at {sw}x{sh}"
        assert h <= sh - 60, f"{h} > {sh}-60 at {sw}x{sh}"
        assert min_w <= w, f"minsize_w {min_w} > default {w} at {sw}x{sh}"
        assert min_h <= h, f"minsize_h {min_h} > default {h} at {sw}x{sh}"
        left_w = nk_GUI._left_panel_width(sw)
        assert left_w + 4 + 400 <= min_w + 1, (
            f"layout overflow: left {left_w} + 4 + 400 = {left_w+4+400} "
            f"> minsize_w {min_w} at {sw}x{sh}"
        )


def test_left_panel_width_normal_screen():
    """On 1280+ wide screens, left panel is in the [280, 430] range."""
    import nk_GUI
    for sw in (1280, 1366, 1440, 1680, 1920, 2560, 3840):
        w = nk_GUI._left_panel_width(sw)
        assert 280 <= w <= 430, f"left_w {w} out of range at sw={sw}"


def test_left_panel_width_floor():
    """On very narrow screens, left panel stays at the 280 px floor."""
    import nk_GUI
    for sw in (640, 720, 800, 875):
        assert nk_GUI._left_panel_width(sw) == 280


# ────────────────────────────────────────────────────────────────
# v0.5.6 cross-platform patches
# ────────────────────────────────────────────────────────────────
def test_maximize_helper_has_platform_branches():
    """The helper must explicitly handle the three known problem cases:
    win32, darwin, and the generic linux branch. Source inspection --
    no Tk root needed (so this test never trips the Windows
    tk.Tk() reuse bug described below).
    """
    import nk_GUI
    import inspect

    src = inspect.getsource(nk_GUI._maximize_window)
    assert 'sys.platform == "win32"' in src, "win32 branch missing"
    assert 'sys.platform == "darwin"' in src, "darwin branch missing"
    # The linux fallback path -- check for the geometry() fallback
    assert "geometry" in src, "geometry fallback missing"


def test_gui_features_combined():
    """Combined GUI test -- single Tk root for all GUI-touching checks.

    Why one test for four assertions: on Windows CI runners, creating
    and destroying multiple `tk.Tk()` roots in the same Python process
    can leave the Tcl interpreter in a state where the next `tk.Tk()`
    raises `TclError: couldn't read auto.tcl`. This is a Tk / Tcl issue,
    not our code. macOS and Linux runners tolerate it fine. Solution:
    do every Tk-touching assertion inside a single Tk root, in one test
    function. Source-inspection-only assertions (PanedWindow class,
    maximize helper branches) go in separate tests that don't touch Tk.
    """
    import nk_GUI

    root = tk.Tk()
    try:
        # (1) Build the full GUI widget tree -- exercises PanedWindow,
        # tree, plots, all ttk widgets. Catches regressions in
        # NkCurveGUI.__init__ on every platform.
        NkCurveGUI = nk_GUI.NkCurveGUI  # noqa: N806
        app = NkCurveGUI(root)
        root.update_idletasks()

        # (2) PanedWindow must be classic tk.PanedWindow (not ttk).
        # ttk.PanedWindow's widget class is 'TPanedwindow';
        # tk.PanedWindow's is 'Panedwindow'.
        def find_panewindow(widget):
            if widget.winfo_class() in ("Panedwindow", "TPanedwindow"):
                return widget
            for child in widget.winfo_children():
                result = find_panewindow(child)
                if result is not None:
                    return result
            return None

        pw = find_panewindow(root)
        assert pw is not None, "PanedWindow not found in widget tree"
        assert pw.winfo_class() == "Panedwindow", (
            f"expected classic tk.PanedWindow (class 'Panedwindow'), got "
            f"{pw.winfo_class()!r} -- ttk.PanedWindow is in use and sash "
            f"drag will lag on macOS"
        )

        # Left pane must be fixed-ish width (width=430 hint); right
        # pane stretches to fill the rest of the window.
        panes = [root.nametowidget(str(p)) for p in pw.panes()]
        assert len(panes) == 2
        assert pw.paneconfig(panes[0], "stretch")[4] == "never"
        assert pw.paneconfig(panes[1], "stretch")[4] == "always"

        # Left pane width should now come from _left_panel_width, not
        # the hard-coded 430 -- verify it's at least 280 and <= 430.
        left_pane = panes[0]
        actual_left_w = pw.paneconfig(left_pane, "width")[4]
        if isinstance(actual_left_w, str):
            actual_left_w = int(actual_left_w)
        assert 280 <= actual_left_w <= 430, (
            f"left pane width {actual_left_w} outside [280, 430]"
        )

        # (3) _maximize_window must be callable on the current platform
        # without raising. On macOS it's a no-op; on win32/linux it
        # does its thing.
        nk_GUI._maximize_window(root)
        root.update_idletasks()

        # (4) Material load -- exercises the data path end-to-end.
        app._load("main", "Si", "Aspnes")
        assert app.wavelengths is not None
        assert app.n_vals is not None
        assert app.k_vals is not None
        # Query path also works
        from scipy.interpolate import interp1d  # noqa: F401  # sanity
        assert float(app._interp_n(500.0)) > 0
    finally:
        root.destroy()


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))