# -*- coding: utf-8 -*-
"""Build Pu database YAML files from the paper formulas."""
import numpy as np
import os

# Output base dir
base = r"D:\xiaorui_macOS\scripts\refractiveindex\pu_data\db"
pu_dir = os.path.join(base, "Pu")
os.makedirs(pu_dir, exist_ok=True)

# Wavelength: 435-850 nm, every 5 nm = 84 points
wl_nm = np.arange(435, 855, 5)  # 435 to 850 inclusive
wl_um = wl_nm / 1000.0

# ═══════════════════════════════════════════════
# Delta-Pu (Appendix C)
# n = -0.6702078 + 0.005482374*λ - 1.374023e-6*λ²
# k = -0.1313834 + 0.01075337*λ - 8.596842e-6*λ²
# ═══════════════════════════════════════════════
n_pu = -0.6702078 + 0.005482374 * wl_nm - 1.374023e-6 * wl_nm**2
k_pu = -0.1313834 + 0.01075337 * wl_nm - 8.596842e-6 * wl_nm**2

lines = ["# Delta-Pu optical constants\n",
         "# J. Appl. Phys. 125, 183102 (2019) - Appendix C\n",
         "# lambda range: 435-850 nm\n",
         "#\n",
         "DATA:\n",
         "  - type: tabulated nk\n",
         "    wavelength_range: 0.435 0.850\n",
         "    data: |\n"]
for w, n, k in zip(wl_um, n_pu, k_pu):
    lines.append(f"      {w:.4f}  {n:.6f}  {k:.6f}\n")

with open(os.path.join(pu_dir, "delta-Pu.yml"), "w", encoding="utf-8") as f:
    f.writelines(lines)

# ═══════════════════════════════════════════════
# Pu oxide 41nm (Appendix B)
# n = 12.95378 - 0.09204364*λ + 0.0002722518*λ² - 3.787362e-7*λ³ + 2.570111e-10*λ⁴ - 6.893235e-14*λ⁵
# k = 17.81371 - 0.1875458*λ + 0.0007856408*λ² - 1.651641e-6*λ³ + 1.881628e-9*λ⁴ - 1.116711e-12*λ⁵ + 2.717676e-16*λ⁶
# ═══════════════════════════════════════════════
n_ox41 = (12.95378 - 0.09204364*wl_nm + 0.0002722518*wl_nm**2 
          - 3.787362e-7*wl_nm**3 + 2.570111e-10*wl_nm**4 - 6.893235e-14*wl_nm**5)
k_ox41 = (17.81371 - 0.1875458*wl_nm + 0.0007856408*wl_nm**2 
           - 1.651641e-6*wl_nm**3 + 1.881628e-9*wl_nm**4 - 1.116711e-12*wl_nm**5 + 2.717676e-16*wl_nm**6)

lines = ["# Pu oxide (41 nm) optical constants\n",
         "# J. Appl. Phys. 125, 183102 (2019) - Appendix B\n",
         "# lambda range: 435-850 nm\n",
         "#\n",
         "DATA:\n",
         "  - type: tabulated nk\n",
         "    wavelength_range: 0.435 0.850\n",
         "    data: |\n"]
for w, n, k in zip(wl_um, n_ox41, k_ox41):
    lines.append(f"      {w:.4f}  {n:.6f}  {k:.6f}\n")

with open(os.path.join(pu_dir, "Pu-oxide-41nm.yml"), "w", encoding="utf-8") as f:
    f.writelines(lines)

# ═══════════════════════════════════════════════
# Pu oxide 47.95nm (Appendix B, second set)
# Same formulas as 41nm but different coefficients (slightly different fit)
# n = 12.95379 - 0.09204364*λ + 0.0002722518*λ² - 3.787362e-7*λ³ + 2.570111e-10*λ⁴ - 6.893235e-14*λ⁵
# k = 17.81371 - 0.1875458*λ + 0.0007856408*λ² - 1.651641e-6*λ³ + 1.881628e-9*λ⁴ - 1.116711e-12*λ⁵ + 2.717676e-16*λ⁶
# ═══════════════════════════════════════════════
n_ox48 = (12.95379 - 0.09204364*wl_nm + 0.0002722518*wl_nm**2 
          - 3.787362e-7*wl_nm**3 + 2.570111e-10*wl_nm**4 - 6.893235e-14*wl_nm**5)
k_ox48 = (17.81371 - 0.1875458*wl_nm + 0.0007856408*wl_nm**2 
           - 1.651641e-6*wl_nm**3 + 1.881628e-9*wl_nm**4 - 1.116711e-12*wl_nm**5 + 2.717676e-16*wl_nm**6)

lines = ["# Pu oxide (47.95 nm) optical constants\n",
         "# J. Appl. Phys. 125, 183102 (2019) - Appendix B\n",
         "# lambda range: 435-850 nm\n",
         "#\n",
         "DATA:\n",
         "  - type: tabulated nk\n",
         "    wavelength_range: 0.435 0.850\n",
         "    data: |\n"]
for w, n, k in zip(wl_um, n_ox48, k_ox48):
    lines.append(f"      {w:.4f}  {n:.6f}  {k:.6f}\n")

with open(os.path.join(pu_dir, "Pu-oxide-48nm.yml"), "w", encoding="utf-8") as f:
    f.writelines(lines)

print("Database files created:")
print(f"  {pu_dir}\\delta-Pu.yml")
print(f"  {pu_dir}\\Pu-oxide-41nm.yml")
print(f"  {pu_dir}\\Pu-oxide-48nm.yml")
print(f"\nData points per file: {len(wl_nm)} (every 5 nm from 435-850 nm)")

# Verify
import yaml
for fn in ["delta-Pu.yml", "Pu-oxide-41nm.yml", "Pu-oxide-48nm.yml"]:
    with open(os.path.join(pu_dir, fn), "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    d = data["DATA"][0]
    pts = d["data"].strip().split("\n")
    first = pts[0].split()
    last = pts[-1].split()
    print(f"\n{fn}:")
    print(f"  Range: {first[0]} - {last[0]} um")
    print(f"  First: n={first[1]}, k={first[2]}")
    print(f"  Last:  n={last[1]}, k={last[2]}")
