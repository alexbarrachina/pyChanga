import { contextBridge, ipcRenderer } from 'electron';
import type { EngineEvent, MusicBridge } from '../editor/bridge';

const api: MusicBridge = {
  command: command => ipcRenderer.invoke('music:command', command),
  onEvent: handler => {
    const listener = (_: unknown, event: EngineEvent) => handler(event);
    ipcRenderer.on('music:event', listener);
    return () => ipcRenderer.removeListener('music:event', listener);
  },
  connect: () => ipcRenderer.invoke('music:connect'),
  restart: () => ipcRenderer.invoke('music:restart'),
  open: () => ipcRenderer.invoke('file:open'),
  save: (path, source) => ipcRenderer.invoke('file:save', path, source),
  examples: () => ipcRenderer.invoke('file:examples'),
  confirmDiscard: name => ipcRenderer.invoke('file:discard', name),
  setDirty: dirty => ipcRenderer.send('file:dirty', dirty),
};
contextBridge.exposeInMainWorld('pyChanga', api);
