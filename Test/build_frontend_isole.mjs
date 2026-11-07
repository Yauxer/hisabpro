// Build de recette sans charger le .env du projet ni démarrer de serveur.
import { mkdtemp, mkdir, writeFile, readdir, readFile } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import { createHash } from 'node:crypto'
import { build } from 'vite'

const root = fileURLToPath(new URL('../', import.meta.url))
const espace = path.join(root, '.codex-tests')
await mkdir(espace, { recursive: true })
const travail = await mkdtemp(path.join(espace, 'build-frontend-'))
const envDir = path.join(travail, 'env-vide')
const outDir = path.join(travail, 'dist')
await mkdir(envDir)
const debut = Date.now()
await build({ root, envDir,
  define: { 'import.meta.env.VITE_API_URL': JSON.stringify('http://127.0.0.1:1') },
  build: { outDir, emptyOutDir: false },
})
const fichiers = {}
async function inventorier(dir) {
  for (const entree of await readdir(dir, { withFileTypes: true })) {
    const p = path.join(dir, entree.name)
    if (entree.isDirectory()) await inventorier(p)
    else fichiers[path.relative(outDir, p).split(path.sep).join('/')] =
      createHash('sha256').update(await readFile(p)).digest('hex')
  }
}
await inventorier(outDir)
const preuve = { commande: 'node Test/build_frontend_isole.mjs', environnement_vide: true,
  api_inerte: 'http://127.0.0.1:1', code_sortie: 0, secondes: (Date.now() - debut) / 1000,
  sortie: path.relative(root, outDir), fichiers }
await writeFile(path.join(espace, 'build_frontend_preuve.json'), JSON.stringify(preuve, null, 2))
console.log('Build isolé terminé ; preuve dans .codex-tests/build_frontend_preuve.json')
