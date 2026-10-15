"""Mirror releases, not upstream workflow code, with separate scoped credentials."""
import json
import os
import pathlib
import re
import subprocess
import tempfile
from verify import verify

UPSTREAM = 'OpenWorkingGroup/wordpress-plugin-template'
name = os.environ['DOWNSTREAM_REPOSITORY']
assert re.fullmatch('[A-Za-z0-9_.-]+', name) and name not in ('.', '..')
DOWNSTREAM = 'ByteableHub/' + name


def gh(token, *args, json_result=False):
    env = dict(os.environ, GH_TOKEN=token)
    result = subprocess.run(['gh', *args], env=env, text=True, capture_output=True, check=True)
    return json.loads(result.stdout) if json_result else result.stdout


up, down = os.environ['UPSTREAM_TOKEN'], os.environ['DOWNSTREAM_TOKEN']
# Pre-existing destination required: this credential cannot create repositories.
gh(down, 'api', f'repos/{DOWNSTREAM}', json_result=True)
releases = gh(up, 'api', '--paginate', '--slurp', f'repos/{UPSTREAM}/releases?per_page=100', json_result=True)
all_releases = [r for page in releases for r in page]
stable = [r['tag_name'] for r in all_releases if not r['draft'] and not r['prerelease'] and re.fullmatch(r'v[0-9]+\.[0-9]+\.[0-9]+', r['tag_name'])]
latest = max(stable, key=lambda tag: tuple(map(int, tag[1:].split('.'))), default=None)
for release in reversed(all_releases):
    tag = release['tag_name']
    if release['draft'] or not re.fullmatch(r'v\d+\.\d+\.\d+(-rc\.[1-9]\d*)?', tag):
        continue
    commit = gh(up, 'api', f'repos/{UPSTREAM}/commits/{tag}', json_result=True)['sha']
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        gh(up, 'release', 'download', tag, '--repo', UPSTREAM, '--dir', tmp)
        meta = verify(tmp, tag, commit)
        assert release['prerelease'] == meta['prerelease']
        existing = gh(down, 'api', '--paginate', '--slurp', f'repos/{DOWNSTREAM}/releases?per_page=100', json_result=True)
        found = next((r for page in existing for r in page if r['tag_name'] == tag), None)
        if found:
            assert not found['draft'], 'Incomplete draft requires maintainer recovery'
            with tempfile.TemporaryDirectory() as previous:
                gh(down, 'release', 'download', tag, '--repo', DOWNSTREAM, '--dir', previous)
                verify(previous, tag, commit)
                for filename in ['metadata.json', 'SHA256SUMS', *meta['sha256']]:
                    assert (pathlib.Path(previous) / filename).read_bytes() == (root / filename).read_bytes(), 'Existing mirror differs; refusing overwrite'
            if tag == latest:
                gh(down, 'release', 'edit', tag, '--repo', DOWNSTREAM, '--latest=true')
            continue
        # Keep artifact bytes identical. Metadata records authoritative upstream revision.
        assets = [str(root / n) for n in ['metadata.json', 'SHA256SUMS', *meta['sha256']]]
        args = ['release', 'create', tag, '--repo', DOWNSTREAM, '--draft', '--title', tag,
                '--notes', f'Mirrored from https://github.com/{UPSTREAM}/releases/tag/{tag}\nUpstream commit: {commit}', *assets]
        if meta['prerelease']:
            args.append('--prerelease')
        gh(down, *args)
        gh(down, 'release', 'edit', tag, '--repo', DOWNSTREAM, '--draft=false', '--latest=' + str(tag == latest).lower())
        with tempfile.TemporaryDirectory() as downloaded:
            gh(down, 'release', 'download', tag, '--repo', DOWNSTREAM, '--dir', downloaded)
            verify(downloaded, tag, commit)
        print(f'Published and verified source artifacts for {DOWNSTREAM} {tag}')
