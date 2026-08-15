"""Sanity check plot for CeO2 Marabelli-1987 data extraction.

Generates 4-panel plot:
  - eps1 full range (semilog-x in E)
  - eps2 full range (semilog-x in E)
  - 4 eV main peak zoom
  - low-E phonon-mode range (Fig 3)

Saved to plot_check_ceo2.png for visual inspection.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')  # for headless savefig
import matplotlib.pyplot as plt
from pathlib import Path
import sys

# ======= 路径配置 =======
SRC = Path(r"D:\xiaorui_macOS\scripts\refellips\RIs\1987-prb-ceo2")
OUT = Path(r"D:\xiaorui_macOS\scripts\refractiveindex_GUI\plot_check_ceo2.png")

def load_csv(path):
    arr = np.loadtxt(path, delimiter=",", comments="#")
    return arr[:, 0], arr[:, 1]

# ======= 加载数据 =======
E1_hi, eps1_hi = load_csv(SRC / "eps1.csv")    # ~0.4-12 eV
E2_hi, eps2_hi = load_csv(SRC / "eps2.csv")
E1_lo, eps1_lo = load_csv(SRC / "eps1_.csv")   # ~0.005-0.1 eV
E2_lo, eps2_lo = load_csv(SRC / "eps2__.csv")
E_peak, eps2_peak = load_csv(SRC / "eps2_.csv")  # 3.15-4.73 eV

# Filter negative E (junk at end of low-E files)
def clean(E, v):
    m = E > 0
    return E[m], v[m]
E1_hi, eps1_hi = clean(E1_hi, eps1_hi)
E2_hi, eps2_hi = clean(E2_hi, eps2_hi)
E1_lo, eps1_lo = clean(E1_lo, eps1_lo)
E2_lo, eps2_lo = clean(E2_lo, eps2_lo)

# 合并网格
grid_hi = np.union1d(E1_hi, E2_hi)
grid_lo = np.union1d(E1_lo, E2_lo)

eps1_hi_i = np.interp(grid_hi, E1_hi, eps1_hi)
eps2_hi_i = np.interp(grid_hi, E2_hi, eps2_hi)
eps1_lo_i = np.interp(grid_lo, E1_lo, eps1_lo)
eps2_lo_i = np.interp(grid_lo, E2_lo, eps2_lo)

# 4 eV主峰区域用密集数据覆盖
mask = (grid_hi >= E_peak.min()) & (grid_hi <= E_peak.max())
eps2_hi_i[mask] = np.interp(grid_hi[mask], E_peak, eps2_peak)

# 合并高低能区
E_all = np.concatenate([grid_lo, grid_hi])
eps1_all = np.concatenate([eps1_lo_i, eps2_hi_i])  # NOTE: would be wrong if interleaved
eps2_all = np.concatenate([eps2_lo_i, eps2_hi_i])

# Fix: actually we want eps1 from eps1_hi_i and eps2 from eps2_hi_i
# Re-do concat properly
eps1_all_hi = np.concatenate([eps1_lo_i, eps1_hi_i])
eps1_all = eps1_all_hi
# eps2 already has dense-peak overlay

# 按能量升序排列
order = np.argsort(E_all)
E_all = E_all[order]
eps1_all = eps1_all[order]
eps2_all = eps2_all[order]

# Drop bad points (very negative eps2)
m = eps2_all > -1.0
E_all, eps1_all, eps2_all = E_all[m], eps1_all[m], eps2_all[m]

# ======= 绘图检查 =======
fig, axes = plt.subplots(2, 2, figsize=(14, 9))

# eps1 全能区
ax = axes[0, 0]
ax.semilogx(E_all, eps1_all, 'b-', lw=1, label='eps1 (Marabelli 1987)')
ax.axhline(0, color='k', lw=0.5)
ax.set_xlabel('Photon Energy (eV)')
ax.set_ylabel('ε₁')
ax.set_title('ε₁ (dielectric function, real part)')
ax.legend()
ax.grid(True, alpha=0.3)

# eps2 全能区
ax = axes[0, 1]
ax.semilogx(E_all, eps2_all, 'r-', lw=1, label='eps2 (Marabelli 1987)')
ax.axhline(0, color='k', lw=0.5)
ax.set_xlabel('Photon Energy (eV)')
ax.set_ylabel('ε₂')
ax.set_title('ε₂ (dielectric function, imaginary part)')
ax.legend()
ax.grid(True, alpha=0.3)

# 4 eV 主峰细节
ax = axes[1, 0]
m4 = (E_all >= 2) & (E_all <= 6)
ax.plot(E_all[m4], eps1_all[m4], 'b-', lw=1, label='ε₁')
ax.plot(E_all[m4], eps2_all[m4], 'r-', lw=1, label='ε₂')
ax.axhline(0, color='k', lw=0.5)
ax.set_xlabel('Photon Energy (eV)')
ax.set_ylabel('ε')
ax.set_title('4 eV main peak (zoom)')
ax.legend()
ax.grid(True, alpha=0.3)

# 低能区细节
ax = axes[1, 1]
ml = E_all < 0.2
ax.semilogx(E_all[ml], eps1_all[ml], 'b-', lw=1, label='ε₁ (phonon tail)')
ax.semilogx(E_all[ml], eps2_all[ml], 'r-', lw=1, label='ε₂ (phonon tail)')
ax.set_xlabel('Photon Energy (eV)')
ax.set_ylabel('ε')
ax.set_title('Low-energy range (phonon modes, Fig 3)')
ax.legend()
ax.grid(True, alpha=0.3)

plt.suptitle('CeO₂ Marabelli & Wachter PRB 36, 1238 (1987) - Sanity Check', fontsize=14)
plt.tight_layout()
plt.savefig(OUT, dpi=150, bbox_inches='tight')
print(f"Saved to {OUT}")