# refractiveindex_GUI

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Bundled DB: CC0](https://img.shields.io/badge/database-CC0-lightgrey.svg)](db/doc/permission.txt)

A self-contained Tk GUI for browsing **refractive index (n, k)** and
**dielectric function (ε₁, ε₂)** curves from the
[refractiveindex.info](https://refractiveindex.info) database — bundled
locally so it works offline without depending on the `refractiveindex`
pip package's installed data path.

> **Based on `nk_GUI_v0_5.py`** (2026-08-08).
> v0.5.6: cross-platform maximize helper + classic `tk.PanedWindow` for
> smooth sash drag on macOS / Linux; fixed `os.path.join` bugs in Pu data
> build scripts; corrected `build_sc_db.py` output path.
> v0.5.5: CSV sorted ascending by wavelength; n/k use `:.6g` so small k
> (e.g. 3e-7) doesn't round to 0.
> v0.5.4: CSV export wavelength changed from nm to μm.
> v0.5.3: log-axis bug fixes (scroll zoom, Apply button, entry boxes).
> v0.5.2: CSV export simplified to 3 columns (wavelength_nm, n, k); extra/custom
> DB consolidated in `./db_extra/`.
> v0.5.1: bundled-DB path resolution; the original feature set is unchanged.

## Features

| Capability | Status |
|---|---|
| Browse the full refractiveindex.info catalog (12 shelves, 3582+ entries) | ✅ |
| Two independent plot frames: **n, k** and **ε₁, ε₂** | ✅ |
| X-axis switchable: wavelength (nm) ↔ photon energy (eV) | ✅ |
| Per-plot Y range, log-Y toggle, rubber-band zoom, right-drag pan, scroll zoom | ✅ |
| Tab-style active-plot selector on left panel | ✅ |
| Query n / k / ε at a given wavelength or photon energy | ✅ |
| Export current spectrum to CSV | ✅ |
| Local custom shelves (Pu, Sc, ...) auto-merged via `pu_data/db/catalog-*.yml` | ✅ |
| Search box (filters shelf / book / page by name or ID) | ✅ |

## Installation

```bash
git clone https://github.com/<your-org>/refractiveindex_GUI.git
cd refractiveindex_GUI
pip install -r requirements.txt
```

Requires Python ≥ 3.10. Tkinter ships with CPython on Windows/macOS; on
Linux install `python3-tk` separately.

## Usage

```bash
python nk_GUI.py
```

On startup the title bar reports which database was loaded:

```
nk Curve Viewer v0.5.1 — refractiveindex.info (bundled (./db))
```

If `db/catalog-nk.yml` is missing the GUI automatically falls back to the
system DB distributed with the `refractiveindex` pip package (at
`%USERPROFILE%\.refractiveindex.info-database` on Windows,
`~/.refractiveindex.info-database` on Linux/macOS).

## Project layout

```
refractiveindex_GUI/
├── nk_GUI.py                    # Main Tk GUI (entry point)
├── generate_pu_data.py          # Regenerate the Pu data files from the 2019 paper
├── plot_pu_optical_constants.py # Quick standalone plot of the Pu data
├── db/                          # Bundled refractiveindex.info database (CC0)
│   ├── catalog-n2.yml, catalog-nk.yml
│   ├── data/{glass,main,organic,other,specs}/   # 4180+ yml data files
│   ├── doc/                     #   license, credits, formulas PDF
│   └── .version                 #   upstream git SHA
├── db_extra/                    # Extra / custom DB (NOT from refractiveindex.info)
│   ├── catalog-pu.yml, catalog-sc.yml
│   ├── Pu/...                   #   Pu shelf data (Dinh 2019)
│   ├── Sc/...                   #   Sc shelf data (Sigrist/Weaver/Henke)
│   ├── *.csv, *.txt, *.yml      #   raw measurement files
│   └── build_*.py, simulate_load.py, test_db.py, ...
├── requirements.txt
├── LICENSE                      # MIT (code) + CC0 (db/) notice
├── README.md
├── CHANGELOG.md
└── .gitignore
```

`db/` (refractiveindex.info) and `db_extra/` (your own additions) are
separate on purpose. The GUI merges both catalogs at startup; the extra
shelves appear in the tree just like the system ones.

## Adding a custom material

The GUI auto-discovers any `catalog-<name>.yml` file in `db_extra/` and
merges it into the catalog at startup. To add a new material:

1. Drop a shelf directory under `db_extra/<shelf>/<book>/`.
2. Create `db_extra/catalog-<name>.yml` that points at it (see
   `catalog-pu.yml` / `catalog-sc.yml` for examples).
3. Restart the GUI — the new shelf appears in the tree on the left.

Shelf / book / page IDs and the YAML schema follow the upstream
refractiveindex.info convention (`SHELF` / `BOOK` / `PAGE` blocks in
catalogs, `DATA` blocks in pages). See `db/data/main/Si/Aspnes.yml` for
a typical example.

## Data sources

| Shelf | Source | License |
|---|---|---|
| `db/` (glass, main, organic, other, specs) | refractiveindex.info, M. Polyanskiy | CC0 1.0 |
| `db_extra/Pu` | Dinh et al., *J. Appl. Phys.* **125**, 183102 (2019), Appendices B & C | (paper) |
| `db_extra/Sc` | Sigrist (1987) + Henke (1993) + Weaver (1981) | (papers) |

See `db/doc/credits.txt` for the full upstream credit list and
`db_extra/` for the original measurement files.

## Versioning

- **v0.5.6** (this repo) — cross-platform maximize + PanedWindow fix; build
  script bug fixes (3 scripts); CI matrix (3 OS × 3 Python).
- **v0.5.5** — CSV sorted ascending; precision bumped to 6 sig digs.
- **v0.5.4** — CSV export wavelength in μm.
- **v0.5.3** — log-axis bug fixes (scroll zoom, Apply, entry boxes).
- **v0.5.2** — 3-column CSV export; extra DB moved to `db_extra/`.
- **v0.5.1** — bundled DB; title bar reports DB source.
- **v0.5** — original two-plot independent-zoom/pan rewrite.

## Related projects

- [se-ellipsometry](https://github.com/ruidegua/se-ellipsometry) — fitting
  + inversion of spectroscopic ellipsometry data; consumes the same
  refractiveindex database.