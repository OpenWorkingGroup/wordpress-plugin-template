"""Publish only verified artifacts; never overwrite an existing release."""
import json
import os
import subprocess
from package import ROOT, validate

version, _ = validate()
tag = os.environ['GITHUB_REF_NAME']
assert tag == 'v' + version, 'Tag must match package and plugin versions'
metadata = json.loads((ROOT / 'dist/metadata.json').read_text())
assert metadata['sourceCommit'] == os.environ['GITHUB_SHA'], 'Commit mismatch'
assert metadata['sourceRepository'] == os.environ['GITHUB_REPOSITORY'], 'Repository mismatch'
subprocess.run(['python3', 'scripts/verify.py', 'dist', tag, os.environ['GITHUB_SHA']], check=True)
existing = json.loads(subprocess.check_output(['gh', 'release', 'list', '--limit', '1000', '--json', 'tagName,isPrerelease,isDraft'], text=True))
current = tuple(map(int, version.split('-')[0].split('.')))
newest = not metadata['prerelease'] and all(tuple(map(int, r['tagName'][1:].split('.'))) <= current for r in existing if not r['isPrerelease'] and not r['isDraft'] and __import__('re').fullmatch(r'v[0-9]+\.[0-9]+\.[0-9]+', r['tagName']))
args = ['gh', 'release', 'create', tag, '--verify-tag', '--title', tag,
        '--notes', f'Install the attached plugin ZIP. Source revision: {metadata["sourceCommit"]}', '--draft']
args += [str(p) for p in sorted((ROOT / 'dist').iterdir()) if p.is_file()]
if metadata['prerelease']:
    args += ['--prerelease']
subprocess.run(args, check=True)
# Upload completes before the release becomes visible.
subprocess.run(['gh', 'release', 'edit', tag, '--draft=false', '--latest=' + str(newest).lower()], check=True)
subprocess.run(['gh', 'release', 'view', tag, '--json', 'url,isDraft,isPrerelease,assets'], check=True)
