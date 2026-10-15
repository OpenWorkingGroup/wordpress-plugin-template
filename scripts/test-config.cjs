require('./wp-env-compat.cjs');
const assert = require('node:assert/strict');
const { loadConfig } = require('@wordpress/env/lib/config');
const compose = require(require('node:path').resolve(require.resolve('@wordpress/env/lib/config'), '../../runtime/docker/build-docker-compose-config.js'));
(async () => {
  const config = await loadConfig(process.cwd(), null, { resolvePorts: false });
  assert.equal(config.env.development.pluginSources.length, 1);
  assert.equal(config.env.tests.pluginSources.length, 0);
  const generated = compose(config);
  const expected = `${process.cwd()}/dist:/var/www/html/wp-content/plugin-artifacts`;
  assert(generated.services['tests-cli'].volumes.includes(expected));
  assert(generated.services.cli.volumes.includes(expected));
  assert(!generated.services['tests-cli'].volumes.some(p => p.includes('/wp-content/plugins/wordpress-plugin-template')));
  const yaml = require('js-yaml');
  assert.deepEqual(yaml.safeLoad(yaml.dump(generated)), generated);
  const git = require('simple-git')({ baseDir: process.cwd() });
  assert.equal(await git.checkIsRepo('root'), true);
  console.log('Development mount, isolated ZIP test environment, and artifact mounts verified.');
})().catch(error => { console.error(error); process.exitCode = 1; });
