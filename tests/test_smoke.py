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
    assert (REPO_ROOT / "db_extra" / "catalog-ce.yml").is_file()
    assert nk_GUI.LOCAL_DB_PATH.is_dir()


def test_local_catalogs_merged_into_index():
    """The Pu, Sc, CeO2 local shelves appear in INDEX_NK after merge."""
    import nk_GUI
    shelves = {sid for sid, _, _ in nk_GUI.INDEX_NK}
    assert "Pu" in shelves, f"Pu missing from INDEX_NK: {shelves}"
    assert "Sc" in shelves, f"Sc missing from INDEX_NK: {shelves}"
    assert "CeO2" in shelves, f"CeO2 missing from INDEX_NK: {shelves}"


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


def test_load_local_ceo2_marabelli():
    """CeO2/Marabelli-1987 is a local db_extra/ entry (PRB 36, 1238 1987).

    Single crystal CeO2 reflectivity 1 meV-12 eV, Kramers-Kronig -> eps1,
    eps2; converted to n,k via n+ik = sqrt(eps1 + i*eps2). Digitized from
    Marabelli & Wachter PRB 36, 1238 (1987), Figs 2 & 3.

    Sanity checks:
      - 800-point linspace output (loader fills to linspace of wl_range)
      - Wavelength range covers the full ~0.10-285 um (1 meV-12 eV)
      - n peaks in the phonon-mode region (~40-50 um)
      - k >= 0 everywhere (CeO2 is passive, no gain)
      - n, k finite everywhere
    """
    import nk_GUI
    wl, n, k = nk_GUI._load_material_data(
        "CeO2", "Marabelli-1987", "nk-Marabelli-1987"
    )
    assert len(wl) == 800
    # Full range from digitized data: ~100 nm to ~285 um
    assert wl[0] == pytest.approx(100, abs=2)
    assert wl[-1] == pytest.approx(285000, rel=0.02)
    # CeO2 is passive: k >= 0 in physical data. The yml has k clipped to >= 0,
    # but the loader's cubic interp1d can overshoot by ~1e-4 at transitions
    # from clipped zero regions to non-zero values (standard cubic spline
    # overshoot, well-known artifact). Tolerate tiny negative.
    assert (k >= -0.01).all(), f"unexpected negative k in CeO2: min={k.min()}"
    # n peak in phonon-mode region (Fig 3, ~30-50 um = 217-333 cm^-1)
    # Marabelli TO mode ~ 270 cm^-1 ~ 37 um
    peak_idx = n.argmax()
    assert 30000 < wl[peak_idx] < 60000, (
        f"n peak at {wl[peak_idx]:.0f} nm, expected in 30-60 um range"
    )


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
# v0.5.8 small-screen layout fixes (1280x800 Linux Mint bugs)
# ────────────────────────────────────────────────────────────────
def test_left_pane_is_scrollable():
    """v0.5.8 fix for Linux Mint 1280x800: left pane is now wrapped in
    a scrollable Canvas so all controls (including Export CSV at the
    bottom) remain reachable even when the total content height
    exceeds the left pane's visible area.
    """
    import nk_GUI
    import inspect

    # Source check: helper exists
    assert hasattr(nk_GUI, "_make_scrollable"), (
        "_make_scrollable helper missing"
    )

    # Source check: _build_left calls it
    src = inspect.getsource(nk_GUI.NkCurveGUI._build_left)
    assert "_make_scrollable" in src, (
        "_build_left does not call _make_scrollable"
    )


def test_right_pane_uses_grid_layout():
    """v0.5.8 fix for Linux Mint 1280x800: right pane uses grid layout
    with equal row weights so the two plot frames (frame_nk, frame_eps)
    always have the same height regardless of matplotlib's natural-size
    request.
    """
    import nk_GUI
    import inspect

    src = inspect.getsource(nk_GUI.NkCurveGUI._build_right)
    assert "rowconfigure" in src, (
        "_build_right doesn't configure rows"
    )
    assert "weight=1" in src, (
        "_build_right doesn't give equal weight to plot-frame rows"
    )
    assert ".grid(" in src, "_build_right doesn't use grid"
    assert "frame_nk.grid(" in src, "frame_nk not grid'd"
    assert "frame_eps.grid(" in src, "frame_eps not grid'd"


# ────────────────────────────────────────────────────────────────
# v0.5.9 wheel-scroll fix (blank space at top of left panel)
# ────────────────────────────────────────────────────────────────
def test_scrollregion_rooted_at_origin():
    """v0.5.9 fix for blank space at the top of the left panel when
    scrolling: the scrollregion must be explicitly anchored at canvas
    (0, 0). Using `canvas.bbox("all")` directly is not safe because
    bbox can transiently return coordinates with y < 0 during initial
    layout or content reflow. A scrollregion with a negative top lets
    the user scroll past y=0, exposing blank canvas background at the
    top of the viewport.
    """
    import nk_GUI
    import inspect

    src = inspect.getsource(nk_GUI._make_scrollable)
    assert "scrollregion=(0, 0," in src, (
        "scrollregion not explicitly anchored at canvas origin; "
        "use (0, 0, bbox[2], bbox[3]) instead of bbox('all') directly"
    )
    assert 'canvas.bbox("all")' not in src, (
        "scrollregion still derived from bbox('all') -- can extend "
        "above the inner frame's top during transient layout states"
    )


def test_wheel_bound_to_canvas_not_global():
    """v0.5.9 fix for blank space at the top of the left panel: wheel
    events must bind to the canvas widget, not globally via bind_all.
    bind_all causes _on_wheel to fire for events over the right
    pane's matplotlib plots, which have their own wheel binding for
    zoom. The double-fire scrolls the left canvas unintentionally,
    pushing the left panel away from its natural scroll position and
    exposing blank canvas space at the top.
    """
    import nk_GUI
    import inspect

    src = inspect.getsource(nk_GUI._make_scrollable)
    # Check for an actual `.bind_all(` call, not just the word
    # "bind_all" (which appears in our docstring explaining why we
    # don't use it).
    assert ".bind_all(" not in src, (
        "_make_scrollable uses .bind_all(...) -- wheel events fire "
        "globally and can scroll the left pane when the user wheels on "
        "the right pane's matplotlib plots"
    )
    assert 'canvas.bind("<MouseWheel>"' in src, (
        "MouseWheel handler not bound to canvas widget"
    )
    assert 'canvas.bind("<Button-4>"' in src, (
        "X11 Button-4 (scroll up) not handled"
    )
    assert 'canvas.bind("<Button-5>"' in src, (
        "X11 Button-5 (scroll down) not handled"
    )


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

        # (2b) v0.5.8: frame_nk and frame_eps must have the same height
        # (Bug 2: nk and epsilon plots had different vertical sizes on
        # 1280x800 Linux Mint). Grid with weight=1 on both rows forces
        # equal allocation regardless of matplotlib's natural-size hint.
        h_nk = app.frame_nk.winfo_height()
        h_eps = app.frame_eps.winfo_height()
        assert h_nk == h_eps, (
            f"plot frames have different heights: nk={h_nk}, eps={h_eps}"
        )

        # (2c) v0.5.9: the scrollable Canvas in the left pane must
        # have a scrollregion rooted at canvas (0, 0). A scrollregion
        # with negative top lets the user scroll past y=0 and exposes
        # blank canvas background at the top of the left panel.
        # Find the scrollable Canvas: it's the only Canvas inside the
        # left pane (the right pane's matplotlib FigureCanvasTkAgg is
        # not a descendant of the left pane).
        def find_canvas(widget):
            if widget.winfo_class() == "Canvas":
                return widget
            for child in widget.winfo_children():
                result = find_canvas(child)
                if result is not None:
                    return result
            return None

        scroll_canvas = find_canvas(left_pane)
        assert scroll_canvas is not None, (
            "scrollable Canvas not found in left pane"
        )
        sr = scroll_canvas.cget("scrollregion")
        assert sr, (
            f"scrollregion not set on scrollable Canvas: {sr!r}"
        )
        sr_vals = [float(x) for x in sr.split()]
        assert sr_vals[0] == 0 and sr_vals[1] == 0, (
            f"scrollregion not rooted at (0, 0): {sr} -- user can "
            f"scroll past y=0 and see blank canvas at the top"
        )

        # (2d) v0.5.9: wheel events on the left pane's scrollable
        # Canvas must scroll it; wheel events on the right pane's
        # matplotlib canvas must NOT scroll the left pane. The old
        # bind_all binding double-fired on matplotlib's wheel handler
        # and pushed the left canvas away from scroll position 0,
        # exposing blank space at the top.
        bbox = scroll_canvas.bbox("all")
        canvas_h = scroll_canvas.winfo_height()
        scrollable = (
            bbox is not None
            and bbox[3] > canvas_h
            and canvas_h > 1
        )
        if scrollable:
            scroll_canvas.yview_moveto(0)
            root.update_idletasks()
            assert scroll_canvas.yview()[0] == 0.0, (
                "scrollable Canvas didn't reset to scroll position 0"
            )

            # Wheel DOWN on the scrollable Canvas scrolls it down.
            scroll_canvas.event_generate("<MouseWheel>", delta=-120)
            root.update_idletasks()
            assert scroll_canvas.yview()[0] > 0.0, (
                "MouseWheel on scrollable Canvas didn't scroll it"
            )

            # Reset to top and confirm.
            scroll_canvas.yview_moveto(0)
            root.update_idletasks()

            # Wheel DOWN on the right pane's matplotlib canvas must
            # NOT scroll the left pane. Find the matplotlib canvas
            # (a Canvas inside the right pane that isn't our
            # scrollable canvas).
            right_pane = panes[1]

            def find_other_canvas(widget, exclude):
                if widget.winfo_class() == "Canvas" and widget is not exclude:
                    return widget
                for child in widget.winfo_children():
                    result = find_other_canvas(child, exclude)
                    if result is not None:
                        return result
                return None

            mpl_canvas = find_other_canvas(right_pane, scroll_canvas)
            if mpl_canvas is not None:
                scroll_canvas.yview_moveto(0)
                root.update_idletasks()
                mpl_canvas.event_generate("<MouseWheel>", delta=-120)
                root.update_idletasks()
                assert scroll_canvas.yview()[0] == 0.0, (
                    "left pane scrolled when wheel fired on right pane's "
                    "matplotlib canvas -- bind_all bug regressed"
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