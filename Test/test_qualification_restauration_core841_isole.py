"""Restauration native réellement rejouée, candidate produit conservée, aucune base utilisateur."""
from pathlib import Path
import hashlib,json
from test_restauration_tp761_isole import test_761_restaurer_cm_qualifiee_et_tous_complements as restaurer_source
R=Path(__file__).resolve().parents[1]

def empreintes841():
 chemins=[]
 for dossier in ['src','hisabpro-backend','public']:
  for p in (R/dossier).rglob('*'):
   if p.is_file() and not any(s in p.parts for s in ['.venv','venv','__pycache__','uploads','.pytest_cache','node_modules']) and p.suffix in {'.py','.sql','.jsx','.js','.css','.json','.svg','.png','.jpg','.woff','.woff2'}:chemins.append(p)
 for nom in ['package.json','package-lock.json','vite.config.js','index.html']:
  p=R/nom
  if p.is_file():chemins.append(p)
 return {p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(chemins)}

def test_841_restauration_froide_et_candidat_inchange(monkeypatch,tmp_path):
 avant=empreintes841();p=R/'.codex-tests/restauration761_preuve.json';ancien=p.read_bytes() if p.exists() else None;preuve={'erreur':None}
 try:
  restaurer_source(monkeypatch,tmp_path);d=json.loads(p.read_text(encoding='utf8'));assert d['erreur'] is None and d['tables']==83 and d['source_preservee'] and d['cibles_supprimees'] and d['schema_donnees_acl_sequences_identiques'];assert d['fec2025_octets_identiques'] and d['pieces_octets_traces_dossier_manifestes_logos_identiques'];assert empreintes841()==avant
  preuve.update(d,candidat_produit_conserve=True,nb_sources_produit=len(avant),nb_fichiers_restaures=len(d['fichiers']),perimetre='Banc104 sur PostgreSQL natif éphémère nonce ; restauration réelle pg_dump/pg_restore, données fictives. Pas restauration du PostgreSQL utilisateur. Pas qualification individuelle automatique des fiches EXP du cahier.')
  (R/'.codex-tests/candidat841_sha256.json').write_text(json.dumps(avant,ensure_ascii=False,indent=2),encoding='utf8')
 except BaseException as exc:preuve['erreur']=repr(exc);raise
 finally:
  (R/'.codex-tests/restauration841_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
  if ancien is not None:p.write_bytes(ancien)
  elif p.exists():p.unlink()
