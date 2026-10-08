#!/usr/bin/env python3
"""Offline publisher validation. Never publish a graph solely on filename extension."""
import argparse
import hashlib
import json
import re
import sys
import tarfile
from pathlib import Path
from urllib.parse import urlparse

LIMIT = 2_100_000_000  # Below GitHub Release's per-asset 2 GiB restriction.


def verify_tar(path: Path, max_bytes: int = LIMIT) -> dict:
    if not path.is_file() or path.stat().st_size <= 2048:
        raise ValueError('Missing/empty graph TAR')
    if path.stat().st_size >= max_bytes:
        raise ValueError('TAR is too big for a single GitHub Release asset')
    with tarfile.open(path, 'r:') as archive:
        index = 0
        graph = 0
        for member in archive:
            if not member.isfile():
                continue
            if member.name == 'index.bin':
                index += 1
                if member.size < 1:
                    raise ValueError('Invalid index.bin')
            if member.name.endswith('.gph') and member.size > 0:
                graph += 1
        if index != 1 or graph < 1:
            raise ValueError('Requires one nonempty index.bin and at least one .gph graph')
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    return {'bytes': path.stat().st_size, 'tiles': graph, 'sha256': digest}


def verify_catalog(path: Path, region: str, info: dict):
    data = json.loads(path.read_text(encoding='utf-8'))
    if data.get('schema') != 1 or not isinstance(data.get('packages'), list):
        raise ValueError('Bad catalog schema')
    matches = [p for p in data['packages'] if p.get('id') == region]
    if len(matches) != 1:
        raise ValueError('Wrong number of packages for region')
    entry = matches[0]
    if entry.get('bytes') != info['bytes'] or entry.get('sha256') != info['sha256']:
        raise ValueError('Catalog byte length / SHA256 mismatch')
    url = urlparse(entry.get('url',''))
    if url.scheme != 'https' or url.username or not url.hostname:
        raise ValueError('Only public HTTPS download links supported')
    if url.hostname != 'github.com' or not re.fullmatch(
            r'/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/releases/download/[^/]+/[^/]+\.tar',url.path):
        raise ValueError('Expected an immutable GitHub Release .tar URL')
    return entry


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--tar', required=True, type=Path)
    p.add_argument('--catalog', type=Path)
    p.add_argument('--region', default='jambi')
    p.add_argument('--max-bytes', type=int, default=LIMIT)
    a = p.parse_args()
    info = verify_tar(a.tar, a.max_bytes)
    if a.catalog:
        verify_catalog(a.catalog, a.region, info)
    print(f'PASS: graph tar: tiles={info["tiles"]}, bytes={info["bytes"]}, sha256={info["sha256"]}')
    if a.catalog:
        print(f'PASS: catalog region {a.region} matches tar and immutable GitHub URL')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, tarfile.TarError, KeyError, TypeError) as exc:
        print(f'FAIL: {exc}', file=sys.stderr)
        sys.exit(1)
