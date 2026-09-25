// The browser editor's host contract. Electron implements it in desktop/preload.ts.
// Keep this file free of Electron/Node imports so other hosts can use the editor.
export interface Selection { startLine: number; startColumn: number; endLine: number; endColumn: number }
export interface MusicError { message: string; filename?: string; line?: number; column?: number; traceback?: string }
export interface MusicPart {
  id: string; name: string; origin: 'section' | 'function'; documentId: string; filename: string; line: number;
  state: 'preparing' | 'playing' | 'finished' | 'stopped' | 'error';
  revision: string | null; pending: {revision: string; beat: number | null} | null; error: MusicError | null;
}
export interface Section { name: string; line: number; markerLine: number; endLine: number; kind?: 'part' | 'all' }
export interface EngineEvent {
  type: string; version: number; requestId?: string; message?: string; audio?: string;
  partId?: string; revision?: string; documentId?: string; filename?: string;
  line?: number; column?: number; traceback?: string; text?: string; stream?: string;
  parts?: MusicPart[]; beat?: number; bpm?: number;
  pendingTempo?: {bpm: number; beat: number} | null;
}
export interface MusicBridge {
  command: (command: Record<string, unknown>) => Promise<Record<string, any>>;
  onEvent: (handler: (event: EngineEvent) => void) => () => void;
  connect: () => Promise<EngineEvent | null>;
  restart: () => Promise<void>;
  open: () => Promise<{path: string; source: string} | null>;
  save: (path: string | null, source: string) => Promise<string | null>;
  examples: () => Promise<{name: string; source: string}[]>;
  confirmDiscard: (name: string) => Promise<boolean>;
  setDirty: (dirty: boolean) => void;
}
declare global { interface Window { pyChanga: MusicBridge } }
