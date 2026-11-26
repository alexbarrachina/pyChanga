// Copyright (C) 2026 Alex Barrachina
// SPDX-License-Identifier: GPL-3.0-only

// Builds out/installer/pyChangaIDE-<version>-win-x64-setup.exe with Inno Setup 6
// from the application folder that `npm run make` packaged.

import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const {productName, version} = JSON.parse(fs.readFileSync(path.join(root, 'package.json'), 'utf8'));
const appDir = path.join(root, 'out', 'release', `${productName}-win32-x64`);
const outDir = path.join(root, 'out', 'installer');

if (process.platform !== 'win32') throw new Error('Build the Windows installer on Windows');
for (const required of [`${productName}.exe`, 'resources/app.asar', 'resources/runtime/runtime-manifest.json',
  'resources/runtime/python/python.exe', 'resources/runtime/packages/pyChanga', 'resources/runtime/packages/pyo',
  'resources/runtime/native']) {
  if (!fs.existsSync(path.join(appDir, required))) throw new Error(`${path.join(appDir, required)} is missing. Run npm run make first.`);
}

const firstExisting = (candidates, fallback) => candidates.filter(Boolean).find(file => fs.existsSync(file)) ?? fallback;
// Newest version first among folders such as "Inno Setup 6".
const versionsIn = (folder, prefix) => !folder || !fs.existsSync(folder) ? [] : fs.readdirSync(folder)
  .filter(name => name.startsWith(prefix)).sort((a, b) => b.localeCompare(a, undefined, {numeric: true}))
  .map(name => path.join(folder, name));
const iscc = firstExisting([process.env.ISCC,
  ...[process.env['ProgramFiles(x86)'], process.env.ProgramFiles, process.env.LOCALAPPDATA && path.join(process.env.LOCALAPPDATA, 'Programs')]
    .flatMap(folder => versionsIn(folder, 'Inno Setup ')).map(folder => path.join(folder, 'ISCC.exe'))], 'iscc');

const args = ['/Qp', `/DAppVersion=${version}`, `/DAppDir=${appDir}`, `/O${outDir}`];
if (process.env.SIGN_RELEASE === 'true') {
  const certificate = process.env.WINDOWS_CERTIFICATE_FILE;
  if (!certificate) throw new Error('WINDOWS_CERTIFICATE_FILE is required for a signed release');
  const kits = path.join(process.env['ProgramFiles(x86)'] ?? 'C:\\Program Files (x86)', 'Windows Kits', '10', 'bin');
  const signtool = firstExisting([process.env.SIGNTOOL,
    ...versionsIn(kits, '10.').map(sdk => path.join(sdk, 'x64', 'signtool.exe'))], 'signtool.exe');
  // Inno Setup expands $q to a quote and $f to the quoted file name; a literal $ is $$.
  const quote = value => '$q' + value.split('$').join('$$') + '$q';
  const password = process.env.WINDOWS_CERTIFICATE_PASSWORD ? ` /p ${quote(process.env.WINDOWS_CERTIFICATE_PASSWORD)}` : '';
  args.push('/DSign', `/Ssigntool=${quote(signtool)} sign /fd sha256 /tr http://timestamp.digicert.com /td sha256 /f ${quote(certificate)}${password} $f`);
}
args.push(path.join(root, 'scripts', 'windows-installer.iss'));

fs.rmSync(outDir, {recursive: true, force: true});
const result = spawnSync(iscc, args, {stdio: 'inherit'});
if (result.error) throw new Error(`Could not run Inno Setup (${iscc}): ${result.error.message}. Install Inno Setup 6 or set ISCC.`);
if (result.status !== 0) process.exit(result.status ?? 1);
console.log('Installer:', path.join(outDir, `${productName}-${version}-win-x64-setup.exe`));
