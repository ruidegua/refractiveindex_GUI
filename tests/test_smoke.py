"""Cross-platform smoke tests for refractiveindex_GUI.

Verifies the GUI module imports cleanly on Windows / Linux / macOS,
the bundled `db/` and local `db_extra/` catalogs resolve correctly,
materials (system + local) load, the CSV export logic is sound, and
the v0.5.6 cross-platform patches (classic tk.PanedWindow,
_maximize_window helper) are present and working.

Tests run under `MPLBACKEND=Agg` so they don't need a display.
"""

from __future__ import annotations

import os

# CRITICAL: set MPLBACKEND before any matplotlib/pyplot import happens
# inside nk_GUI.py or any of the modules it pulls in.
os.environ.setdefault("MPLBACKEND", "Agg")

import sys
import tkinter as tk
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # belt-and-suspenders

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
# v0.5.6 cross-platform patches
# ────────────────────────────────────────────────────────────────
def test_panedwindow_is_classic_tk():
    """The splitter must be classic tk.PanedWindow (not ttk) for
    smooth sash drag on macOS. ttk.PanedWindow's widget class name is
    'TPanedwindow'; tk.PanedWindow's is 'Panedwindow'.
    """
    import nk_GUI
    root = tk.Tk()
    try:
        NkCurveGUI = nk_GUI.NkCurveGUI  # noqa: N806
        app = NkCurveGUI(root)
        root.update_idletasks()

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
            f"{pw.winfo_class()!r} -- this means ttk.PanedWindow is still "
            f"in use and sash drag will lag on macOS"
        )

        # Left pane must be fixed-ish width (width=430 hint)
        panes = [root.nametowidget(str(p)) for p in pw.panes()]
        assert len(panes) == 2
        assert pw.paneconfig(panes[0], "stretch")[4] == "never"
        assert pw.paneconfig(panes[1], "stretch")[4] == "always"
    finally:
        root.destroy()


def test_maximize_helper_exists_and_callable():
    """_maximize_window must be defined and callable without raising,
    on every platform CI runs on (win32 / linux / darwin).
    """
    import nk_GUI
    root = tk.Tk()
    try:
        # Must not raise on the current platform
        nk_GUI._maximize_window(root)
        root.update_idletasks()
    finally:
        root.destroy()


def test_maximize_helper_has_platform_branches():
    """The helper must explicitly handle the three known problem cases:
    win32, darwin, and the generic linux branch.
    """
    import nk_GUI
    import inspect

    src = inspect.getsource(nk_GUI._maximize_window)
    assert 'sys.platform == "win32"' in src, "win32 branch missing"
    assert 'sys.platform == "darwin"' in src, "darwin branch missing"
    # The linux fallback path -- check for the geometry() fallback
    assert "geometry" in src, "geometry fallback missing"


# ────────────────────────────────────────────────────────────────
# Headless run -- verify the whole __main__ flow works without
# crashing (we just build the UI, don't enter mainloop)
# ────────────────────────────────────────────────────────────────
def test_full_gui_build_headless():
    """Build the entire GUI widget tree on a headless Tk root."""
    import nk_GUI
    root = tk.Tk()
    try:
        app = nk_GUI.NkCurveGUI(root)
        root.update_idletasks()
        # Load a material to exercise the data path
        app._load("main", "Si", "Aspnes")
        assert app.wavelengths is not None
        assert app.n_vals is not None
        assert app.k_vals is not None
    finally:
        root.destroy()


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))