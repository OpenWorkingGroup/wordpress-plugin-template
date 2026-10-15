import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
const { version } = JSON.parse(readFileSync(new URL('../package.json', import.meta.url)));
const slug = 'wordpress-plugin-template';
const run = (...args) => execFileSync('npx', ['--no-install', 'wp-env', ...args], { stdio: 'inherit' });
run('start');
// Use the dedicated tests installation so the live development mount is untouched.
run('run', 'tests-cli', 'wp', 'plugin', 'install', `/var/www/html/wp-content/plugin-artifacts/${slug}-${version}.zip`, '--force', '--activate');
run('run', 'tests-cli', 'wp', 'plugin', 'is-active', slug);
run('run', 'tests-cli', 'wp', 'eval', `require_once ABSPATH . 'wp-admin/includes/plugin.php'; if (get_plugin_data(WP_PLUGIN_DIR . '/${slug}/${slug}.php')['Version'] !== '${version}') { throw new Exception('Installed version mismatch'); }`);
