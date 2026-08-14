# Changelog

All notable changes to **refractiveindex_GUI** are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
this project adheres to [Semantic Versioning](https://semver.org/).

## [0.5.9] — 2026-08-15

### Fixed
- **Blank canvas space at the top of the left panel when scrolling**.
  Two coupled bugs in `_make_scrollable`:
  1. **Wheel bound globally via `bind_all`**: scrolling over the right
     pane's matplotlib plots double-fired `_on_wheel` (matplotlib's
     zoom handler + the global binding), scrolling the left canvas
     away from its natural position. Once the user looked back at the
     left panel, the top portion showed blank canvas background.
     Switched to `canvas.bind("<MouseWheel>" / "<Button-4>" /
     "<Button-5>", ...)` — Tk event propagation ensures this still
     fires for the canvas AND every descendant control (search entry,
     tree, radiobuttons, options, buttons), but NOT for events over
     the right pane. No `Enter`/`Leave` dance needed.
  2. **Scrollregion derived from `canvas.bbox("all")` directly**:
     bbox can transiently report coordinates with `y < 0` during
     initial layout or content reflow. A scrollregion with a
     negative top lets the user scroll past y=0, exposing blank
     canvas background at the top of the viewport. Anchored the
     scrollregion at `(0, 0, bbox[2], bbox[3])` so the user can
     never scroll above the inner frame's top.

### Added
- 2 new source-inspection tests:
    - `test_scrollregion_rooted_at_origin` — verifies the
      scrollregion is built with explicit `(0, 0, ...)` and not from
      `bbox("all")` directly.
    - `test_wheel_bound_to_canvas_not_global` — verifies no
      `.bind_all(...)` call exists in `_make_scrollable`.
- 1 in-process assertion added to `test_gui_features_combined`:
    - `sr_vals[0] == 0 and sr_vals[1] == 0` — verifies the live
      scrollregion on the built GUI is rooted at canvas (0, 0).
    - `event_generate("<MouseWheel>")` on the scrollable Canvas
      changes `yview()` (wheel does scroll the left panel).
    - `event_generate("<MouseWheel>")` on the right pane's matplotlib
      Canvas does NOT change the left panel's `yview()` (no more
      `bind_all` regression — wheel only scrolls the panel it
      belongs to).

## [0.5.8] — 2026-08-11

### Fixed
- **Export CSV button unreachable on 1280x800 Linux Mint**: the left
  control panel's total content height (~540 px including title,
  search, tree, Active Plot / Options / Query LabelFrames, Status,
  Export CSV button) exceeded the left pane's visible content area
  on some Linux Mint setups where Cinnamon WM decorations + theme
  reduced the usable height. Tk `pack` silently clipped the bottom
  widget. The left pane is now wrapped in a scrollable Canvas
  (`_make_scrollable` helper), so all controls remain reachable via
  mouse wheel / scrollbar even on small screens. Handles macOS delta
  events, X11 Button-4/5 (Cinnamon), and Windows MouseWheel.
- **nk and epsilon plots rendered at different heights on 1280x800
  Linux Mint**: matplotlib's `FigureCanvasTkAgg` has a figsize-based
  natural size request (8×4.2 in @ 110 dpi = 880×462 px) that
  `pack(expand=True)` didn't honour consistently across themes.
  Switched the right pane to `grid` layout with `weight=1` on rows 1
  and 2 so they get equal allocation regardless of internal sizing
  quirks. Both plots now always render at exactly the same height.

### Added
- `_make_scrollable(parent)` helper: returns an inner Frame wrapped in
  a Canvas + vertical scrollbar, with mouse-wheel scrolling bound on
  `<Enter>` and unbound on `<Leave>` so wheel events only fire when
  the cursor is over the scrollable region.
- 2 new source-inspection tests + 1 in-process assertion (combined
  into the existing GUI test to avoid the Windows Tk state-reuse
  bug):
    - `test_left_pane_is_scrollable`
    - `test_right_pane_uses_grid_layout`
    - `app.frame_nk.winfo_height() == app.frame_eps.winfo_height()`
      inside `test_gui_features_combined`

## [0.5.7] — 2026-08-11

### Changed
- **Adaptive window geometry**: replaced hard-coded `1200x900`
  default + `minsize(1000, 650)` with `_adaptive_geometry(root)`,
  which reads `winfo_screenwidth/height` and picks a sensible size
  for the actual display. Default = 85% of usable screen, clamped to
  `[720, 1800] × [500, 1100]` and capped at the usable size (with
  ~40 px horizontal / ~60 px vertical slack for window decorations)
  so the window never opens larger than the display. Minsize = 85%
  of default, with a hard floor `[640, 440]`. Window title bar is
  now `v0.5.7`.
- **Adaptive left pane width**: `width=430` on the left PanedWindow
  pane became `_left_panel_width(sw) = min(430, max(280, 32% of sw))`.
  The 32% rule keeps the historical 430 px on any display ≥ 1344 px
  wide; on smaller screens the pane shrinks so the right plot area
  keeps room. Pure helper, unit-tested without a display.

### Fixed
- **Small-screen display cutoff**: on 1280×800 (ThinkPad X1 Carbon,
  older MacBook Air, Surface Pro, etc.) the previous 1200×900 default
  overflowed the display — maximizing it hid the menubar / plot
  borders. New default at 1280×800 is `1054×629` with minsize
  `895×534` and left pane `409 px`; window always fits the screen.
- **Tiny-screen layout collapse**: on 1024×600 netbooks the old
  `minsize(1000, 650)` was effectively un-shrinkable, leaving no
  room for the user to grab the sash. New minsize at 1024×600 is
  `710×440`, and the left pane shrinks to `327 px` so the right pane
  can render both plots.

### Behaviour at common resolutions
| Screen | Default | Minsize | Left pane |
|---|---|---|---|
| 1920×1080 | 1598×867 | 1358×736 | 430 |
| 1366×768 | 1127×601 | 957×510 | 430 |
| **1280×800** | **1054×629** | **895×534** | **409** |
| 1024×600 | 836×500 | 751×440 | 327 |

### Added
- Pure helpers `_compute_geometry(sw, sh) -> (w, h, min_w, min_h)` and
  `_left_panel_width(sw)` so the layout math is unit-testable without
  a display server.
- 7 new tests in `tests/test_smoke.py` covering the 1280×800 case
  explicitly, 1920×1080, 1024×600, 4K, a sweep invariant test across
  9 common resolutions, and a behaviour test that runs
  `_adaptive_geometry(root)` against a real `tk.Tk()` root.

## [0.5.6] — 2026-08-10

### Fixed
- **Cross-platform window maximize**: replaced bare `root.state("zoomed")`
  with a platform-aware helper `_maximize_window(root)`.
  - `win32`: keeps `state("zoomed")` (works correctly).
  - `darwin` (macOS): no-op. macOS Tk silently ignores `state("zoomed")`
    so the window used to open at the 1200×900 fallback; users now get
    the same 1200×900 without the no-op call. The green maximize button
    on the title bar still works.
  - `linux` (X11 / Wayland / Cinnamon / MATE / Xfce): tries
    `state("zoomed")` first; if the WM doesn't apply it (some Wayland
    sessions and certain Cinnamon/MATE configs on Linux Mint silently
    drop the request), falls back to setting geometry to the screen
    size directly.
- **PanedWindow lag on macOS**: switched the left/right splitter from
  `ttk.PanedWindow` to classic `tk.PanedWindow`. The ttk version redraws
  every child widget on every sash motion event, which made dragging the
  left-side panel width feel janky on macOS. The classic version uses
  native window handles and is smooth on all three OSes.
- **`generate_pu_data.py` and `db_extra/generate_pu_ri.py`** were
  broken on all OSes (not a cross-platform issue per se, but they would
  fail with `NameError: name 'os' is not defined` on every run because
  `os.path.join` was used without `import os`). Replaced with
  `pathlib` `/` joins to match the project style.
- **`db_extra/build_sc_db.py`** wrote outputs to `db_extra/db/Sc/...`
  and `db_extra/db/catalog-sc.yml` — one directory level too deep.
  `nk_GUI.py` reads from `db_extra/` (not `db_extra/db/`), so running
  the script produced a stale catalog in `db_extra/db/` that the GUI
  ignored. Fixed to write to `db_extra/Sc/` and `db_extra/catalog-sc.yml`.

### Added
- Cross-platform smoke tests at `tests/test_smoke.py` covering DB path
  resolution, local catalog merge, system + local material loading, CSV
  export logic, and PanedWindow type / maximize-helper sanity checks.
- GitHub Actions CI at `.github/workflows/ci.yml` with a 3 OS × 3 Python
  matrix (Ubuntu / macOS / Windows × Python 3.10 / 3.11 / 3.12) that
  installs `python3-tk + xvfb` on Linux and runs the smoke tests under
  `MPLBACKEND=Agg`.

## [0.5.5] — 2026-08-09

### Fixed
- **CSV export sorted ascending by wavelength**: some upstream tabulated
  files (notably `Sc-Sigrist.yml` and similar that were originally sampled
  uniformly in photon energy) come out of `_load_material_data` with the
  wavelength column sorted descending. Exporting as-is produced CSVs where
  the x-axis jumped 4.59 → 0.0001 — confusing for downstream tools
  (pandas, gnuplot, spreadsheets) that expect monotonic x. CSV export now
  does `argsort(wavelengths)` before writing rows.
- **CSV export precision**: switched from `:.6f` (6 decimal places) to
  `:.6g` (6 significant digits) for n and k. The fixed format rounded
  very small values (e.g. k=3.02e-7 near the Lyman-α cutoff) to
  `0.000000` — losing information. Significant-digit format preserves
  small values without padding big values.

## [0.5.4] — 2026-08-09

### Changed
- **CSV export wavelength units**: changed from nm to μm (column header
  `wavelength_um`, values divided by 1000). Matches upstream
  refractiveindex.info raw data convention and most optics workflows
  (e.g. infrared / fiber / mid-IR where wavelengths are typically 0.2–10 μm).
  If you need nm in v0.5.4+, post-process with a `*1000` column or revert
  to v0.5.3.

## [0.5.3] — 2026-08-09

### Fixed
- **Log-axis scroll zoom**: zoom factor was being applied in matplotlib's
  data-coord space, which broke on log axes (zoom amount would be ~1.15x in
  log space but not in linear/visual space). Now works correctly — verified
  linear span scales by exactly 1.15x / 0.87x on log X and log Y.
- **Apply button (any mode, any axis)**: previously user-entered limits in
  `xmin` / `xmax` / `ymin` / `ymax` were silently dropped. Root cause: limits
  were applied BEFORE `ax.clear() + plot()`, and the autoscale reset that
  follows clear() overwrote them. Apply now runs AFTER the plot so limits
  survive.
- **Entry boxes on log axes**: previously showed log-axis data coords (e.g.
  `2.477`) instead of linear nm/eV values (e.g. `300`). After the rewrite
  matplotlib's `get_xlim()` is always LINEAR, so the entry boxes now show
  what the user expects (`300` not `2.477`) regardless of log toggle.
- **Range info text**: now always shows linear values with `(logX)` /
  `(logY)` indicators instead of confusing raw log-space coords.
- **Log Y auto-fit warning**: matplotlib would warn
  `Attempt to set non-positive ylim on a log-scaled axis` whenever the
  autoscale picked a range that included a zero/negative value (e.g. from
  k=0 data or negative ε1). Now clamps to a multiplicative pad on log.

### Added
- 4 module-level helpers (`_xlim_linear`, `_ylim_linear`,
  `_set_xlim_linear`, `_set_ylim_linear`) that bridge matplotlib's
  always-LINTERNAL get/set_xlim API with the GUI's always-LINEAR entry
  boxes. All GUI get/set call sites go through these.

## [0.5.2] — 2026-08-09

### Changed
- **CSV export simplified**: 3 columns (`wavelength_nm, n, k`) regardless of
  GUI x-axis mode. Dropped `energy_eV` / `epsilon1` / `epsilon2` columns
  (epsilon can be recomputed downstream from n, k).
- **`pu_data/` → `db_extra/`**: extra/custom DB (catalogs + shelves + raw
  source files + build scripts) consolidated into a single `db_extra/`
  directory at the repo root, flat layout. The system DB (`db/`,
  refractiveindex.info) and the extra DB (`db_extra/`) are now
  visibly separate.
- `nk_GUI.py` `LOCAL_DB_PATH` updated to `Path(__file__).resolve().parent
  / "db_extra"`.
- `generate_pu_data.py` now writes outputs to `db_extra/` instead of the
  repo root.
- Hardcoded Windows paths removed from `db_extra/build_pu_db.py`,
  `db_extra/build_sc_db.py`, `db_extra/generate_pu_ri.py`,
  `db_extra/simulate_load.py`, `db_extra/test_db.py` — all now use
  `Path(__file__).resolve().parent`.
- Initial-dir of the export file dialog now defaults to the script
  directory (was hardcoded to the old `D:\xiaorui_macOS\...` path).

## [0.5.1] — 2026-08-09

### Added
- **Bundled database**: `db/` ships the full refractiveindex.info
  database (CC0) — ~46 MB, 12 shelves, 3582 entries, 4180+ data files.
- **DB source resolution**: `nk_GUI.py` prefers the bundled `db/`
  directory next to the script; falls back to the system DB at
  `ri._DEFAULT_DB_PATH` if the bundled one is missing.
- Title bar reports which DB is active: `bundled (./db)` vs
  `system (...)`.
- `LICENSE` notes the CC0 dedication on `db/`.
- `requirements.txt` pins runtime deps (numpy, scipy, matplotlib,
  PyYAML, refractiveindex).
- `.gitignore` for Python caches and IDE files.

### Changed
- `nk_GUI_v0_5.py` renamed to `nk_GUI.py` for cleaner GitHub naming;
  v0.5 feature set is preserved verbatim.
- `Path(__file__).parent` → `Path(__file__).resolve().parent` in the
  DB-path resolution so it works regardless of the cwd.

## [0.5] — 2026-08-08

### Added
- Two independent plot frames: Refractive Index (n, k) and Dielectric
  Function (ε₁, ε₂), each with its own zoom / pan / Y range / log Y.
- Tab-style active-plot selector on the left panel; left-panel controls
  only affect the currently active plot.
- X-axis mode switch (wavelength ↔ photon energy), shared across both
  plots.
- Mouse-wheel zoom (fixed), rubber-band drag-to-zoom (left button),
  right-drag pan — all per-plot.
- Query n / k / ε at a given wavelength or photon energy.
- Export current spectrum to CSV.
- Range info text (X/Y bounds + log flags) in the bottom-right corner
  of each subplot.

## Earlier (pre-0.5, not in this repo)

v0.1 – v0.4 lived in `D:\xiaorui_macOS\scripts\refractiveindex\nk_GUI_v0_{1..4}.py`
and are preserved there as historical reference. They are not included
in this repo because v0.5 supersedes them.