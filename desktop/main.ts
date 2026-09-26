import { app, BrowserWindow, dialog, ipcMain, Menu } from 'electron';
import { spawn, type ChildProcessWithoutNullStreams } from 'node:child_process';
import { randomUUID } from 'node:crypto';
import { mkdir, readFile, readdir, stat, writeFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import path from 'node:path';
import type { EngineEvent } from '../editor/bridge';

let window: BrowserWindow | null = null;
let service: ChildProcessWithoutNullStreams | null = null;
let latest: EngineEvent | null = null;
let quitting = false;
let dirty = false;
const requests = new Map<string, {resolve: (value: any) => void; reject: (error: Error) => void; timer: NodeJS.Timeout}>();
const root = path.resolve(__dirname, '..');
app.setName('pyChangaIDE');
if (process.env.PYCHANGA_TEST_USER_DATA) app.setPath('userData', process.env.PYCHANGA_TEST_USER_DATA);
const preferencesFile = path.join(app.getPath('userData'), 'preferences.json');
let lastOpenedFolder: string | undefined;
const send = (event: EngineEvent) => { if (window && !window.isDestroyed()) window.webContents.send('music:event', event); };

async function openDirectory(): Promise<string> {
  if (lastOpenedFolder) {
    try { if ((await stat(lastOpenedFolder)).isDirectory()) return lastOpenedFolder; } catch { /* Folder moved or disconnected. */ }
  }
  return app.getPath('documents');
}

function startService() {
  const runtime = app.isPackaged ? path.join(process.resourcesPath, 'runtime')
    : path.join(root, 'runtime', `${process.platform}-${process.arch}`, 'runtime');
  const runtimePython = path.join(runtime, 'python', process.platform === 'win32' ? 'python.exe' : 'bin/python3');
  const useRuntime = app.isPackaged || (!process.env.PYCHANGA_PYTHON && existsSync(runtimePython));
  const python = useRuntime ? runtimePython : process.env.PYCHANGA_PYTHON || (process.platform === 'win32' ? 'python' : 'python3');
  const pythonPath = app.isPackaged ? path.join(runtime, 'packages')
    : [path.join(root, 'pyChanga_package'), ...(useRuntime ? [path.join(runtime, 'packages')] : []), process.env.PYTHONPATH]
      .filter(Boolean).join(path.delimiter);
  const env = {...process.env, PYTHONPATH: pythonPath, PYTHONUNBUFFERED: '1', PYTHONIOENCODING: 'utf-8',
    ...(useRuntime ? {PYCHANGA_NATIVE_DIR: app.isPackaged ? path.join(runtime, 'native')
      : process.env.PYCHANGA_NATIVE_DIR || path.join(runtime, 'native')} : {})};
  const child = spawn(python, ['-m', 'pyChanga', '--service', ...(process.env.PYCHANGA_SILENT === '1' ? ['--silent'] : [])],
    {cwd: app.isPackaged ? app.getPath('userData') : root, env, windowsHide: true, stdio: ['pipe', 'pipe', 'pipe']});
  service = child;
  latest = null;
  let buffer = '', diagnostic = '';
  child.stdout.setEncoding('utf8');
  child.stdout.on('data', (chunk: string) => {
    buffer += chunk;
    if (buffer.length > 4_000_000) { child.kill(); return; }
    let newline: number;
    while ((newline = buffer.indexOf('\n')) >= 0) {
      const line = buffer.slice(0, newline); buffer = buffer.slice(newline + 1);
      try {
        const event = JSON.parse(line);
        if (event.type === 'response') {
          const pending = requests.get(event.requestId);
          if (pending) {
            clearTimeout(pending.timer); requests.delete(event.requestId);
            if (event.ok) pending.resolve(event.result);
            else pending.resolve({error: event.error});
          }
        } else {
          if (event.type === 'ready' || event.type === 'fatal') latest = event;
          send(event);
        }
      } catch { diagnostic = `Unexpected playback response: ${line.slice(0, 300)}`; }
    }
  });
  child.stderr.setEncoding('utf8');
  child.stderr.on('data', (text: string) => { diagnostic = (diagnostic + text).slice(-4000); });
  child.stdin.on('error', () => {});
  const failed = (message: string) => {
    if (service !== child) return;
    service = null;
    for (const pending of requests.values()) { clearTimeout(pending.timer); pending.reject(new Error(message)); }
    requests.clear();
    if (!quitting) {
      latest = {version: 1, type: 'fatal', message}; send(latest);
    }
  };
  child.on('error', error => failed(`Could not start Python: ${error.message}`));
  child.on('exit', code => failed(latest?.type === 'fatal' ? latest.message! : `Playback stopped (${code ?? 'signal'}). ${diagnostic}`));
}

async function stopService() {
  const child = service;
  if (!child) return;
  service = null;
  for (const pending of requests.values()) { clearTimeout(pending.timer); pending.reject(new Error('Playback restarted')); }
  requests.clear();
  await new Promise<void>(resolve => {
    const timer = setTimeout(() => { child.kill(); resolve(); }, 2000);
    child.once('exit', () => { clearTimeout(timer); resolve(); });
    child.stdin.end(JSON.stringify({version: 1, type: 'shutdown'}) + '\n');
  });
}

function command(value: Record<string, unknown>): Promise<any> {
  if (!service || latest?.type !== 'ready') return Promise.reject(new Error('Playback is not ready. Use Restart audio.'));
  if (!['run', 'stop', 'stop_all', 'tempo', 'parse', 'status', 'launch_mode'].includes(String(value.type))) return Promise.reject(new Error('Unsupported command'));
  const requestId = randomUUID();
  const line = JSON.stringify({...value, version: 1, requestId}) + '\n';
  if (line.length > 2_000_000) return Promise.reject(new Error('The document is too large'));
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => { requests.delete(requestId); reject(new Error('Playback did not respond')); }, 15000);
    requests.set(requestId, {resolve, reject, timer});
    service!.stdin.write(line);
  });
}

app.whenReady().then(async () => {
  try {
    const preferences = JSON.parse(await readFile(preferencesFile, 'utf8'));
    if (typeof preferences.lastOpenedFolder === 'string' && path.isAbsolute(preferences.lastOpenedFolder)) {
      lastOpenedFolder = preferences.lastOpenedFolder;
    }
  } catch { /* First launch, or unreadable preferences: use Documents. */ }
  Menu.setApplicationMenu(Menu.buildFromTemplate([
    ...(process.platform === 'darwin' ? [{role: 'appMenu' as const}] : []),
    {role: 'editMenu'}, {role: 'viewMenu'}, {role: 'windowMenu'},
  ]));
  ipcMain.handle('music:command', (_event, value) => command(value));
  ipcMain.on('file:dirty', (_event, value) => { dirty = Boolean(value); });
  ipcMain.handle('music:connect', () => latest);
  ipcMain.handle('music:restart', async () => { await stopService(); startService(); });
  ipcMain.handle('file:open', async () => {
    const result = await dialog.showOpenDialog(window!, {defaultPath: await openDirectory(),
      filters: [{name: 'Python compositions', extensions: ['py']}], properties: ['openFile']});
    if (result.canceled || !result.filePaths[0]) return null;
    const filename = result.filePaths[0];
    const source = await readFile(filename, 'utf8');
    lastOpenedFolder = path.dirname(filename);
    try {
      await mkdir(app.getPath('userData'), {recursive: true});
      await writeFile(preferencesFile, JSON.stringify({lastOpenedFolder}, null, 2) + '\n', 'utf8');
    } catch (error) { console.warn('Could not remember the opened folder:', error); }
    return {path: filename, source};
  });
  ipcMain.handle('file:save', async (_event, filename: string | null, source: string) => {
    if (!filename) {
      const result = await dialog.showSaveDialog(window!, {defaultPath: 'composition.py', filters: [{name: 'Python composition', extensions: ['py']}]});
      if (result.canceled || !result.filePath) return null;
      filename = result.filePath;
    }
    await writeFile(filename, source, 'utf8');
    return filename;
  });
  ipcMain.handle('file:discard', async (_event, name: string) => {
    const result = await dialog.showMessageBox(window!, {type: 'question', message: `Discard unsaved changes to ${name}?`,
      buttons: ['Keep editing', 'Discard changes'], defaultId: 0, cancelId: 0});
    return result.response === 1;
  });
  ipcMain.handle('file:examples', async () => {
    const directory = app.isPackaged ? path.join(process.resourcesPath, 'examples') : path.join(root, 'examples');
    const names = (await readdir(directory)).filter(name => name.endsWith('.py')).sort();
    return Promise.all(names.map(async name => ({name, source: await readFile(path.join(directory, name), 'utf8')})));
  });
  window = new BrowserWindow({width: 1320, height: 900, minWidth: 880, minHeight: 600,
    title: 'pyChangaIDE', backgroundColor: '#151a1c',
    webPreferences: {preload: path.join(__dirname, 'preload.cjs'), contextIsolation: true, nodeIntegration: false, sandbox: true}});
  window.webContents.setWindowOpenHandler(() => ({action: 'deny'}));
  window.webContents.on('will-navigate', event => event.preventDefault());
  window.on('close', event => {
    if (!quitting && dirty) {
      const result = dialog.showMessageBoxSync(window!, {type: 'question', message: 'Close pyChangaIDE with unsaved changes?',
        detail: 'Playing parts will stop.', buttons: ['Keep editing', 'Close without saving'], defaultId: 0, cancelId: 0});
      if (result === 0) event.preventDefault();
      else dirty = false;
    }
  });
  if (process.env.PYCHANGA_RENDERER_URL) void window.loadURL(process.env.PYCHANGA_RENDERER_URL);
  else void window.loadFile(path.join(__dirname, 'renderer', 'index.html'));
  window.webContents.once('did-finish-load', startService);
});
app.on('window-all-closed', () => app.quit());
app.on('before-quit', event => {
  if (quitting) return;
  if (dirty && window && !window.isDestroyed()) {
    const result = dialog.showMessageBoxSync(window, {type: 'question', message: 'Quit with unsaved changes?',
      detail: 'Playing parts will stop.', buttons: ['Keep editing', 'Quit without saving'], defaultId: 0, cancelId: 0});
    if (result === 0) { event.preventDefault(); return; }
    dirty = false;
  }
  event.preventDefault(); quitting = true;
  void stopService().finally(() => app.quit());
});
