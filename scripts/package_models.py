#!/usr/bin/env python3
"""Package Unweave's portable FP32 Core ML exports as versioned release assets."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parent.parent
MODELS = {
    'htdemucs': ['drums', 'bass', 'other', 'vocals'],
    'htdemucs_6s': ['drums', 'bass', 'other', 'vocals', 'guitar', 'piano'],
}


def digest(file):
    value = hashlib.sha256()
    with file.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()


def write_member(archive, name, file):
    if file.is_symlink():
        raise ValueError(f'Symlinks are not allowed in model assets: {file}')
    # Stable timestamps and permissions make archives reproducible.
    info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    with file.open('rb') as source, archive.open(info, 'w', force_zip64=True) as target:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            target.write(chunk)


def package(source, output, tag):
    if not re.fullmatch(r'models-v[0-9]+(?:\.[0-9]+)*', tag):
        raise ValueError('Use a versioned tag such as models-v1 or models-v1.1.')
    source, output = Path(source), Path(output)
    # Validate both models before writing any release output.
    inputs = []
    for name, stems in MODELS.items():
        folder = source / f'{name}.mlpackage'
        metadata = source / f'{name}.json'
        info = json.loads(metadata.read_text())
        if info.get('name') != name or info.get('sources') != stems or info.get('samplerate') != 44100:
            raise ValueError(f'Unexpected metadata for {name}.')
        for key, expected in [('segment_samples', 343980), ('frames', 336), ('nfft', 4096), ('hop', 1024)]:
            if info.get(key) != expected:
                raise ValueError(f'Unexpected {key} for {name}: {info.get(key)}')
        for relative in ['Manifest.json', 'Data/com.apple.CoreML/model.mlmodel', 'Data/com.apple.CoreML/weights/weight.bin']:
            file = folder / relative
            if not file.is_file() or not file.stat().st_size:
                raise ValueError(f'Missing or empty model file: {file}')
        files = sorted(p for p in folder.rglob('*') if p.is_file() and p.name != '.DS_Store')
        if folder.is_symlink() or any(p.is_symlink() for p in folder.rglob('*')):
            raise ValueError(f'Symlinks are not allowed in {folder}.')
        inputs.append((name, folder, metadata, info, files))
    output.mkdir(parents=True, exist_ok=True)
    entries = []
    for name, folder, metadata, info, files in inputs:
        filename = f'{name}-fp32.zip'
        destination = output / filename
        temporary = destination.with_suffix('.zip.partial')
        try:
            with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
                for file in files:
                    write_member(archive, f'{folder.name}/{file.relative_to(folder).as_posix()}', file)
                write_member(archive, f'{name}.json', metadata)
                write_member(archive, 'LICENSE', ROOT / 'LICENSE')
                write_member(archive, 'THIRD_PARTY_NOTICES.md', ROOT / 'THIRD_PARTY_NOTICES.md')
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)
        entries.append({
            'id': name, 'asset': filename, 'bytes': destination.stat().st_size,
            'sha256': digest(destination), 'package': folder.name, 'metadata': metadata.name,
            **{key: value for key, value in info.items() if key != 'name'},
        })
        print(f'{filename}: {destination.stat().st_size / 1024 / 1024:.1f} MiB', flush=True)
    manifest = {
        'schema_version': 1, 'release': tag, 'format': 'coreml-package', 'precision': 'float32',
        'minimum_macos': '14.0', 'engine_interface': 'unweave-split-core-v1', 'models': entries,
    }
    manifest_file = output / 'manifest.json'
    manifest_file.write_text(json.dumps(manifest, indent=2) + '\n')
    assets = [output / entry['asset'] for entry in entries] + [manifest_file]
    (output / 'SHA256SUMS').write_text(''.join(f'{digest(asset)}  {asset.name}\n' for asset in assets))
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True, help='Directory containing .mlpackage exports and model JSON metadata')
    parser.add_argument('--tag', default='models-v1')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    package(args.source, args.output or ROOT / 'dist' / args.tag, args.tag)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError) as error:
        raise SystemExit(str(error))
