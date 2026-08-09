# -*- coding: utf-8 -*-
"""Test the Pu database setup."""
import yaml
from pathlib import Path

LOCAL_DB_PATH = Path(r'D:\xiaorui_macOS\scripts\refractiveindex\pu_data\db')
pu_cat = yaml.safe_load(open(LOCAL_DB_PATH / 'catalog-pu.yml', 'r', encoding='utf-8'))

print(f'Pu catalog type: {type(pu_cat)}')
print(f'Pu catalog length: {len(pu_cat)}')

# Check structure
item = pu_cat[0]
print(f'Shelf: {item["SHELF"]}')
print(f'Name: {item["name"]}')
print(f'Content items: {len(item["content"])}')

# Find BOOK entries
for c in item['content']:
    if 'BOOK' in c:
        print(f'  Book: {c["BOOK"]} ({c["name"]})')
        for p in c['content']:
            if 'PAGE' in p:
                print(f'    Page: {p["PAGE"]} -> {p["data"]}')

# Check data files exist
pu_dir = LOCAL_DB_PATH / 'Pu'
for fn in ['delta-Pu.yml', 'Pu-oxide-41nm.yml', 'Pu-oxide-48nm.yml']:
    p = pu_dir / fn
    print(f'  {fn}: exists={p.exists()}')

# Test merge with CAT_NK
DB_PATH = Path(r'C:\Users\zhuxi\.refractiveindex.info-database')
CAT_NK = yaml.safe_load(open(DB_PATH / 'catalog-nk.yml', 'r', encoding='utf-8'))
print(f'\nSystem catalog: {len(CAT_NK)} entries')
CAT_NK.extend(pu_cat)
print(f'After merge: {len(CAT_NK)} entries')

# Build index with local_base
def _build_index(catalog, local_base=None):
    idx = {}
    for shelf in catalog:
        if 'SHELF' not in shelf:
            continue
        sid = shelf['SHELF']
        for book in shelf.get('content', []):
            if 'BOOK' not in book:
                continue
            bid = book['BOOK']
            for page in book.get('content', []):
                if 'PAGE' not in page:
                    continue
                pid = page['PAGE']
                data_path = page['data']
                if local_base is not None and data_path.startswith('Pu/'):
                    idx[(sid, bid, pid)] = LOCAL_DB_PATH / data_path
                else:
                    idx[(sid, bid, pid)] = DB_PATH / 'data' / data_path
    return idx

INDEX_NK = _build_index(CAT_NK, LOCAL_DB_PATH)
pu_keys = [(sid, bid, pid) for (sid, bid, pid) in INDEX_NK if sid == 'Pu']
print(f'\nPu keys in INDEX_NK: {pu_keys}')

# Verify paths
for key in pu_keys:
    path = INDEX_NK[key]
    print(f'  {key} -> {path} (exists={path.exists()})')
