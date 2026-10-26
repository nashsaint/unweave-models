import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from package_models import MODELS, digest, package
from verify_models import verify


class ModelReleaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        self.output = self.root / 'release'
        for name, sources in MODELS.items():
            metadata = {'name': name, 'sources': sources, 'samplerate': 44100,
                        'segment_samples': 343980, 'frames': 336, 'nfft': 4096, 'hop': 1024}
            (self.source / f'{name}.json').write_text(json.dumps(metadata))
            folder = self.source / f'{name}.mlpackage'
            (folder / 'Data/com.apple.CoreML/weights').mkdir(parents=True)
            (folder / 'Manifest.json').write_text('{"test": true}')
            (folder / 'Data/com.apple.CoreML/model.mlmodel').write_bytes(b'fixture model')
            (folder / 'Data/com.apple.CoreML/weights/weight.bin').write_bytes(bytes(range(256)) * 10)

    def tearDown(self):
        self.tmp.cleanup()

    def test_archives_include_metadata_and_licence_and_match_manifest(self):
        manifest = package(self.source, self.output, 'models-v1')
        verify(self.output, 'models-v1')
        for model in manifest['models']:
            with zipfile.ZipFile(self.output / model['asset']) as archive:
                self.assertIn(b'Meta Platforms', archive.read('LICENSE'))
                metadata = json.loads(archive.read(model['metadata']))
                self.assertEqual(metadata['sources'], MODELS[model['id']])
                self.assertFalse(any(name.startswith('/') or '..' in name.split('/') for name in archive.namelist()))

    def test_archives_are_reproducible(self):
        package(self.source, self.output, 'models-v1')
        first = {file.name: digest(file) for file in self.output.iterdir()}
        package(self.source, self.output, 'models-v1')
        self.assertEqual(first, {file.name: digest(file) for file in self.output.iterdir()})

    def test_corrupted_archive_is_rejected(self):
        package(self.source, self.output, 'models-v1')
        with (self.output / 'htdemucs-fp32.zip').open('ab') as file:
            file.write(b'corrupted')
        with self.assertRaisesRegex(ValueError, 'Checksum mismatch'):
            verify(self.output, 'models-v1')

    def test_missing_model_prevents_partial_release(self):
        (self.source / 'htdemucs_6s.mlpackage/Data/com.apple.CoreML/weights/weight.bin').unlink()
        with self.assertRaisesRegex(ValueError, 'Missing or empty'):
            package(self.source, self.output, 'models-v1')
        self.assertFalse(self.output.exists())

    def test_unknown_engine_shapes_are_rejected(self):
        file = self.source / 'htdemucs.json'
        data = json.loads(file.read_text())
        data['segment_samples'] = 100
        file.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'Unexpected segment_samples'):
            package(self.source, self.output, 'models-v1')

    def test_symlinks_are_rejected(self):
        (self.source / 'htdemucs.mlpackage/outside').symlink_to('/etc/hosts')
        with self.assertRaisesRegex(ValueError, 'Symlinks'):
            package(self.source, self.output, 'models-v1')


if __name__ == '__main__':
    unittest.main()
