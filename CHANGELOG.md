# Changelog

All notable changes to **refractiveindex_GUI** are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
this project adheres to [Semantic Versioning](https://semver.org/).

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