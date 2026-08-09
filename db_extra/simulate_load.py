# -*- coding: utf-8 -*-
"""Simulate GUI loading of Pu data."""
import sys

import numpy as np
from scipy.interpolate import interp1d
import yaml
from pathlib import Path

# This script mirrors the GUI's data loader. DBs are read from the same
# directories as nk_GUI.py:
#   - bundled system DB:    <repo>/db/    (refractiveindex.info, CC0)
#   - extra / custom DB:    <repo>/db_extra/   (Pu, Sc, ...)
# Both are relative to this script's parent directory.
LOCAL_DB_PATH = Path(__file__).resolve().parent
BUNDLED_DB_PATH = LOCAL_DB_PATH.parent / "db"

import refractiveindex.refractiveindex as ri
DB_PATH = Path(ri._DEFAULT_DB_PATH) if not BUNDLED_DB_PATH.exists() else BUNDLED_DB_PATH

def _load_material_data(shelf, book, page):
    """Simulate _load_material_data from the GUI."""
    key = (shelf, book, page)
    
    # Build index
    INDEX_NK = {}
    with open(DB_PATH / 'catalog-nk.yml', 'r', encoding='utf-8') as f:
        CAT_NK = yaml.safe_load(f)
    pu_cat_path = LOCAL_DB_PATH / 'catalog-pu.yml'
    if pu_cat_path.exists():
        with open(pu_cat_path, 'r', encoding='utf-8') as f:
            CAT_PU = yaml.safe_load(f)
        CAT_NK.extend(CAT_PU)
    
    for s in CAT_NK:
        if 'SHELF' not in s:
            continue
        sid = s['SHELF']
        for b in s.get('content', []):
            if 'BOOK' not in b:
                continue
            bid = b['BOOK']
            for p in b.get('content', []):
                if 'PAGE' not in p:
                    continue
                pid = p['PAGE']
                data_path = p['data']
                if data_path.startswith('Pu/'):
                    INDEX_NK[(sid, bid, pid)] = LOCAL_DB_PATH / data_path
                else:
                    INDEX_NK[(sid, bid, pid)] = DB_PATH / 'data' / data_path
    
    if key not in INDEX_NK:
        raise KeyError(f"Material not found: {key}")
    
    with open(INDEX_NK[key], 'r', encoding='utf-8') as f:
        mat = yaml.safe_load(f)
    
    n_func = k_func = None
    wl_range = None
    
    for data in mat.get('DATA', []):
        dtype = data.get('type', '').split()
        cat, sub = dtype[0], dtype[1] if len(dtype) > 1 else None
        
        if cat == 'tabulated':
            wl_list, c1_list, c2_list = [], [], []
            for line in data['data'].strip().split('\n'):
                p = line.split()
                wl_list.append(float(p[0]))
                c1_list.append(float(p[1]))
                c2_list.append(float(p[2]) if len(p) > 2 else None)
            wl_um = np.array(wl_list)
            c1 = np.array(c1_list)
            c2 = np.array([x for x in c2_list if x is not None])
            
            mk_i = lambda y: interp1d(wl_um, y, kind='cubic', bounds_error=False,
                                      fill_value=(y[0], y[-1]))
            if sub == 'n':
                n_func = mk_i(c1)
                wl_range = (wl_um[0] * 1000, wl_um[-1] * 1000)
            elif sub == 'k':
                k_func = mk_i(c1)
                wl_range = (wl_um[0] * 1000, wl_um[-1] * 1000)
            elif sub == 'nk':
                n_func = mk_i(c1)
                k_func = mk_i(c2)
                wl_range = (wl_um[0] * 1000, wl_um[-1] * 1000)
    
    if wl_range is None:
        raise ValueError(f'No wavelength range for {key}')
    
    wl_nm = np.linspace(wl_range[0], wl_range[1], 800)
    wl_um = wl_nm / 1000.0
    n = np.asarray(n_func(wl_um)) if n_func else np.zeros_like(wl_nm)
    k = np.asarray(k_func(wl_um)) if k_func else np.zeros_like(wl_nm)
    
    return wl_nm, n, k

# Test loading delta-Pu
print('Loading delta-Pu...')
wl, n, k = _load_material_data('Pu', 'delta-Pu', 'nk-Dinh2019')
print(f'  Wavelength range: {wl[0]:.1f} - {wl[-1]:.1f} nm')
print(f'  n range: {n.min():.4f} - {n.max():.4f}')
print(f'  k range: {k.min():.4f} - {k.max():.4f}')
print(f'  Data points: {len(wl)}')
print(f'  Sample at 500nm: n={interp1d(wl, n)(500):.4f}, k={interp1d(wl, k)(500):.4f}')
print(f'  Sample at 700nm: n={interp1d(wl, n)(700):.4f}, k={interp1d(wl, k)(700):.4f}')

print('\nLoading Pu oxide 41nm...')
wl2, n2, k2 = _load_material_data('Pu', 'Pu-oxide-41nm', 'nk-41nm-Dinh2019')
print(f'  Wavelength range: {wl2[0]:.1f} - {wl2[-1]:.1f} nm')
print(f'  n range: {n2.min():.4f} - {n2.max():.4f}')
print(f'  k range: {k2.min():.4f} - {k2.max():.4f}')
print(f'  Sample at 500nm: n={interp1d(wl2, n2)(500):.4f}, k={interp1d(wl2, k2)(500):.4f}')

print('\nAll loads successful!')
