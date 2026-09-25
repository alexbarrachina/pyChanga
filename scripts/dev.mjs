import { createServer } from 'vite';
import { spawn } from 'node:child_process';
import electron from 'electron';
import { buildMain } from './build.mjs';

await buildMain();
const server = await createServer({root: 'editor', server: {host: '127.0.0.1', port: 5173, strictPort: true}});
await server.listen();
console.log('pyChangaIDE editor: http://127.0.0.1:5173');
const env = {...process.env, PYCHANGA_RENDERER_URL: 'http://127.0.0.1:5173'};
delete env.ELECTRON_RUN_AS_NODE;
const child = spawn(electron, ['.'], {env, stdio: 'inherit'});
let closing = false;
async function close() { if (closing) return; closing = true; child.kill(); await server.close(); }
child.on('exit', async () => { await close(); process.exit(); });
process.on('SIGINT', close);
process.on('SIGTERM', close);
