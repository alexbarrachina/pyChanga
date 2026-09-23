// Use macOS's image builder directly; no native Node addon is needed to make a DMG.
const { MakerBase } = require('@electron-forge/maker-base');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const { promisify } = require('node:util');
const execFile = promisify(require('node:child_process').execFile);

module.exports = class PyChangaDmgMaker extends MakerBase {
  name = 'pychangaide-dmg';
  defaultPlatforms = ['darwin'];
  isSupportedOnCurrentPlatform() { return process.platform === 'darwin'; }
  async make({dir, makeDir, appName, packageJSON, targetArch}) {
    const staging = await fs.mkdtemp(path.join(os.tmpdir(), 'pychangaide-dmg-'));
    const output = path.resolve(makeDir, `${appName}-${packageJSON.version}-${targetArch}.dmg`);
    try {
      await fs.mkdir(makeDir, {recursive:true});
      await fs.cp(path.join(dir, `${appName}.app`), path.join(staging, `${appName}.app`), {recursive:true, verbatimSymlinks:true});
      await fs.symlink('/Applications', path.join(staging, 'Applications'));
      await execFile('hdiutil', ['create', '-volname', appName, '-srcfolder', staging, '-format', 'UDZO', '-ov', output]);
      return [output];
    } finally { await fs.rm(staging, {recursive:true, force:true}); }
  }
};
