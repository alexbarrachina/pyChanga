const path = require('node:path');
const fs = require('node:fs');
const {createHash} = require('node:crypto');
const PyChangaDmgMaker = require('./scripts/maker-dmg.cjs');

const target = `${process.platform}-${process.arch}`;
const runtime = path.join(__dirname, 'runtime', target, 'runtime');
const signing = process.env.SIGN_RELEASE === 'true';
if (signing && process.platform === 'darwin' && !process.env.APPLE_SIGN_IDENTITY) throw new Error('APPLE_SIGN_IDENTITY is required for a signed release');
if (signing && process.platform === 'win32' && !process.env.WINDOWS_CERTIFICATE_FILE) throw new Error('WINDOWS_CERTIFICATE_FILE is required for a signed release');

module.exports = {
  outDir: 'out/release',
  packagerConfig: {
    asar: true,
    appBundleId: 'org.pychanga.ide',
    executableName: 'pyChangaIDE',
    appCategoryType: 'public.app-category.education',
    prune: false,
    ignore: filename => filename !== '' && !/^\/(dist($|\/)|package\.json$)/.test(filename.replace(/\\/g, '/')),
    extraResource: [runtime, path.join(__dirname, 'examples'), path.join(__dirname, 'THIRD_PARTY_NOTICES.md')],
    ...(signing && process.platform === 'darwin' ? {
      osxSign: {identity: process.env.APPLE_SIGN_IDENTITY, optionsForFile: () => ({
        entitlements: path.join(__dirname, 'scripts', 'entitlements.plist'), hardenedRuntime: true,
      })},
      osxNotarize: {appleId: process.env.APPLE_ID, appleIdPassword: process.env.APPLE_APP_PASSWORD, teamId: process.env.APPLE_TEAM_ID},
    } : {}),
  },
  hooks: {
    prePackage: async () => {
      if (!fs.existsSync(path.join(runtime, 'runtime-manifest.json'))) throw new Error('Run python3 scripts/prepare_runtime.py before packaging');
      const fontSource = 'pyChanga_package/pyChanga/sounds/pyChanga.sf2';
      const font = fs.readFileSync(path.join(__dirname, fontSource));
      if (font.toString('ascii', 0, 4) !== 'RIFF' || font.toString('ascii', 8, 12) !== 'sfbk') throw new Error('Invalid pyChanga.sf2 SoundFont');
      // Refresh Python sources after edits without downloading the runtime again.
      fs.rmSync(path.join(runtime, 'packages', 'musica'), {recursive: true, force: true});
      fs.rmSync(path.join(runtime, 'packages', 'pyChanga'), {recursive: true, force: true});
      fs.cpSync(path.join(__dirname, 'pyChanga_package', 'pyChanga'), path.join(runtime, 'packages', 'pyChanga'), {
        recursive: true, filter: source => !source.includes('__pycache__') && !source.endsWith('Emu_Planet_Phatt_Hip_Hop.sf2'),
      });
      const manifestPath = path.join(runtime, 'runtime-manifest.json');
      const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
      manifest.soundfont = {source: fontSource, soundfontSha256: createHash('sha256').update(font).digest('hex')};
      fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2) + '\n');
      fs.copyFileSync(path.join(__dirname, 'THIRD_PARTY_NOTICES.md'), path.join(runtime, 'THIRD_PARTY_NOTICES.md'));
      fs.copyFileSync(path.join(__dirname, 'node_modules', 'monaco-editor', 'LICENSE'), path.join(runtime, 'Monaco-LICENSE.txt'));
    },
  },
  makers: [
    new PyChangaDmgMaker(),
    {name: '@electron-forge/maker-zip', platforms: ['darwin', 'win32']},
    {name: '@electron-forge/maker-squirrel', platforms: ['win32'], config: {
      name: 'pyChangaIDE', authors: 'pyChangaIDE', description: 'Python live coding for musicians',
      ...(signing ? {certificateFile: process.env.WINDOWS_CERTIFICATE_FILE, certificatePassword: process.env.WINDOWS_CERTIFICATE_PASSWORD} : {}),
    }},
  ],
};
