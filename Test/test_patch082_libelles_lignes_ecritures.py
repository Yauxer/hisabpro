"""082 — saisie des écritures : libellé du compte prérempli, tiers préservés."""
from pathlib import Path
import json
import shutil
import subprocess
from jsx_syntax import assert_jsx

ROOT = Path(__file__).resolve().parents[1]
FORM = (ROOT / 'src/components/FormulaireEcriture.jsx').read_text(encoding='utf-8')
CSS = (ROOT / 'src/components/FormulaireEcriture.module.css').read_text(encoding='utf-8')
HELPER = ROOT / 'src/utils/libellesEcriture.js'


def _node(script):
    assert shutil.which('node'), 'Node est nécessaire au test fonctionnel du helper JS'
    result = subprocess.run(
        ['node', '--input-type=module', '-e', script], cwd=ROOT,
        capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout.strip())


def test_082_compte_selectionne_renseigne_libelle_y_compris_banque():
    result = _node('''
import { synchroniserLibelleCompte } from './src/utils/libellesEcriture.js';
const plan = new Map([['5161', 'Caisses'], ['5141', 'Banques (solde débiteur)'], ['6126', 'Achats de services']]);
const lookup = n => plan.has(n) ? {libelle: plan.get(n)} : null;
const nature = n => n === '3421' ? 'client' : n === '4411' ? 'fournisseur' : null;
const initial = {compte: '5161', libelle: 'Caisses', tiers_id: null, debit:'100', credit:''};
const next = synchroniserLibelleCompte(initial, '5141', lookup, nature);
const alt = synchroniserLibelleCompte(next, '6126', lookup, nature);
const unknown = synchroniserLibelleCompte(alt, '9999', lookup, nature);
console.log(JSON.stringify({next, alt, unknown, initial}));
''')
    assert result['next']['libelle'] == 'Banques (solde débiteur)'
    assert result['next']['credit'] == '' and result['next']['debit'] == '100'
    assert result['alt']['libelle'] == 'Achats de services'
    assert result['unknown']['libelle'] == ''  # Aucun libellé périmé sur un compte inconnu.
    assert result['initial']['libelle'] == 'Caisses'


def test_082_tiers_reste_selectionnable_sans_faux_libelle_compte():
    data = _node('''
import { synchroniserLibelleCompte } from './src/utils/libellesEcriture.js';
const lookup = n => ({3421:{libelle:'Clients'}, 3425:{libelle:'Effets à recevoir'}, 4411:{libelle:'Fournisseurs'}, 5141:{libelle:'Banques'}}[n] || null);
const nature = n => n === '3421' || n === '3425' ? 'client' : n === '4411' ? 'fournisseur' : null;
const banque = {compte: '5141',libelle:'Banques', tiers_id:null, debit:'', credit:'1200'};
const client = synchroniserLibelleCompte(banque,'3421',lookup,nature);
const selection = {...client,libelle:'CLIENT ALPHA',tiers_id:14};
const memeRole = synchroniserLibelleCompte(selection,'3425',lookup,nature);
const fournisseur = synchroniserLibelleCompte(memeRole,'4411',lookup,nature);
const banqueRetour = synchroniserLibelleCompte(selection,'5141',lookup,nature);
console.log(JSON.stringify({client,memeRole,fournisseur,banqueRetour}));
''')
    assert data['client']['libelle'] == '' and data['client']['tiers_id'] is None
    assert data['memeRole']['libelle'] == 'CLIENT ALPHA' and data['memeRole']['tiers_id'] == 14
    assert data['fournisseur']['libelle'] == '' and data['fournisseur']['tiers_id'] is None
    assert data['banqueRetour']['libelle'] == 'Banques' and data['banqueRetour']['tiers_id'] is None


def test_082_edition_et_modeles_preservent_descriptions_personnalisees():
    data = _node('''
import { initialiserLibelleLigne, synchroniserLibelleCompte } from './src/utils/libellesEcriture.js';
const lookup = n => ({5161:{libelle:'Caisses'},5141:{libelle:'Banques'},3421:{libelle:'Clients'}}[n] || null);
const nature = n => n === '3421' ? 'client' : null;
const edited = initialiserLibelleLigne({compte:'5141',libelle:'Transfert interne',debit:'100',tiers_id:null}, lookup,nature);
const blank = initialiserLibelleLigne({compte:'5141',libelle:'',tiers_id:null}, lookup,nature);
const tiers = initialiserLibelleLigne({compte:'3421',libelle:'ALPHA',tiers_id:14}, lookup,nature);
const same = synchroniserLibelleCompte(edited,'5141',lookup,nature);
const changed = synchroniserLibelleCompte(edited,'5161',lookup,nature);
console.log(JSON.stringify({edited,blank,tiers,same,changed}));
''')
    assert data['edited']['libelle'] == 'Transfert interne' and data['edited']['libelle_personnalise']
    assert data['blank']['libelle'] == 'Banques' and not data['blank']['libelle_personnalise']
    assert data['tiers']['libelle'] == 'ALPHA' and data['tiers']['tiers_id'] == 14
    assert data['same']['libelle'] == 'Transfert interne'
    assert data['changed']['libelle'] == 'Caisses' and not data['changed']['libelle_personnalise']


def test_082_isolation_plan_societe_et_payload_inchange():
    data = _node('''
import { synchroniserLibelleCompte } from './src/utils/libellesEcriture.js';
const nature = () => null;
const socA = n => n === '6111' ? {libelle:'Achats société A'} : null;
const socB = n => n === '6111' ? {libelle:'Achats société B'} : null;
const base = {compte:'',libelle:'',tiers_id:null,debit:'50',credit:''};
const a = synchroniserLibelleCompte(base,'6111',socA,nature);
const b = synchroniserLibelleCompte(base,'6111',socB,nature);
console.log(JSON.stringify({a,b}));
''')
    assert data['a']['libelle'] == 'Achats société A'
    assert data['b']['libelle'] == 'Achats société B'
    assert 'readOnly={!ligne.libelle_personnalise}' in FORM
    assert 'onSelect={tiers => majLigne(i, \'tiers_id\'' in FORM
    assert 'libelle: libelleEffectifLigne(l, trouverCompte, natureAuxiliaireCompte)' in FORM
    assert 'libelle_personnalise: l.libelle_personnalise' not in FORM.split('const donnees =', 1)[1].split('if (edition)', 1)[0]
    assert 'tiers_id: l.tiers_id || null' in FORM



def test_082_libelle_persiste_selon_plan_actif_ou_personnalisation():
    data = _node('''
import {libelleEffectifLigne} from './src/utils/libellesEcriture.js';
const planB = n => n === '6111' ? {libelle:'Achats société B'} : null;
const nature = n => n === '3421' ? 'client' : null;
console.log(JSON.stringify({
  actuel:libelleEffectifLigne({compte:'6111',libelle:'Achats société A',libelle_personnalise:false},planB,nature),
  personnalise:libelleEffectifLigne({compte:'6111',libelle:'Description spécifique',libelle_personnalise:true},planB,nature),
  tiers:libelleEffectifLigne({compte:'3421',libelle:'CLIENT ALPHA',libelle_personnalise:false},planB,nature)
}));
''')
    assert data == {'actuel':'Achats société B','personnalise':'Description spécifique','tiers':'CLIENT ALPHA'}

def test_082_ux_accessible_et_aucun_changement_regles_comptables():
    assert 'aria-label={ligne.libelle_personnalise' in FORM
    assert "'Personnaliser le libellé de la ligne'" in FORM
    assert "'Reprendre le libellé du compte'" in FORM
    assert 'className={styles.libelleCompteRow}' in FORM
    assert '.libelleCompteRow { display: flex;' in CSS
    assert 'const valide      = equilibre' in FORM
    assert "date_piece: datePiece || date" in FORM


def test_082_compilation_jsx():
    assert_jsx(['src/components/FormulaireEcriture.jsx', 'src/utils/libellesEcriture.js'])
