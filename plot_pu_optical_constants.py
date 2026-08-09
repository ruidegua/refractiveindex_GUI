"""Plot optical constants for Pu and Pu oxide from the 2019 paper."""
import numpy as np
import matplotlib.pyplot as plt

# Generate data from the formulas in the paper
wl = np.linspace(435, 850, 500)  # nm

# Delta-Pu (Appendix C)
n_pu = -0.6702078 + 0.005482374 * wl - 1.374023e-6 * wl**2
k_pu = -0.1313834 + 0.01075337 * wl - 8.596842e-6 * wl**2

# Pu oxide 41nm (Appendix B)
n_oxide = (12.95378 - 0.09204364*wl + 0.0002722518*wl**2 
           - 3.787362e-7*wl**3 + 2.570111e-10*wl**4 - 6.893235e-14*wl**5)
k_oxide = (17.81371 - 0.1875458*wl + 0.0007856408*wl**2 
            - 1.651641e-6*wl**3 + 1.881628e-9*wl**4 - 1.116711e-12*wl**5 + 2.717676e-16*wl**6)

# Create figure with two subplots
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

# Plot Delta-Pu
ax1.plot(wl, n_pu, 'b-', linewidth=2, label='n (Pu)')
ax1.plot(wl, k_pu, 'r--', linewidth=2, label='k (Pu)')
ax1.set_xlabel('Wavelength (nm)', fontsize=12)
ax1.set_ylabel('n, k', fontsize=12)
ax1.set_title('Delta-Pu (δ-Pu) Optical Constants\n(J. Appl. Phys. 125, 183102, 2019 - Appendix C)', fontsize=12)
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.3)
ax1.set_xlim(435, 850)

# Plot Pu oxide
ax2.plot(wl, n_oxide, 'b-', linewidth=2, label='n (Pu oxide)')
ax2.plot(wl, k_oxide, 'r--', linewidth=2, label='k (Pu oxide)')
ax2.set_xlabel('Wavelength (nm)', fontsize=12)
ax2.set_ylabel('n, k', fontsize=12)
ax2.set_title('Pu Oxide (41 nm) Optical Constants\n(J. Appl. Phys. 125, 183102, 2019 - Appendix B)', fontsize=12)
ax2.legend(fontsize=10)
ax2.grid(True, alpha=0.3)
ax2.set_xlim(435, 850)

plt.tight_layout()
from pathlib import Path
out = Path(__file__).resolve().parent / "pu_optical_constants.png"
plt.savefig(out, dpi=150)
plt.show()

print(f"Plot saved to: {out}")
