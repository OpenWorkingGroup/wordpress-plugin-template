import hashlib
import importlib.util
import json
import pathlib
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'scripts'))
from verify import verify

class ArtifactValidation(unittest.TestCase):
    def fixture(self, directory, version='1.2.3'):
        root = pathlib.Path(directory)
        slug = 'wordpress-plugin-template'
        name = f'{slug}-{version}.zip'
        with zipfile.ZipFile(root/name, 'w') as archive:
            for file, content in [(f'{slug}.php', f' * Version: {version}'), ('readme.txt', f'Stable tag: {version}')]:
                info = zipfile.ZipInfo(f'{slug}/{file}')
                info.external_attr = 0o100644 << 16
                archive.writestr(info, content)
        names = [name]
        if '-rc.' not in version:
            alias = f'{slug}-latest.zip'
            (root/alias).write_bytes((root/name).read_bytes())
            names.append(alias)
        hashes = {n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in names}
        meta = dict(schemaVersion=1, sourceRepository='OpenWorkingGroup/wordpress-plugin-template', slug=slug,version=version,sourceCommit='a'*40, prerelease='-rc.' in version,sha256=hashes.copy())
        (root/'metadata.json').write_text(json.dumps(meta))
        hashes['metadata.json']=hashlib.sha256((root/'metadata.json').read_bytes()).hexdigest()
        (root/'SHA256SUMS').write_text(''.join(f'{v}  {k}\n' for k,v in hashes.items()))
        return root, name

    def test_stable_and_rc(self):
        for version in ['1.2.3', '1.2.3-rc.1']:
            with tempfile.TemporaryDirectory() as d:
                self.fixture(d, version)
                verify(d, 'v'+version, 'a'*40)

    def test_corrupted_zip_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root,name=self.fixture(d)
            (root/name).write_bytes(b'corrupted')
            with self.assertRaises(AssertionError): verify(d,'v1.2.3','a'*40)

    def test_wrong_revision_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            self.fixture(d)
            with self.assertRaises(AssertionError): verify(d,'v1.2.3','b'*40)

    def test_unsafe_checksum_path_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root,name=self.fixture(d)
            with (root/'SHA256SUMS').open('a') as f: f.write('0'*64+'  ../outside\n')
            with self.assertRaises(AssertionError): verify(d,'v1.2.3','a'*40)
