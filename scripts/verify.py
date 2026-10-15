"""Validate downloaded release artifacts before publishing or extracting."""
import hashlib
import io
import json
import pathlib
import re
import sys
import zipfile


def verify(directory, tag, commit):
    root = pathlib.Path(directory)
    meta = json.loads((root / 'metadata.json').read_text())
    assert re.fullmatch(r'v\d+\.\d+\.\d+(-rc\.[1-9]\d*)?', tag)
    assert meta['schemaVersion'] == 1
    assert meta['sourceRepository'] == 'OpenWorkingGroup/wordpress-plugin-template'
    assert meta['slug'] == 'wordpress-plugin-template'
    assert meta['version'] == tag[1:]
    assert re.fullmatch('[0-9a-f]{40}', commit) and meta['sourceCommit'] == commit
    assert meta['prerelease'] == ('-rc.' in tag)
    slug = meta['slug']
    names = {f'{slug}-{tag[1:]}.zip'}
    if not meta['prerelease']:
        names.add(f'{slug}-latest.zip')
    assert set(meta['sha256']) == names
    expected = names | {'metadata.json'}
    checksums = {}
    for line in (root / 'SHA256SUMS').read_text().splitlines():
        digest, name = line.split('  ')
        assert name in expected and name not in checksums
        assert re.fullmatch('[0-9a-f]{64}', digest)
        checksums[name] = digest
    assert set(checksums) == expected
    for name, digest in checksums.items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest, 'Checksum mismatch'
        if name in names:
            assert meta['sha256'][name] == digest
    for name in names:
        with zipfile.ZipFile(io.BytesIO((root / name).read_bytes())) as archive:
            assert sorted(archive.namelist()) == sorted([f'{slug}/readme.txt', f'{slug}/{slug}.php'])
            assert archive.testzip() is None
            for entry in archive.infolist():
                assert entry.file_size < 1024 * 1024
                assert entry.external_attr >> 16 == 0o100644
            php = archive.read(f'{slug}/{slug}.php').decode()
            readme = archive.read(f'{slug}/readme.txt').decode()
            assert re.search(r'^ \* Version: ' + re.escape(tag[1:]) + '$', php, re.M)
            assert re.search(r'^Stable tag: ' + re.escape(tag[1:]) + '$', readme, re.M)
    if len(names) == 2:
        assert len(set(meta['sha256'].values())) == 1
    return meta


if __name__ == '__main__':
    verify(*sys.argv[1:])
    print('Release metadata, checksums, ZIP paths, contents and versions verified')
