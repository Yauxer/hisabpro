// Parse et compile les fichiers réels avec les outils déjà utilisés par Vite.
const fs = require('node:fs')
const parser = require('@babel/parser')
const esbuild = require('esbuild')
for (const filename of process.argv.slice(2)) {
  const source = fs.readFileSync(filename, 'utf8')
  parser.parse(source, { sourceType: 'module', plugins: ['jsx'] })
  esbuild.transformSync(source, { loader: filename.endsWith('.jsx') ? 'jsx' : 'js', format: 'esm' })
}
console.log('OK analyse et compilation JSX')
