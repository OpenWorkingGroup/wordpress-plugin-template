"""Production allowlist packaging; no development files enter installable archives."""
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
SLUG = 'wordpress-plugin-template'
FILES = ['readme.txt', SLUG + '.php']


def validate():
    version = json.loads((ROOT / 'package.json').read_text())['version']
    assert re.fullmatch(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(-rc\.[1-9]\d*)?', version), 'Invalid version'
    source = ROOT / 'plugin' / SLUG
    assert re.search(r'^ \* Version: ' + re.escape(version) + r'$', (source / (SLUG + '.php')).read_text(), re.M)
    assert re.search(r'^Stable tag: ' + re.escape(version) + r'$', (source / 'readme.txt').read_text(), re.M)
    for name in FILES:
        path = source / name
        assert path.is_file() and not path.is_symlink()
        if path.suffix == '.php':
            subprocess.run(['php', '-l', str(path)], check=True)
    return version, source


def package():
    version, source = validate()
    dist = ROOT / 'dist'
    dist.mkdir(exist_ok=True)
    # Remove only generated files owned by this script, avoiding stale RC/stable aliases.
    for path in dist.iterdir():
        if path.name in ('metadata.json', 'SHA256SUMS') or re.fullmatch(SLUG + r'-(latest|[0-9].*)\.zip', path.name):
            path.unlink()
    name = f'{SLUG}-{version}.zip'
    archive = dist / name
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as out:
        for relative in sorted(FILES):
            info = zipfile.ZipInfo(f'{SLUG}/{relative}', (2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            out.writestr(info, (source / relative).read_bytes())
    with zipfile.ZipFile(archive) as check:
        assert check.testzip() is None
        assert sorted(check.namelist()) == sorted(f'{SLUG}/{f}' for f in FILES)
        for f in FILES:
            assert check.read(f'{SLUG}/{f}') == (source / f).read_bytes()
    names = [name]
    if '-rc.' not in version:
        alias = f'{SLUG}-latest.zip'
        (dist / alias).write_bytes(archive.read_bytes())
        names.append(alias)
    checksums = {n: hashlib.sha256((dist / n).read_bytes()).hexdigest() for n in names}
    revision = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True)
    metadata = {'schemaVersion': 1, 'slug': SLUG, 'version': version,
                'sourceRepository': 'OpenWorkingGroup/wordpress-plugin-template',
                'sourceCommit': revision.stdout.strip() if revision.returncode == 0 else None,
                'prerelease': '-rc.' in version, 'sha256': checksums}
    (dist / 'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    checksums['metadata.json'] = hashlib.sha256((dist / 'metadata.json').read_bytes()).hexdigest()
    (dist / 'SHA256SUMS').write_text(''.join(f'{value}  {key}\n' for key, value in checksums.items()))
    print(f'Validated {archive}')


if __name__ == '__main__':
    command = sys.argv[1]
    if command == 'zip':
        package()
    elif command in ('build', 'test'):
        validate()
    else:
        raise SystemExit('Unknown command')
