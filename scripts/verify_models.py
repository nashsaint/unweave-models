#!/usr/bin/env python3
"""Verify release files before upload, using only the Python standard library."""
import json
from pathlib import Path
import sys
import zipfile
from package_models import MODELS, digest


def verify(root, tag):
    root = Path(root)
    manifest = json.loads((root / 'manifest.json').read_text())
    if manifest.get('release') != tag or manifest.get('engine_interface') != 'unweave-split-core-v1':
        raise ValueError('Release manifest does not match the expected tag or engine.')
    if {model['id'] for model in manifest['models']} != set(MODELS):
        raise ValueError('Both four-stem and six-stem models are required.')
    for model in manifest['models']:
        if model['asset'] != f"{model['id']}-fp32.zip":
            raise ValueError('Unexpected asset filename.')
        file = root / model['asset']
        if file.stat().st_size != model['bytes'] or digest(file) != model['sha256']:
            raise ValueError(f'Checksum mismatch: {file}')
        with zipfile.ZipFile(file) as archive:
            if archive.testzip() is not None:
                raise ValueError(f'Corrupted archive: {file}')
            names = archive.namelist()
            if any(Path(name).is_absolute() or '..' in Path(name).parts for name in names):
                raise ValueError(f'Unsafe archive path: {file}')
            for name in ['LICENSE', 'THIRD_PARTY_NOTICES.md', model['metadata'], f"{model['package']}/Manifest.json"]:
                if name not in names:
                    raise ValueError(f'{file} is missing {name}.')
    sums = dict((name, value) for value, name in (line.split('  ', 1) for line in (root / 'SHA256SUMS').read_text().splitlines()))
    for name in ['htdemucs-fp32.zip', 'htdemucs_6s-fp32.zip', 'manifest.json']:
        if digest(root / name) != sums.get(name):
            raise ValueError(f'SHA256SUMS mismatch: {name}')
    print('Release archives, checksums and model metadata verified.')


if __name__ == '__main__':
    try:
        verify(sys.argv[1], sys.argv[2])
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        raise SystemExit(str(error))
