// wp-env 11 uses the simple-git 3 callable CommonJS export and js-yaml 3
// safeLoad API. Adapt those interfaces to patched dependencies without editing
// installed files or weakening the dependencies' security defaults.
const gitPath = require.resolve('simple-git');
const git = require(gitPath);
require.cache[gitPath].exports = Object.assign(git.simpleGit, git);
const yamlPath = require.resolve('js-yaml');
const yaml = require(yamlPath);
require.cache[yamlPath].exports = { ...yaml, safeLoad: yaml.load, safeDump: yaml.dump };
