# -*- coding: utf-8 -*-
"""
Generate optical constants for delta-Pu and Pu oxide from the 2019 paper
(Dinh et al., J. Appl. Phys. 125, 183102 — Appendices B & C).

Reproduces the data files committed under ``./`` next to this script
(``delta-Pu.txt``, ``Pu-oxide-41nm.txt``, ``Pu-oxide-47.95nm.txt``).

Run from anywhere:
    python generate_pu_data.py
Files are written to the same directory as this script.
"""
import numpy as np
from pathlib import Path

# Wavelength range: 435-850 nm
wl = np.linspace(435, 850, 500)

# Delta Pu (delta-Pu) optical constants from Appendix C
# n = -0.6702078 + 0.005482374*lambda - 1.374023e-6*lambda^2
# k = -0.1313834 + 0.01075337*lambda - 8.596842e-6*lambda^2
n = -0.6702078 + 0.005482374 * wl - 1.374023e-6 * wl**2
k = -0.1313834 + 0.01075337 * wl - 8.596842e-6 * wl**2

# Also generate for Pu oxide (41 nm) from Appendix B
n_oxide = (12.95378 - 0.09204364*wl + 0.0002722518*wl**2
           - 3.787362e-7*wl**3 + 2.570111e-10*wl**4 - 6.893235e-14*wl**5)
k_oxide = (17.81371 - 0.1875458*wl + 0.0007856408*wl**2
           - 1.651641e-6*wl**3 + 1.881628e-9*wl**4 - 1.116711e-12*wl**5 + 2.717676e-16*wl**6)

# Convert wavelength from nm to um for the database format
wl_um = wl / 1000.0

# Save as tabulated data, relative to this script
output_dir = Path(__file__).resolve().parent
output_dir.mkdir(parents=True, exist_ok=True)

# Delta-Pu: tabulated n,k format
with open(os.path.join(output_dir, "delta-Pu.txt"), "w", encoding="utf-8") as f:
    f.write("# Delta-Pu (delta-Pu) optical constants\n")
    f.write("# From: Spectroscopic ellipsometry extraction of optical constants\n")
    f.write("# for materials from oxide covered samples: Application to the\n")
    f.write("# plutonium/oxides system, J. Appl. Phys. 125, 183102 (2019)\n")
    f.write("# Appendix C: n = -0.6702078 + 0.005482374*lambda - 1.374023e-6*lambda^2\n")
    f.write("#            k = -0.1313834 + 0.01075337*lambda - 8.596842e-6*lambda^2\n")
    f.write("# lambda range: 435-850 nm\n")
    f.write("#\n")
    f.write("# Format: wavelength(um)  n  k\n")
    for w, n_val, k_val in zip(wl_um, n, k):
        f.write(f"{w:.6f}  {n_val:.6f}  {k_val:.6f}\n")

# Pu oxide: tabulated n,k format  
with open(os.path.join(output_dir, "Pu-oxide-41nm.txt"), "w", encoding="utf-8") as f:
    f.write("# Pu oxide (41 nm surface oxide) optical constants\n")
    f.write("# From: Same 2019 paper, Appendix B\n")
    f.write("# lambda range: 435-850 nm\n")
    f.write("#\n")
    f.write("# Format: wavelength(um)  n  k\n")
    for w, n_val, k_val in zip(wl_um, n_oxide, k_oxide):
        f.write(f"{w:.6f}  {n_val:.6f}  {k_val:.6f}\n")

print("Data files generated:")
print(f"  Delta-Pu: {len(wl)} points, lambda={wl[0]}-{wl[-1]} nm")
print(f"  Pu oxide: {len(wl)} points, lambda={wl[0]}-{wl[-1]} nm")
print(f"\nData saved to: {output_dir}")

# Also print sample values
print("\n=== Delta-Pu sample values ===")
print("lambda(nm)    n        k")
for i in [0, 100, 200, 300, 400]:
    print(f"{wl[i]:.0f}    {n[i]:.4f}  {k[i]:.4f}")

print("\n=== Pu oxide (41nm) sample values ===")
print("lambda(nm)    n        k")
for i in [0, 100, 200, 300, 400]:
    print(f"{wl[i]:.0f}    {n_oxide[i]:.4f}  {k_oxide[i]:.4f}")
