# -*- coding: utf-8 -*-
"""Generate RI data files for Pu and Pu oxide from J. Appl. Phys. 125, 183102 (2019)."""
import numpy as np
from pathlib import Path

# Output directory: same as this script
out_dir = Path(__file__).resolve().parent
out_dir.mkdir(parents=True, exist_ok=True)

# Wavelength range: 435-850 nm (as specified in the paper)
wl = np.linspace(435, 850, 500)  # nm

# ═══════════════════════════════════════════════
# Delta-Pu (Appendix C)
# n = -0.6702078 + 0.005482374*λ - 1.374023e-6*λ²
# k = -0.1313834 + 0.01075337*λ - 8.596842e-6*λ²
# ═══════════════════════════════════════════════
n_pu = -0.6702078 + 0.005482374 * wl - 1.374023e-6 * wl**2
k_pu = -0.1313834 + 0.01075337 * wl - 8.596842e-6 * wl**2

# Convert λ from nm to μm for refractiveindex.info format
wl_um = wl / 1000.0

# Save as CSV (wavelength in nm, n, k)
csv_path = os.path.join(out_dir, "delta-Pu.csv")
with open(csv_path, "w", encoding="utf-8") as f:
    f.write("# Delta-Pu (δ-Pu) optical constants\n")
    f.write("# J. Appl. Phys. 125, 183102 (2019) - Appendix C\n")
    f.write("# λ range: 435-850 nm\n")
    f.write("# Formula: n = -0.6702078 + 0.005482374*λ - 1.374023e-6*λ²\n")
    f.write("#          k = -0.1313834 + 0.01075337*λ - 8.596842e-6*λ²\n")
    f.write("# wavelength_nm,n,k\n")
    for w, n_val, k_val in zip(wl, n_pu, k_pu):
        f.write(f"{w:.4f},{n_val:.6f},{k_val:.6f}\n")

print(f"Saved: {csv_path}")

# ═══════════════════════════════════════════════
# Pu oxide 41nm (Appendix B)
# n = 12.95378 - 0.09204364*λ + 0.0002722518*λ² - 3.787362e-7*λ³ + 2.570111e-10*λ⁴ - 6.893235e-14*λ⁵
# k = 17.81371 - 0.1875458*λ + 0.0007856408*λ² - 1.651641e-6*λ³ + 1.881628e-9*λ⁴ - 1.116711e-12*λ⁵ + 2.717676e-16*λ⁶
# ═══════════════════════════════════════════════
n_oxide_41 = (12.95378 - 0.09204364*wl + 0.0002722518*wl**2 
              - 3.787362e-7*wl**3 + 2.570111e-10*wl**4 - 6.893235e-14*wl**5)
k_oxide_41 = (17.81371 - 0.1875458*wl + 0.0007856408*wl**2 
               - 1.651641e-6*wl**3 + 1.881628e-9*wl**4 - 1.116711e-12*wl**5 + 2.717676e-16*wl**6)

csv_path2 = os.path.join(out_dir, "Pu-oxide-41nm.csv")
with open(csv_path2, "w", encoding="utf-8") as f:
    f.write("# Pu oxide (41 nm surface oxide) optical constants\n")
    f.write("# J. Appl. Phys. 125, 183102 (2019) - Appendix B\n")
    f.write("# λ range: 435-850 nm\n")
    f.write("# wavelength_nm,n,k\n")
    for w, n_val, k_val in zip(wl, n_oxide_41, k_oxide_41):
        f.write(f"{w:.4f},{n_val:.6f},{k_val:.6f}\n")

print(f"Saved: {csv_path2}")

# ═══════════════════════════════════════════════
# Pu oxide 47.95nm (Appendix B)
# ═══════════════════════════════════════════════
n_oxide_48 = (12.95379 - 0.09204364*wl + 0.0002722518*wl**2 
              - 3.787362e-7*wl**3 + 2.570111e-10*wl**4 - 6.893235e-14*wl**5)
k_oxide_48 = (17.81371 - 0.1875458*wl + 0.0007856408*wl**2 
               - 1.651641e-6*wl**3 + 1.881628e-9*wl**4 - 1.116711e-12*wl**5 + 2.717676e-16*wl**6)

csv_path3 = os.path.join(out_dir, "Pu-oxide-47.95nm.csv")
with open(csv_path3, "w", encoding="utf-8") as f:
    f.write("# Pu oxide (47.95 nm surface oxide) optical constants\n")
    f.write("# J. Appl. Phys. 125, 183102 (2019) - Appendix B\n")
    f.write("# λ range: 435-850 nm\n")
    f.write("# wavelength_nm,n,k\n")
    for w, n_val, k_val in zip(wl, n_oxide_48, k_oxide_48):
        f.write(f"{w:.4f},{n_val:.6f},{k_val:.6f}\n")

print(f"Saved: {csv_path3}")

# ═══════════════════════════════════════════════
# Verify data makes physical sense
# ═══════════════════════════════════════════════
print("\n=== Delta-Pu verification ===")
print("λ(nm)    n        k        Re(ε)    Im(ε)")
eps1 = n_pu**2 - k_pu**2
eps2 = 2 * n_pu * k_pu
for i in [0, 99, 199, 299, 399, 499]:
    print(f"{wl[i]:.0f}    {n_pu[i]:.6f}  {k_pu[i]:.6f}  {eps1[i]:8.4f}  {eps2[i]:8.4f}")

print("\n=== Pu oxide (41nm) verification ===")
print("λ(nm)    n        k        Re(ε)    Im(ε)")
eps1_o = n_oxide_41**2 - k_oxide_41**2
eps2_o = 2 * n_oxide_41 * k_oxide_41
for i in [0, 99, 199, 299, 399, 499]:
    print(f"{wl[i]:.0f}    {n_oxide_41[i]:.6f}  {k_oxide_41[i]:.6f}  {eps1_o[i]:8.4f}  {eps2_o[i]:8.4f}")
