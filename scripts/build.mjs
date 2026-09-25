import { build } from 'esbuild';
import { build as viteBuild } from 'vite';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export async function buildMain() {
  await build({entryPoints: ['desktop/main.ts', 'desktop/preload.ts'], outdir: 'dist', bundle: true,
    platform: 'node', format: 'cjs', outExtension: {'.js': '.cjs'}, external: ['electron'], sourcemap: true});
}
if (path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  await buildMain();
  await viteBuild({root: 'editor', base: './', build: {outDir: path.resolve('dist/renderer'), emptyOutDir: true}});
}
