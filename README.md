# Open Working Group WordPress plugin template

Implementation for `OpenWorkingGroup/wordpress-plugin-template`. Check GitHub Actions for current CI results; no release is implied by this source repository. ByteableHub is a GitHub organization only.

## Development

Prerequisites: Git, PHP 8.2+, Python 3.10+, Node 24.18+, npm 11.16+, and a running Docker installation with Compose support. GitHub Actions runners also need GitHub CLI (provided on GitHub-hosted Ubuntu).

```sh
npm ci
npm run dev
npm test
npm run build
npm run zip
npm run test:package
npm run stop
```

`dev` mounts `plugin/wordpress-plugin-template` into WordPress. Edit PHP files directly; this minimal plugin has no JavaScript compilation step. `build` validates source and version consistency. `test` adds artifact integrity tests. `zip` makes deterministic production-only archives. `test:package` installs and activates the ZIP in wp-env's separate tests instance, then verifies its installed version. It replaces the template plugin only in that test instance. The development mount remains in the development instance. The environment remains running until `stop` is called.

The default wp-env development login is `admin` / `password`; use this environment only for local development. Documentation: https://developer.wordpress.org/block-editor/reference-guides/packages/packages-env/

## Customize before publishing a real plugin

Replace the slug, namespace, source repository, plugin name, contributor placeholder and metadata across the source, scripts, tests and workflows. This template is not itself a finished directory submission. Add production files to the explicit packaging allowlist in `scripts/package.py` and matching archive validation in `scripts/verify.py`. Add behavioral tests for your plugin.

Keep `package.json`, lockfile root version, PHP header and `readme.txt` stable tag synchronized. Supported tags are `vX.Y.Z` and `vX.Y.Z-rc.N`, with N starting at 1. Commit all changes before tagging. The metadata records the source commit; a standalone local copy without a Git commit has null provenance and cannot pass release verification.

## Release workflow

Push a matching version tag after CI passes. The release workflow runs validation and a Docker ZIP installation test before publishing. It creates a draft, uploads all assets, and only then publishes it. RC releases are marked prerelease and have no latest ZIP alias. Stable releases include:

- `wordpress-plugin-template-X.Y.Z.zip`
- `wordpress-plugin-template-latest.zip` (identical bytes)
- `metadata.json` (repository, exact source commit, version, channel and ZIP SHA-256)
- `SHA256SUMS` (ZIP and metadata checksums)

The stable URL is `https://github.com/OpenWorkingGroup/wordpress-plugin-template/releases/latest/download/wordpress-plugin-template-latest.zip` once a stable release exists. Older stable version tags do not replace a newer latest release (comparison considers up to 1,000 existing upstream releases). Published assets are never overwritten. A failed draft must be inspected and removed/recovered by a maintainer before retrying the same tag. Tag rules should restrict release tag creation and prohibit movement/deletion. Require review for workflow changes and use protected deployment environments.

Checksums detect corruption; they are not independent signatures. The authenticated GitHub repository and tag-to-commit lookup establish the trust boundary. Workflow dependencies are pinned to exact commits.

## ByteableHub mirroring

Create and initialize a corresponding destination repository in the **ByteableHub GitHub organization**. Repository provisioning is an administrative setup step, deliberately separate from the narrowly scoped runtime credential. Install a GitHub App on only the destination repository, granting Contents: write and Metadata: read. Do not grant organization administration or workflow-writing permissions.

Upstream repository variables:

| Variable | Value |
| --- | --- |
| `BYTEABLEHUB_MIRROR_ENABLED` | `true` only after setup |
| `BYTEABLEHUB_REPOSITORY` | Destination repository name, without owner |
| `BYTEABLEHUB_APP_ID` | Installed GitHub App ID |

In the protected `byteablehub` environment, set `BYTEABLEHUB_APP_PRIVATE_KEY`. The workflow issues a short-lived token scoped to that one repository; the action revokes it after the job. Upstream reads use the separate read-only upstream token. No token or private key belongs in source control.

Mirroring runs directly after release publication through a reusable workflow, in a separate job after successful upstream publication. A schedule every six hours and manual dispatch reconcile missed releases. The schedule requires the workflow on the default branch and GitHub scheduled workflows to remain enabled. It reads all upstream release pages, resolves each release tag to its upstream commit, validates metadata, checksums and archive contents, and transfers identical artifacts. RC status is preserved. Existing matching mirrors are verified and skipped; mismatches fail without overwrite. Destination assets are downloaded and verified after new publication.

The mirror copies installable distribution assets and provenance, not upstream development workflows or Git history. The destination release tag belongs to its distribution repository; `metadata.json` identifies the authoritative upstream source commit. Mirroring failure does not roll back or prevent the already published upstream release.

## Optional WordPress.org deployment

Keep `WPORG_APPROVED` unset until WordPress.org has approved the actual plugin and assigned the matching slug. Configure the protected `wordpress-org` environment, with secrets `WPORG_SVN_USERNAME` and `WPORG_SVN_PASSWORD`. Set repository variable `WPORG_APPROVED=true` to enable stable-only deployment. The job downloads and verifies the already published ZIP, extracts only the verified production files, and deploys those via the pinned 10up SVN deployment action. RCs never deploy. Directory approval and valid SVN access cannot be inferred from successful GitHub releases.

See https://github.com/10up/action-wordpress-plugin-deploy for the action's prerequisites. After enabling, verify the SVN tag and WordPress.org download/version before reporting publication successful.

## Local validation and remaining blockers

Completed: PHP syntax and header/readme version checks; deterministic ZIP contents; stable and RC fixture acceptance; corruption, wrong-commit and unsafe-checksum-path rejection tests; JavaScript syntax check; npm lockfile resolution.

Not completed: Docker startup, mounted plugin behavior, ZIP installation/activation, GitHub CI execution, release publication, downstream mirroring, or SVN deployment. The repository was created by its owner. Docker is absent in the implementation machine’s shell; remote write access and CI results must be verified separately. No secrets or organization permissions have been configured.

The pinned `@wordpress/env` 11.17.0 dependency tree passes `npm audit` with zero reported vulnerabilities after exact overrides for `simple-git` 4.0.2, `js-yaml` 4.3.2 and `qs` 6.16.1. `scripts/wp-env-compat.cjs` adapts wp-env's older callable Git export and YAML safeLoad/safeDump names to the patched APIs. Use the npm scripts (or `npm run wp-env -- ...`) so this adapter is loaded; do not invoke the unwrapped wp-env binary directly. Configuration/YAML round-trip and Git API checks cover the adapter locally; Docker CI verifies the complete workflow. Remove the adapter and overrides when upstream wp-env supports patched dependencies directly. CI and releases reject high/critical audit findings.

The implementation machine's Node 22 is below the resolved tooling's Node 24 requirement. Local PHP, packaging, configuration and CLI checks passed, but full runtime support requires the documented Node/npm versions. CI requests Node 24.
