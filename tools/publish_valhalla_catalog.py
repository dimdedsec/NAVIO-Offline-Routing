#!/usr/bin/env python3
"""Create/update a NAVIO region manifest for an already hosted pre-built Valhalla tar.

Example:
python tools/publish_valhalla_catalog.py --id jambi --label Jambi \
  --tar NAVIO_Valhalla_Graph/valhalla_tiles.tar \
  --url https://YOUR-HOST/routing/jambi.tar --output catalog.json

This tool DOES NOT host or build tiles; operator must publish TAR & catalog via HTTPS.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlparse


def publish(name, label, tar, url, output):
    if not re.fullmatch(r'[a-z0-9-]{2,40}', name):
        raise ValueError('Invalid region ID')
    uri = urlparse(url)
    if uri.scheme != 'https' or not uri.hostname or uri.username:
        raise ValueError('Only HTTPS URLs without credentials are allowed')
    if not tar.is_file() or tar.stat().st_size < 2049:
        raise ValueError('Missing/empty Valhalla TAR')
    import tarfile
    with tarfile.open(tar, 'r:') as content:
        seen_index = False
        seen_graph = False
        for record in content:
            if record.name == 'index.bin': seen_index = True
            if record.name.endswith('.gph'): seen_graph = True
        if not (seen_index and seen_graph):
            raise ValueError('Not a Valhalla extract (index.bin/.gph missing)')
    digest = hashlib.sha256()
    with tar.open('rb') as inp:
        for chunk in iter(lambda: inp.read(1024 * 1024), b''):
            digest.update(chunk)
    data = json.loads(output.read_text()) if output.exists() else {'schema': 1, 'packages': []}
    if data.get('schema') != 1: raise ValueError('Unknown manifest schema')
    offer = {'id': name, 'label': label, 'url': url, 'bytes': tar.stat().st_size, 'sha256': digest.hexdigest()}
    data['packages'] = [x for x in data['packages'] if x.get('id') != name] + [offer]
    data['packages'].sort(key=lambda x: x['id'])
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    print(f'Published catalog entry {name}: {offer["bytes"]} bytes, SHA-256 {offer["sha256"]}')
    print('Upload BOTH the .tar and catalog.json to the HTTPS host at the specified URLs')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--id', required=True)
    p.add_argument('--label', required=True)
    p.add_argument('--tar', required=True, type=Path)
    p.add_argument('--url', required=True)
    p.add_argument('--output', type=Path, default=Path('catalog.json'))
    a = p.parse_args()
    publish(a.id, a.label, a.tar, a.url, a.output)
