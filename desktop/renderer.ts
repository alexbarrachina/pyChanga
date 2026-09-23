import * as monaco from 'monaco-editor/esm/vs/editor/editor.api';
import 'monaco-editor/esm/vs/basic-languages/python/python.contribution';
import EditorWorker from 'monaco-editor/esm/vs/editor/editor.worker?worker';
import type { EngineEvent, MusicPart, Section } from './types';
import './style.css';

(self as any).MonacoEnvironment = {getWorker: () => new EditorWorker()};
const $ = <T extends HTMLElement = HTMLElement>(id: string) => document.getElementById(id) as T;
const mac = navigator.platform.toUpperCase().includes('MAC');
const modifier = mac ? '⌘' : 'Ctrl';
$('run-key').textContent = `${modifier} ↵`;
for (const [name, key] of [['run', 'Enter'], ['stop', '.'], ['save', 'S']]) document.querySelector(`.shortcut-${name}`)!.textContent = `${modifier} ${key}`;

monaco.editor.defineTheme('pyChanga', {
  base: 'vs-dark', inherit: true,
  rules: [
    {token: 'comment', foreground: '718F80', fontStyle: 'italic'},
    {token: 'keyword', foreground: 'DAC398'}, {token: 'number', foreground: 'D7B997'},
    {token: 'string', foreground: 'A9CBAA'}, {token: 'identifier', foreground: 'D6E3DE'},
    {token: 'delimiter', foreground: '8EA69C'},
  ],
  colors: {'editor.background': '#151A1C', 'editor.foreground': '#D9E4DF', 'editorLineNumber.foreground': '#506460',
    'editorLineNumber.activeForeground': '#A2BEAD', 'editor.selectionBackground': '#35594877', 'editor.lineHighlightBackground': '#20292B77',
    'editorCursor.foreground': '#B8EDCC', 'editorIndentGuide.background1': '#293A34', 'editorIndentGuide.activeBackground1': '#486A59',
    'editorGutter.background': '#151A1C', 'editorWidget.background': '#242F29', 'editorWidget.border': '#415A4B',
    'editorSuggestWidget.background': '#202C25', 'editorSuggestWidget.border': '#415A4B', 'editorSuggestWidget.selectedBackground': '#364D3F',
    'scrollbarSlider.background': '#759A8224', 'scrollbarSlider.hoverBackground': '#759A8244'},
});

const editor = monaco.editor.create($('editor'), {language: 'python', theme: 'pyChanga', automaticLayout: true,
  fontFamily: '"SFMono-Regular", Consolas, "Liberation Mono", monospace', fontSize: 14, lineHeight: 25,
  minimap: {enabled: false}, padding: {top: 10, bottom: 24}, scrollBeyondLastLine: false,
  renderLineHighlight: 'line', lineNumbersMinChars: 3, glyphMargin: true, folding: true,
  tabSize: 4, insertSpaces: true, wordWrap: 'off', bracketPairColorization: {enabled: false},
  overviewRulerLanes: 0, hideCursorInOverviewRuler: true, smoothScrolling: true,
  quickSuggestions: {other: true, comments: false, strings: false}, fixedOverflowWidgets: true});

const instruments = ['piano','clarinet','oboe','violin','cbass','drums','viola','sax','bass','organ','marimba','bassoon','choir','cello','synth','vibra','guitar'];
const functions = [...instruments.map(name => ({name, signature: '(note, vol, dur, block=True)',
  insert: `${name}(\${1:60}, \${2:0.7}, \${3:0.5})`, description: 'Play a MIDI pitch or list of pitches. Volume: 0–1. Duration: beats. block=False overlaps notes.'})),
  {name:'wait',signature:'(beats)',insert:'wait(${1:1})',description:'Rest for beats. Other musical parts keep playing.'},
  {name:'tempo',signature:'(bpm)',insert:'tempo(${1:60})',description:'Change the shared tempo on the next available beat (20–400 BPM; starts at 60).'},
  {name:'drumSeq',signature:'(seq, dur=0.25)',insert:'drumSeq("${1:k-h-s-h-}", ${2:0.25})',description:'k: kick, s: snare, h: hi-hat, c: cymbal, t: tom, -: rest.'},
  ...['major_scale','natural_minor_scale','pentatonic_scale','pentatonic_minor_scale'].map(name => ({name,signature:'(root)',insert:`${name}(\${1:60})`,description:'An octave-extending scale. Access degrees with scale[0] or a finite slice such as scale[:8].'}))];
monaco.languages.registerCompletionItemProvider('python', {provideCompletionItems(model, position) {
  const word = model.getWordUntilPosition(position);
  const range = {startLineNumber: position.lineNumber, endLineNumber: position.lineNumber, startColumn: word.startColumn, endColumn: word.endColumn};
  return {suggestions: functions.map(f => ({label: f.name, kind: monaco.languages.CompletionItemKind.Function,
    detail: f.name + f.signature, documentation: f.description, insertText: f.insert,
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet, range}))};
}});
monaco.languages.registerHoverProvider('python', {provideHover(model, position) {
  const word = model.getWordAtPosition(position); const fn = functions.find(f => f.name === word?.word);
  return fn ? {contents: [{value: `\`\`\`python\n${fn.name}${fn.signature}\n\`\`\``}, {value: fn.description}]} : null;
}});

interface Composition {id: string; name: string; path: string | null; model: monaco.editor.ITextModel; saved: string;
  sections: Section[]; view: monaco.editor.ICodeEditorViewState | null; disposable: monaco.IDisposable}
const documents = new Map<string, Composition>();
let active: Composition;
let ready = false, parts: MusicPart[] = [], outputCount = 0, parseTimer: ReturnType<typeof setTimeout>;
let partsSignature = '', decorations: string[] = [];

function banner(message = '') { $('banner').textContent = message; $('banner').hidden = !message; }
function log(text: string, kind = 'info', source?: {documentId?: string; line?: number; name?: string}) {
  if (!$('output').querySelector('.output-line')) $('output').replaceChildren();
  const entry = document.createElement('div'); entry.className = `output-line ${kind}`;
  if (source) {
    const link = document.createElement('span'); link.className = 'output-source';
    link.textContent = `[${source.name || 'part'}${source.line ? ':' + source.line : ''}]`;
    link.onclick = () => { const doc = documents.get(source.documentId || ''); if (doc) { activate(doc); editor.setPosition({lineNumber: source.line || 1, column: 1}); editor.revealLineInCenter(source.line || 1); editor.focus(); } };
    entry.append(link);
  }
  entry.append(document.createTextNode(text)); $('output').append(entry);
  while ($('output').children.length > 500) $('output').firstElementChild!.remove();
  $('output-count').textContent = String(++outputCount); $('output').scrollTop = $('output').scrollHeight;
}
async function command(value: Record<string, unknown>) {
  if (!window.pyChanga) throw new Error('Open this editor through the pyChangaIDE desktop app.');
  const result = await window.pyChanga.command(value);
  if (result.error) {
    const error = result.error;
    log(error.message, 'error', {documentId: active.id, line: error.line, name: active.name});
    markError(active, error);
    throw new Error(error.message);
  }
  return result;
}
function markError(doc: Composition, error: {message: string; line?: number; column?: number}) {
  const line = Math.max(1, Math.min(error.line || 1, doc.model.getLineCount()));
  monaco.editor.setModelMarkers(doc.model, 'pyChanga', [{severity: monaco.MarkerSeverity.Error, message: error.message,
    startLineNumber: line, endLineNumber: line, startColumn: error.column || 1, endColumn: doc.model.getLineMaxColumn(line)}]);
}
function renderTabs() {
  $('tabs').replaceChildren();
  for (const doc of documents.values()) {
    const button = document.createElement('button'); button.className = 'tab' + (doc === active ? ' active' : '');
    button.setAttribute('role', 'tab'); button.setAttribute('aria-selected', String(doc === active));
    const icon = document.createElement('span'); icon.className = 'python-icon'; icon.textContent = 'PY';
    const label = document.createElement('span'); label.textContent = doc.name + (doc.model.getValue() !== doc.saved ? ' •' : '');
    const close = document.createElement('span'); close.className = 'tab-close'; close.textContent = '×'; close.title = `Close ${doc.name}`;
    close.onclick = event => { event.stopPropagation(); void closeDocument(doc); };
    button.append(icon, label, close); button.onclick = () => activate(doc); $('tabs').append(button);
  }
  $('file-status').textContent = active.path || `${active.name} · unsaved composition`;
  window.pyChanga?.setDirty([...documents.values()].some(d => d.model.getValue() !== d.saved));
}
function createDocument(name: string, source: string, filename: string | null = null, saved = false) {
  const id = crypto.randomUUID();
  const model = monaco.editor.createModel(source, 'python', monaco.Uri.parse(`inmemory://pyChanga/${id}/${name}`));
  const doc: Composition = {id, name, path: filename, model, saved: saved ? source : '', sections: [], view: null,
    disposable: model.onDidChangeContent(() => { monaco.editor.setModelMarkers(model, 'pyChanga', []); renderTabs(); scheduleParse(); })};
  documents.set(id, doc); activate(doc); return doc;
}
function activate(doc: Composition) {
  if (active) active.view = editor.saveViewState();
  active = doc; editor.setModel(doc.model); if (doc.view) editor.restoreViewState(doc.view);
  partsSignature = ''; renderTabs(); renderParts(); scheduleParse(); editor.focus();
}
async function closeDocument(doc: Composition) {
  if (doc.model.getValue() !== doc.saved && !await window.pyChanga.confirmDiscard(doc.name)) return;
  for (const part of parts.filter(p => p.documentId === doc.id && (p.revision || p.pending))) await command({type:'stop',partId:part.id});
  documents.delete(doc.id); doc.disposable.dispose();
  if (doc === active) {
    const next = documents.values().next().value;
    if (next) activate(next); else createDocument('untitled.py', '# %% setup\nfrom pyChanga import *\n\n# %% melody\npiano(60, 0.7, 1)\n');
  }
  doc.model.dispose(); renderTabs();
}
function scheduleParse() {
  clearTimeout(parseTimer);
  if (!ready || !active) return;
  const doc = active, version = doc.model.getVersionId();
  parseTimer = setTimeout(async () => {
    try {
      const result = await window.pyChanga.command({type:'parse',source:doc.model.getValue()});
      if (doc.model.isDisposed() || doc.model.getVersionId() !== version) return;
      if (!result.error) { doc.sections = result.parts; if (active === doc) { partsSignature = ''; renderParts(); } }
    } catch { /* The connection banner explains service failures. */ }
  }, 200);
}
async function run(name?: string) {
  if (!ready) return;
  try {
    banner(); monaco.editor.setModelMarkers(active.model, 'pyChanga', []);
    const selection = editor.getSelection()!;
    await command({type:'run', documentId:active.id, filename:active.path || active.name, source:active.model.getValue(),
      quantization:$<HTMLSelectElement>('quantization').value, ...(name ? {name} : {selection: {
        startLine:selection.startLineNumber, startColumn:selection.startColumn,
        endLine:selection.endLineNumber, endColumn:selection.endColumn}})});
  } catch (error) { banner((error as Error).message); }
}
async function stopAll() { try { await command({type:'stop_all'}); } catch (error) { banner((error as Error).message); } }
function renderParts() {
  if (!active) return;
  const docParts = parts.filter(p => p.documentId === active.id);
  const signature = JSON.stringify([active.id, active.sections, docParts, ready]);
  $('playing-count').textContent = `${parts.filter(p => p.revision).length} PLAYING`;
  if (signature === partsSignature) return;
  partsSignature = signature; $('parts').replaceChildren();
  const sections = [...active.sections];
  for (const p of docParts) if (!sections.some(s => s.name === p.name) && (p.revision || p.pending)) sections.push({name:p.name,line:p.line,markerLine:p.line,endLine:p.line});
  if (!sections.length) { const empty = document.createElement('p'); empty.className='empty-parts'; empty.textContent = ready ? 'Add a named section to create your first musical part.' : 'Your parts will appear when the playback service is ready.'; $('parts').append(empty); }
  sections.forEach((section, index) => {
    const part = docParts.find(p => p.name === section.name);
    const playing = Boolean(part?.revision), pending = part?.pending;
    const card = document.createElement('div'); card.className = `part${playing ? ' playing' : ''}${pending ? ' pending' : ''}${part?.error ? ' error' : ''}`;
    const title = document.createElement('div'); title.className='part-title';
    const number = document.createElement('span'); number.className='part-number'; number.textContent=String(index+1).padStart(2,'0');
    const go = document.createElement('button'); go.textContent=section.name; go.title=`Go to ${section.name}`;
    go.onclick=()=>{editor.setPosition({lineNumber:section.line,column:1});editor.revealLineInCenter(section.line);editor.focus();};
    const light=document.createElement('span');light.className='part-light';title.append(number,go,light);
    const meta=document.createElement('div');meta.className='part-meta';
    const state=document.createElement('span');state.className='part-state';
    state.textContent=pending ? (pending.beat === null ? 'Preparing…' : `Queued · beat ${Math.floor(pending.beat)+1}`) : playing ? 'Playing' : part?.state === 'finished' ? 'Finished' : part?.state === 'error' ? 'Check output' : 'Ready to play';
    const controls=document.createElement('div');controls.className='part-buttons';
    const play=document.createElement('button');play.textContent=playing?'↻ Update':'▶ Run';play.title=`Run ${section.name}`;play.disabled=!ready;play.onclick=()=>void run(section.name);controls.append(play);
    if (playing || pending) {const stop=document.createElement('button');stop.className='part-stop';stop.textContent='■';stop.title=`Stop ${section.name}`;stop.setAttribute('aria-label',`Stop ${section.name}`);stop.onclick=()=>void command({type:'stop',partId:part!.id}).catch(e=>banner(e.message));controls.append(stop);}
    meta.append(state,controls);card.append(title,meta);$('parts').append(card);
  });
  decorations = editor.deltaDecorations(decorations, docParts.filter(p=>p.revision||p.pending).map(p=>({range:new monaco.Range(Math.min(p.line,active.model.getLineCount()),1,Math.min(p.line,active.model.getLineCount()),1),
    options:{isWholeLine:true,linesDecorationsClassName:p.pending?'music-pending-line':'music-playing-line'}})));
}
function onEvent(event: EngineEvent) {
  if (event.type==='ready') {
    ready=true;$('connection-dot').className='dot ready';$('connection-label').textContent=event.audio==='silent'?'Silent test mode':'Audio ready';
    $<HTMLButtonElement>('run').disabled=false;$<HTMLButtonElement>('stop-all').disabled=false;banner();scheduleParse();renderParts();
  } else if (event.type==='fatal') {
    ready=false;parts=[];$('connection-dot').className='dot error';$('connection-label').textContent='Audio unavailable';
    $<HTMLButtonElement>('run').disabled=true;$<HTMLButtonElement>('stop-all').disabled=true;banner(event.message);log(event.message||'Playback stopped','error');renderParts();
  } else if(event.type==='status') {
    parts=event.parts||[];
    const beat=event.beat||0;const whole=Math.floor(beat);
    $('beat-position').textContent=`${String(Math.floor(whole/4)+1).padStart(3,'0')}.${whole%4+1}`;
    document.querySelectorAll('.beat-lights i').forEach((el,index)=>el.classList.toggle('active',index===whole%4));
    if(document.activeElement!==$('bpm')) $<HTMLInputElement>('bpm').value=String(event.bpm);
    $('pending-tempo').textContent=event.pendingTempo?`${event.pendingTempo.bpm} BPM on beat ${Math.floor(event.pendingTempo.beat)+1}`:'';
    renderParts();
  } else if(event.type==='error'||event.type==='warning'||event.type==='output') {
    const part=parts.find(p=>p.id===event.partId);const doc=documents.get(event.documentId||part?.documentId||'');
    log(event.type==='output'?event.text||'':event.message||'',event.type==='output'?(event.stream==='stderr'?'error':'info'):event.type,
      {documentId:doc?.id,line:event.line,name:part?.name||'Python'});
    if(event.type==='error'&&doc) markError(doc,{message:event.message||'Python error',line:event.line,column:event.column});
  }
}
async function save() {try {const doc=active;const source=doc.model.getValue();const filename=await window.pyChanga.save(doc.path,source);if(filename){doc.path=filename;doc.name=filename.split(/[\\/]/).pop()!;doc.saved=source;renderTabs();}}catch(error){banner((error as Error).message);}}
async function open() {try {const result=await window.pyChanga.open();if(result){const existing=[...documents.values()].find(d=>d.path===result.path);if(existing)activate(existing);else createDocument(result.path.split(/[\\/]/).pop()!,result.source,result.path,true);}}catch(error){banner((error as Error).message);}}
$('run').onclick=()=>void run();$('stop-all').onclick=()=>void stopAll();$('save').onclick=()=>void save();$('open').onclick=()=>void open();
$('new').onclick=()=>createDocument('untitled.py','# %% setup\nfrom pyChanga import *\n\n# %% melody\npiano(60, 0.7, 1)\n');
$('restart').onclick=()=>{ready=false;parts=[];renderParts();$('connection-label').textContent='Restarting…';void window.pyChanga.restart().catch(e=>banner(e.message));};
$('clear-output').onclick=()=>{$('output').replaceChildren();outputCount=0;$('output-count').textContent='0';};
$('bpm').onchange=()=>void command({type:'tempo',bpm:Number($<HTMLInputElement>('bpm').value)}).catch(e=>banner(e.message));
$('help').onclick=()=>$<HTMLDialogElement>('help-dialog').showModal();$('close-help').onclick=()=>$<HTMLDialogElement>('help-dialog').close();
editor.addCommand(monaco.KeyMod.CtrlCmd|monaco.KeyCode.Enter,()=>void run());
editor.addCommand(monaco.KeyMod.CtrlCmd|monaco.KeyCode.Period,()=>void stopAll());
editor.addCommand(monaco.KeyMod.CtrlCmd|monaco.KeyCode.KeyS,()=>void save());
window.addEventListener('keydown',event=>{if((mac?event.metaKey:event.ctrlKey)&&event.key==='.' ){event.preventDefault();void stopAll();}});
editor.onDidChangeCursorPosition(event=>{const {lineNumber,column}=event.position;$('cursor-position').textContent=`Ln ${lineNumber}, Col ${column}`;const section=active?.sections.find(s=>s.markerLine<=lineNumber&&s.endLine>=lineNumber);$('section-label').textContent=section?`PART / ${section.name.toUpperCase()}`:'YOUR COMPOSITION';});

createDocument('first composition.py', '# %% setup\nfrom pyChanga import *\nfrom random import choice\n\nnotes = [60, 64, 67, 72]\n\n# %% melody\n# Run this part. Then change the notes and run it again.\nwhile True:\n    piano(choice(notes), 0.7, 0.5)\n\n# %% bass\n# Bring in a second voice on the same beat.\nwhile True:\n    bass(36, 0.6, 2)\n    bass(43, 0.6, 2)\n\n# %% rhythm\nwhile True:\n    drumSeq("k-h-s-h-", 0.25)\n', null, true);
if (window.pyChanga) {
  window.pyChanga.onEvent(onEvent);
  void window.pyChanga.connect().then(event=>{if(event)onEvent(event);});
  void window.pyChanga.examples().then(examples=>{
    for(const example of examples){const option=document.createElement('option');option.value=example.name;option.textContent=example.name.replace(/\.py$/,'').replace(/_/g,' ');$('examples').append(option);}
    $('examples').onchange=()=>{const select=$<HTMLSelectElement>('examples');const example=examples.find(e=>e.name===select.value);if(example)createDocument(example.name,example.source,null,true);select.value='';};
  }).catch(error=>log(error.message,'warning'));
} else {banner('This is a preview of the editor. Open pyChangaIDE to execute Python and hear your music.');$('connection-label').textContent='Editor preview';}
