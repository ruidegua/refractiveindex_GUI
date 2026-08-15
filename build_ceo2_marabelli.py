r"""Build db_extra/CeO2/Marabelli-1987.yml from the digitized Fig 2/3 data.

Source: Marabelli & Wachter, PRB 36, 1238 (1987), digitized from
Figs 2 and 3 by the user with webplotdigitizer (or similar).

Inputs (from D:/xiaorui_macOS/scripts/refellips/RIs/1987-prb-ceo2/):
  eps1.csv    eps1 vs E(eV),  high-E (Fig 2)
  eps2.csv    eps2 vs E(eV),  high-E (Fig 2)
  eps1_.csv   eps1 vs E(eV),  low-E (Fig 3, phonon mode tail)
  eps2__.csv  eps2 vs E(eV),  low-E (Fig 3)
  eps2_.csv   eps2 vs E(eV),  mid-E 4 eV peak region (Fig 2 detail)

Output: db_extra/CeO2/Marabelli-1987.yml, refractiveindex.info
format with `tabulated epsilon`, sorted by descending wavelength.
"""
from __future__ import annotations

import sys
from pathlib import Path
import numpy as np

# Repo + source paths
REPO = Path(r"D:\xiaorui_macOS\scripts\refractiveindex_GUI")
SRC = Path(r"D:\xiaorui_macOS\scripts\refellips\RIs\1987-prb-ceo2")
OUT = REPO / "db_extra" / "CeO2" / "Marabelli-1987.yml"


def load_csv(path: Path) -> tuple[np.ndarray, np.ndarray]:
    r"""Load a two-column CSV: E(eV), value. Returns (E, value)."""
    arr = np.loadtxt(path, delimiter=",", comments="#")
    E = arr[:, 0]
    v = arr[:, 1]
    # Filter negative E (junk at end of low-E files)
    mask = E > 0
    return E[mask], v[mask]


def merge_pair(e1: np.ndarray, v1: np.ndarray,
               e2: np.ndarray, v2: np.ndarray,
               grid: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Linearly interpolate v1 and v2 onto a common energy grid."""
    return (np.interp(grid, e1, v1), np.interp(grid, e2, v2))


def build_highE() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Fig 2: 0.4-12 eV. Use eps1.csv + eps2.csv for the broad range,
    and merge in eps2_.csv (the dense 4 eV peak digitization) by
    overwriting eps2 with the more accurate values where they overlap.
    """
    E1, eps1 = load_csv(SRC / "eps1.csv")
    E2, eps2 = load_csv(SRC / "eps2.csv")
    E2d, eps2_detail = load_csv(SRC / "eps2_.csv")  # dense 4 eV peak

    # Common grid for eps1/eps2: union of E1 and E2, sorted ascending
    grid = np.union1d(E1, E2)
    eps1_i = np.interp(grid, E1, eps1)
    eps2_i = np.interp(grid, E2, eps2)

    # Overwrite eps2 with dense peak data where available
    dense_mask = (grid >= E2d.min()) & (grid <= E2d.max())
    # For dense peak region: interpolate eps2_detail to grid
    eps2_dense = np.interp(grid[dense_mask], E2d, eps2_detail)
    eps2_i[dense_mask] = eps2_dense

    return grid, eps1_i, eps2_i


def build_lowE() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Fig 3: 1 meV to 0.1 eV. Use eps1_.csv + eps2__.csv."""
    E1, eps1 = load_csv(SRC / "eps1_.csv")
    E2, eps2 = load_csv(SRC / "eps2__.csv")
    grid = np.union1d(E1, E2)
    return (grid,
            np.interp(grid, E1, eps1),
            np.interp(grid, E2, eps2))


def main() -> int:
    print("Loading high-E (Fig 2)...")
    E_hi, e1_hi, e2_hi = build_highE()
    print(f"  {len(E_hi)} points, {E_hi.min():.4f}-{E_hi.max():.4f} eV")

    print("Loading low-E (Fig 3)...")
    E_lo, e1_lo, e2_lo = build_lowE()
    print(f"  {len(E_lo)} points, {E_lo.min():.4f}-{E_lo.max():.4f} eV")

    # Combine, sort by ascending wavelength (descending energy).
    # Project convention (Pu/Sc tests): wl[0] < wl[-1] (ascending).
    E_all = np.concatenate([E_lo, E_hi])
    e1_all = np.concatenate([e1_lo, e1_hi])
    e2_all = np.concatenate([e2_lo, e2_hi])

    # Convert eV to wavelength in micrometers first, then sort ascending
    lam_um = 1.23984193 / E_all
    order = np.argsort(lam_um)
    lam_um = lam_um[order]
    e1_all = e1_all[order]
    e2_all = e2_all[order]
    E_all = E_all[order]

    # Convert (eps1, eps2) -> (n, k) using n + ik = sqrt(eps1 + i*eps2)
    # Works correctly in all regimes including reststrahlen band (eps1 < 0):
    #   n = Re(sqrt(eps)), k = Im(sqrt(eps))
    eps_complex = e1_all + 1j * e2_all
    nk_complex = np.sqrt(eps_complex)
    n_arr = nk_complex.real
    k_arr = nk_complex.imag
    # Physically: passive dielectric -> k >= 0 always. Digitization noise in
    # eps2 around zero flips the principal-branch sqrt to give k < 0. Clip.
    k_arr = np.maximum(k_arr, 0.0)

    # Sanity check: filter any obviously bad points (negative k is unphysical
    # except in gain media; here CeO2 is purely passive so k >= 0 always).
    # Some digitization artifacts at the tail of Fig 3 give weird values.
    bad = (k_arr < -0.5) | ~np.isfinite(n_arr) | ~np.isfinite(k_arr)
    if bad.any():
        print(f"  WARNING: {bad.sum()} bad points (k<0 or non-finite), dropping")
        mask = ~bad
        lam_um = lam_um[mask]
        n_arr = n_arr[mask]
        k_arr = k_arr[mask]
        E_all = E_all[mask]

    # Build yml
    OUT.parent.mkdir(parents=True, exist_ok=True)
    n_pts = len(lam_um)
    print(f"Writing {n_pts} points to {OUT}")

    # Format: 6 sig digits (matches refractiveindex.info convention)
    lines = []
    for L, n_val, k_val in zip(lam_um, n_arr, k_arr):
        lines.append(f"        {L:.6g} {n_val:.6g} {k_val:.6g}")

    yaml_text = f"""# refractiveindex.info local extension (CC0)
# Source: F. Marabelli and P. Wachter,
#   "Covalent insulator CeO2: Optical reflectivity measurements",
#   Phys. Rev. B 36, 1238 (1987).
# DOI: 10.1103/PhysRevB.36.1238
# Sample: CeO2 single crystal, melt-grown, annealed 500 C in O2 (yellow,
#   transparent). Measurement: optical reflectivity 1 meV-12 eV at 300 K,
#   Kramers-Kronig analysis -> eps1, eps2 -> n, k via n + ik = sqrt(eps).
# Data digitized by user from Figs 2 (high-E) and 3 (low-E) using
# webplotdigitizer-style extraction.
#
# Wavelength range: {lam_um.min():.4g}-{lam_um.max():.4g} um
#   ({E_all.max():.4g}-{E_all.min():.4g} eV)
# Number of points: {n_pts}
REFERENCES: |
    F. Marabelli and P. Wachter. Covalent insulator CeO2: optical reflectivity
    measurements. <a href="https://doi.org/10.1103/PhysRevB.36.1238"><i>Phys. Rev. B</i>
    <b>36</b>, 1238 (1987)</a>
COMMENTS: |
    Single crystal, melt-grown from 99.99% pure CeO2, sintered at 1000 C in
    1 bar O2, electron-beam-welded tungsten crucible at 2275 C, slow-cooled
    6 days. Bleached by annealing 5 h at 500 C in O2 stream (yellow,
    transparent). CaF2-type structure. Reflectivity 1 meV-12 eV at 300 K
    analyzed by Kramers-Kronig to obtain eps1, eps2, then converted to n, k
    via n + ik = sqrt(eps1 + i*eps2). Digitized from Marabelli & Wachter
    PRB 36, 1238 (1987), Figs 2 (high-E) and 3 (low-E).
DATA:
  - type: tabulated nk
    data: |
{chr(10).join(lines)}
"""

    OUT.write_text(yaml_text, encoding="utf-8")
    print(f"Done: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())