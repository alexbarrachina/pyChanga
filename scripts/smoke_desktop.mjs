import { _electron as electron, expect } from '@playwright/test';
import fs from 'node:fs/promises';
import path from 'node:path';

const appArgument = process.argv.indexOf('--app');
const packaged = appArgument >= 0 ? process.argv[appArgument + 1] : process.env.PYCHANGA_TEST_APP;
const profile = path.resolve('test-results', 'smoke-profile-' + Date.now());
await fs.mkdir(profile, {recursive:true});
const env = {...process.env, PYCHANGA_TEST_USER_DATA:profile,
  PYCHANGA_SILENT: process.argv.includes('--audio') || process.env.PYCHANGA_TEST_AUDIO === '1' ? '0' : '1'};
delete env.ELECTRON_RUN_AS_NODE;
// The packaged test deliberately cannot discover a system Python or FluidSynth.
if (packaged) {
  env.PATH = process.platform === 'win32' ? `${process.env.SystemRoot}\\System32` : '/usr/bin:/bin';
  delete env.PYTHONPATH; delete env.PYCHANGA_PYTHON; delete env.PYCHANGA_NATIVE_DIR; delete env.PYCHANGA_FLUIDSYNTH;
}
const launchOptions = {args: packaged ? [] : [path.resolve('.')], ...(packaged ? {executablePath: packaged} : {}), env};
let application = await electron.launch(launchOptions);
const errors = [];
let page;
try {
  page = await application.firstWindow();
  page.on('pageerror', error => errors.push(error.message));
  await expect(page.locator('#connection-label')).toHaveText(env.PYCHANGA_SILENT === '1' ? 'Silent test mode' : 'Audio ready', {timeout: 20000});
  await expect(page).toHaveTitle('pyChangaIDE');
  await expect(page.locator('.brand strong')).toHaveText('pyChangaIDE');
  await expect(page.locator('#bpm')).toHaveValue('60');
  expect((await page.evaluate(() => window.pyChanga.command({type:'status'}))).bpm).toBe(60);
  await expect(page.locator('.part')).toHaveCount(3);
  await page.getByTitle('Run melody', {exact:true}).click();
  await expect(page.locator('.part.playing')).toHaveCount(1, {timeout: 10000});
  await page.getByTitle('Run bass', {exact:true}).click();
  await expect(page.locator('.part.playing')).toHaveCount(2, {timeout: 10000});
  const before = await page.evaluate(() => window.pyChanga.command({type:'status'}));
  await page.getByTitle('Run melody', {exact:true}).click();
  await expect.poll(async () => {
    const state = await page.evaluate(() => window.pyChanga.command({type:'status'}));
    return state.parts.find(p=>p.name==='melody').revision;
  }).not.toBe(before.parts.find(p=>p.name==='melody').revision);
  const after = await page.evaluate(() => window.pyChanga.command({type:'status'}));
  expect(after.parts.find(p=>p.name==='bass').revision).toBe(before.parts.find(p=>p.name==='bass').revision);
  await page.locator('#bpm').fill('96');
  await page.locator('#bpm').press('Enter');
  await page.locator('#run').focus();
  await expect.poll(async () => (await page.evaluate(() => window.pyChanga.command({type:'status'}))).bpm).toBe(96);
  await page.getByTitle('Run rhythm', {exact:true}).click();
  await expect(page.locator('.part.playing')).toHaveCount(3, {timeout:10000});
  await fs.mkdir('test-results', {recursive:true});
  await page.screenshot({path: `test-results/${packaged ? 'packaged' : 'desktop'}.png`});
  await page.getByRole('button', {name:'Stop bass',exact:true}).click();
  await expect(page.locator('.part.playing')).toHaveCount(2);
  await page.locator('#stop-all').click();
  await expect(page.locator('.part.playing')).toHaveCount(0);

  // Ordinary editor keyboard input, including a Unicode filename and line errors.
  await page.locator('#new').click();
  await page.locator('.monaco-editor').click({position:{x:170,y:60}});
  await page.keyboard.press(process.platform==='darwin'?'Meta+A':'Control+A');
  await page.evaluate(source => {
    const data = new DataTransfer(); data.setData('text/plain',source);
    document.querySelector('.monaco-editor textarea').dispatchEvent(new ClipboardEvent('paste',{clipboardData:data,bubbles:true,cancelable:true}));
  }, '# %% setup\nfrom pyChanga import *\n\n# %% pulse\nwhile True:\n    piano(60, 0.3, 0.25)\n\n# %% busy\nwhile True:\n    pass\n');
  await expect(page.getByTitle('Run pulse',{exact:true})).toBeVisible();
  await page.getByTitle('Run pulse',{exact:true}).click();
  await page.getByTitle('Run busy',{exact:true}).click();
  await expect(page.locator('.part.playing')).toHaveCount(2,{timeout:10000});
  const stopStart=Date.now();
  await page.getByRole('button',{name:'Stop busy',exact:true}).click();
  await expect(page.locator('.part.playing')).toHaveCount(1);
  console.log('Busy-loop stop UI round trip:',Date.now()-stopStart,'ms');
  await page.locator('#stop-all').click();
  const file=path.resolve('test-results','música with spaces.py');
  const saved=await page.evaluate(async filename=>window.pyChanga.save(filename,'from pyChanga import *\npiano(60, .5, .25)\n'),file);
  expect(await fs.readFile(saved,'utf8')).toContain('piano(60');
  const result=await page.evaluate(()=>window.pyChanga.command({type:'run',documentId:'errors',filename:'música with spaces.py',source:'from pyChanga import *\nraise ValueError("test error")\n',quantization:'immediate'}));
  expect(result.error).toBeUndefined();
  await expect(page.locator('#output')).toContainText('test error');
  await page.locator('#restart').click();
  await expect(page.locator('#connection-label')).toHaveText(env.PYCHANGA_SILENT === '1' ? 'Silent test mode' : 'Audio ready',{timeout:20000});
  await expect(page.locator('#bpm')).toHaveValue('60');

  // Exercise the real file-open handler; only the native picker is substituted.
  const folder = path.resolve('test-results', 'composicions amb espais i música');
  await fs.mkdir(folder, {recursive:true});
  const composition = path.join(folder, 'melodia.py');
  await fs.writeFile(composition, 'from pyChanga import *\npiano(60, .5, 1)\n');
  await application.evaluate(({dialog}, filename) => {
    dialog.showOpenDialog = async (_window, options) => {
      globalThis.lastDialogPath = options.defaultPath;
      return {canceled:false, filePaths:[filename]};
    };
  }, composition);
  await page.locator('#open').click();
  await expect(page.locator('#tabs')).toContainText('melodia.py');
  expect(JSON.parse(await fs.readFile(path.join(profile, 'preferences.json'), 'utf8')).lastOpenedFolder).toBe(folder);
  await application.evaluate(({dialog}) => {
    dialog.showOpenDialog = async (_window, options) => {
      globalThis.lastDialogPath = options.defaultPath;
      return {canceled:true, filePaths:[]};
    };
  });
  await page.evaluate(() => window.pyChanga.open());
  expect(await application.evaluate(() => globalThis.lastDialogPath)).toBe(folder);

  // A new desktop process must recover the same folder from preferences.
  await application.evaluate(({ipcMain}) => ipcMain.emit('file:dirty', {}, false));
  await application.close();
  application = await electron.launch(launchOptions);
  page = await application.firstWindow();
  page.on('pageerror', error => errors.push(error.message));
  await expect(page.locator('#connection-label')).toHaveText(env.PYCHANGA_SILENT === '1' ? 'Silent test mode' : 'Audio ready', {timeout:20000});
  await application.evaluate(({dialog}) => {
    dialog.showOpenDialog = async (_window, options) => {
      globalThis.lastDialogPath = options.defaultPath;
      return {canceled:true, filePaths:[]};
    };
  });
  await page.evaluate(() => window.pyChanga.open());
  expect(await application.evaluate(() => globalThis.lastDialogPath)).toBe(folder);
  await fs.rename(folder, folder + '-moved-' + Date.now());
  await page.evaluate(() => window.pyChanga.open());
  expect(await application.evaluate(() => globalThis.lastDialogPath)).toBe(await application.evaluate(({app}) => app.getPath('documents')));
  console.log('Open folder persisted across restart; unavailable-folder fallback passed');
  expect(errors).toEqual([]);
  console.log(packaged?'Packaged desktop smoke test passed':'Desktop smoke test passed');
} catch (error) {
  if (page) {
    await fs.mkdir('test-results', {recursive:true});
    await page.screenshot({path:'test-results/desktop-failure.png'}).catch(()=>{});
    console.error('Visible editor:', await page.locator('.view-lines').innerText().catch(()=>''));
    console.error('Parts:', await page.locator('#parts').innerText().catch(()=>''));
    console.error('Output:', await page.locator('#output').innerText().catch(()=>''));
    console.error('Page errors:',errors);
  }
  throw error;
} finally {
  // Test edits are disposable; do not leave a native confirmation dialog open.
  await application.evaluate(({ipcMain})=>ipcMain.emit('file:dirty',{},false)).catch(()=>{});
  await application.close();
}
