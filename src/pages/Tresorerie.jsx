import { useEffect, useMemo, useState } from 'react'
import Modal from '../components/Modal.jsx'
import EtatVide from '../components/EtatVide.jsx'
import { tresorerieAPI, peutEcrire } from '../services/api.js'
import { formatMAD } from '../data/donnees.js'
import { dateLocaleISO } from '../utils/formUtils.js'
import { notifier } from '../services/notifications.js'
import styles from './Tresorerie.module.css'

// Lot 980 : volet Trésorerie — banques, caisses, valeurs à encaisser, et
// virements de fonds (alimenter la caisse depuis la banque, verser en banque).

const ICONES = { banques: 'ti-building-bank', caisses: 'ti-cash', valeurs: 'ti-file-dollar', virements: 'ti-arrows-exchange', credits: 'ti-credit-card' }
const estCaisse = c => String(c || '').startsWith('516')
const dateFr = d => d ? String(d).slice(0, 10).split('-').reverse().join('/') : '—'

function Montant({ valeur }) {
  return <span className={valeur < 0 ? styles.negatif : undefined}>{formatMAD(valeur)}</span>
}

function nomCompte(c) {
  return `${c.compte} — ${c.banques?.length ? c.banques.join(', ') : c.libelle}`
}

function FormulaireVirement({ situation, sensInitial, onFermer, onSucces }) {
  const comptes = useMemo(() => situation.categories
    .filter(c => c.cle === 'banques' || c.cle === 'caisses').flatMap(c => c.comptes), [situation])
  const banques = comptes.filter(c => !estCaisse(c.compte))
  const caisses = comptes.filter(c => estCaisse(c.compte))
  const [sens, setSens] = useState(sensInitial)
  const defauts = s => s === 'retrait' ? [banques[0]?.compte || '5141', caisses[0]?.compte || '5161']
    : s === 'versement' ? [caisses[0]?.compte || '5161', banques[0]?.compte || '5141']
    : [banques[0]?.compte || '5141', banques[1]?.compte || caisses[0]?.compte || '5161']
  const [form, setForm] = useState(() => {
    const [src, dst] = defauts(sensInitial)
    return { date: dateLocaleISO(), montant: '', compte_source: src, compte_destination: dst, reference: '', libelle: '', valider: true }
  })
  const [envoi, setEnvoi] = useState(false)
  const [erreur, setErreur] = useState('')
  const maj = (k, v) => setForm(p => ({ ...p, [k]: v }))
  function choisirSens(s) {
    setSens(s)
    const [src, dst] = defauts(s)
    setForm(p => ({ ...p, compte_source: src, compte_destination: dst }))
  }
  const montant = Number(String(form.montant).replace(',', '.'))
  const source = comptes.find(c => c.compte === form.compte_source)
  const soldeSource = source ? source.solde : 0
  const caisseInsuffisante = estCaisse(form.compte_source) && montant > soldeSource + 0.001
  const journal = c => estCaisse(c) ? 'CA (Caisse)' : 'BQ (Banque)'
  const listeSource = sens === 'retrait' ? banques : sens === 'versement' ? caisses : comptes
  const listeDest = sens === 'retrait' ? caisses : sens === 'versement' ? banques : comptes
  const titre = sens === 'retrait' ? 'Alimenter la caisse depuis la banque' : sens === 'versement' ? 'Verser des espèces en banque' : 'Virement de fonds'

  async function envoyer() {
    setErreur('')
    if (!(montant > 0)) { setErreur('Indiquez un montant supérieur à zéro.'); return }
    if (form.compte_source === form.compte_destination) { setErreur('Choisissez deux comptes différents.'); return }
    setEnvoi(true)
    try {
      const r = await tresorerieAPI.virement({ ...form, montant: montant.toFixed(2), reference: form.reference || null, libelle: form.libelle || null })
      notifier.succes(`${r.sens} : ${formatMAD(r.montant)} MAD enregistré (${r.ecritures.length} écritures${r.valide ? ', validées' : ', en brouillon'}).`)
      await onSucces()
      onFermer()
    } catch (e) { setErreur(e.message) } finally { setEnvoi(false) }
  }

  return <Modal titre={titre} icone="ti-arrows-exchange" onFermer={onFermer} largeur="md">
    <div className={styles.form}>
      <div className={styles.sens} role="group" aria-label="Type de mouvement">
        {[['retrait', 'Banque → caisse'], ['versement', 'Caisse → banque'], ['autre', 'Autre virement']].map(([v, l]) =>
          <button key={v} type="button" className={`${styles.sensBtn} ${sens === v ? styles.sensActif : ''}`} aria-pressed={sens === v} onClick={() => choisirSens(v)}>{l}</button>)}
      </div>
      <div className={styles.formGrid2}>
        <label>
          <span className={styles.label}>Compte qui donne</span>
          <select className={styles.input} value={form.compte_source} onChange={e => maj('compte_source', e.target.value)}>
            {listeSource.map(c => <option key={c.compte} value={c.compte}>{nomCompte(c)} · {formatMAD(c.solde)} MAD</option>)}
          </select>
        </label>
        <label>
          <span className={styles.label}>Compte qui reçoit</span>
          <select className={styles.input} value={form.compte_destination} onChange={e => maj('compte_destination', e.target.value)}>
            {listeDest.map(c => <option key={c.compte} value={c.compte}>{nomCompte(c)} · {formatMAD(c.solde)} MAD</option>)}
          </select>
        </label>
        <label>
          <span className={styles.label}>Montant (MAD)</span>
          <input className={styles.input} inputMode="decimal" value={form.montant} onChange={e => maj('montant', e.target.value)} placeholder="0,00" autoFocus />
        </label>
        <label>
          <span className={styles.label}>Date</span>
          <input className={styles.input} type="date" value={form.date} onChange={e => maj('date', e.target.value)} />
        </label>
        <label>
          <span className={styles.label}>Référence (n° de chèque de retrait, bordereau…)</span>
          <input className={styles.input} value={form.reference} onChange={e => maj('reference', e.target.value)} placeholder="Générée si vide" />
        </label>
        <label>
          <span className={styles.label}>Libellé</span>
          <input className={styles.input} value={form.libelle} onChange={e => maj('libelle', e.target.value)} placeholder="Proposé automatiquement si vide" />
        </label>
      </div>
      {caisseInsuffisante && <div className={styles.alerte}>La caisse n'a que {formatMAD(soldeSource)} MAD : une caisse ne peut pas devenir créditrice, le virement sera refusé.</div>}
      <div className={styles.apercu} aria-label="Écritures qui seront passées">
        <div className={styles.apercuTitre}>Écritures qui seront passées (compte de liaison 5115 Virements de fonds)</div>
        <table className={styles.table}><thead><tr><th>Journal</th><th>Compte</th><th className={styles.num}>Débit</th><th className={styles.num}>Crédit</th></tr></thead><tbody>
          <tr><td rowSpan={2}>{journal(form.compte_source)}</td><td>5115</td><td className={styles.num}>{montant > 0 ? formatMAD(montant) : '—'}</td><td /></tr>
          <tr><td>{form.compte_source}</td><td /><td className={styles.num}>{montant > 0 ? formatMAD(montant) : '—'}</td></tr>
          <tr><td rowSpan={2}>{journal(form.compte_destination)}</td><td>{form.compte_destination}</td><td className={styles.num}>{montant > 0 ? formatMAD(montant) : '—'}</td><td /></tr>
          <tr><td>5115</td><td /><td className={styles.num}>{montant > 0 ? formatMAD(montant) : '—'}</td></tr>
        </tbody></table>
      </div>
      <label className={styles.check}><input type="checkbox" checked={form.valider} onChange={e => maj('valider', e.target.checked)} /> Valider immédiatement les deux écritures</label>
      {erreur && <div className={styles.erreur} role="alert">{erreur}</div>}
      <div className={styles.footer}>
        <button type="button" className={styles.btnSec} onClick={onFermer}>Annuler</button>
        <button type="button" className={styles.btnPrim} onClick={envoyer} disabled={envoi}><i className="ti ti-check" aria-hidden="true" /> Enregistrer</button>
      </div>
    </div>
  </Modal>
}

export default function Tresorerie() {
  const [au, setAu] = useState(dateLocaleISO())
  const [situation, setSituation] = useState(null)
  const [erreur, setErreur] = useState('')
  const [chargement, setChargement] = useState(false)
  const [virement, setVirement] = useState(null)
  const [especes, setEspeces] = useState([])  // lot 981 : espèces aux fournisseurs au-delà des limites
  const ecriture = peutEcrire()

  async function charger() {
    setChargement(true); setErreur('')
    try { setSituation(await tresorerieAPI.situation(au)) } catch (e) { setErreur(e.message) } finally { setChargement(false) }
    tresorerieAPI.especesFournisseurs(`${String(au).slice(0, 4)}-01-01`, au).then(r => setEspeces(r.depassements || [])).catch(() => setEspeces([]))
  }
  useEffect(() => { charger() }, [au])

  const cat = cle => situation?.categories.find(c => c.cle === cle)
  const visibles = (situation?.categories || []).filter(c => c.comptes.length > 0 && (['banques', 'caisses'].includes(c.cle) || c.comptes.some(x => x.solde || x.brouillons)))
  const aucunMouvement = situation && !situation.mouvements.length && visibles.every(c => c.comptes.every(x => !x.solde && !x.brouillons))

  return <div className={styles.page}>
    <div className={styles.topbar}>
      <div>
        <h1 className={styles.pageTitle}>Trésorerie</h1>
        <div className={styles.sousTitre}>Soldes comptables des banques, caisses et valeurs à encaisser, issus des écritures validées.</div>
      </div>
      <div className={styles.actions}>
        <label><span className={styles.label}>Situation au</span><input className={styles.input} type="date" value={au} onChange={e => setAu(e.target.value)} /></label>
        <button type="button" className={styles.btnSec} onClick={charger} disabled={chargement}><i className="ti ti-refresh" aria-hidden="true" /> Actualiser</button>
        {ecriture && situation && <>
          <button type="button" className={styles.btnSec} onClick={() => setVirement('autre')}><i className="ti ti-arrows-exchange" aria-hidden="true" /> Virement de fonds</button>
          <button type="button" className={styles.btnPrim} onClick={() => setVirement('retrait')}><i className="ti ti-cash" aria-hidden="true" /> Alimenter la caisse</button>
        </>}
      </div>
    </div>

    <div className={styles.content}>
      {erreur && <div className={styles.erreur} role="alert">{erreur}</div>}
      {situation && <>
        <div className={styles.kpiGrid}>
          <div className={styles.kpiCard}><div className={styles.kpiLabel}><i className="ti ti-building-bank" aria-hidden="true" />Banques</div><div className={styles.kpiValeur}><Montant valeur={cat('banques').solde} /></div></div>
          <div className={styles.kpiCard}><div className={styles.kpiLabel}><i className="ti ti-cash" aria-hidden="true" />Caisses</div><div className={styles.kpiValeur}><Montant valeur={cat('caisses').solde} /></div></div>
          <div className={styles.kpiCard}><div className={styles.kpiLabel}><i className="ti ti-file-dollar" aria-hidden="true" />Chèques et effets à encaisser</div><div className={styles.kpiValeur}><Montant valeur={cat('valeurs').solde} /></div></div>
          <div className={styles.kpiCard}><div className={styles.kpiLabel}><i className="ti ti-scale" aria-hidden="true" />Trésorerie nette</div><div className={styles.kpiValeur}><Montant valeur={situation.tresorerie_nette} /></div><div className={styles.kpiNote}>Actif de trésorerie moins crédits de trésorerie</div></div>
        </div>

        {aucunMouvement && <EtatVide icone="ti-building-bank" titre="Aucun mouvement de trésorerie">
          Les soldes apparaissent dès qu'un règlement, une écriture de banque ou de caisse, ou un solde d'ouverture est enregistré. Pour alimenter la caisse, utilisez « Alimenter la caisse ».
        </EtatVide>}

        {visibles.map(c => <div key={c.cle} className={styles.card}>
          <div className={styles.cardHeader}>
            <span className={styles.cardTitle}><i className={`ti ${ICONES[c.cle]}`} aria-hidden="true" />{c.titre}</span>
            <span className={styles.cardTotal}><Montant valeur={c.cote === 'passif' ? -c.solde : c.solde} /> MAD</span>
          </div>
          <div className={styles.tableWrapper}><table className={styles.table}>
            <thead><tr><th>Compte</th><th>Libellé</th><th className={styles.num}>Solde validé</th><th className={styles.num}>Brouillons non validés</th><th>Dernier mouvement</th></tr></thead>
            <tbody>{c.comptes.map(x => <tr key={x.compte}>
              <td>{x.compte}</td>
              <td>{x.banques?.length ? x.banques.join(', ') : x.libelle}{x.alerte && <div><span className={styles.alerte}>{x.alerte}</span></div>}</td>
              <td className={styles.num}><Montant valeur={c.cote === 'passif' ? -x.solde : x.solde} /></td>
              <td className={styles.num}>{x.brouillons ? <Montant valeur={c.cote === 'passif' ? -x.brouillons : x.brouillons} /> : <span className={styles.discret}>—</span>}</td>
              <td>{dateFr(x.dernier_mouvement)}</td>
            </tr>)}</tbody>
          </table></div>
        </div>)}

        {especes.length > 0 && <div className={styles.card} aria-label="Espèces aux fournisseurs au-delà des limites">
          <div className={styles.cardHeader}><span className={styles.cardTitle}><i className="ti ti-alert-triangle" aria-hidden="true" />Fournisseurs payés en espèces au-delà de 5 000 MAD/jour ou 50 000 MAD/mois ({String(au).slice(0, 4)})</span></div>
          <div className={styles.tableWrapper}><table className={styles.table}>
            <thead><tr><th>Fournisseur</th><th>Mois</th><th className={styles.num}>Espèces versées</th><th className={styles.num}>Dans les limites</th><th className={styles.num}>Au-delà</th><th>Jours au-delà de 5 000</th></tr></thead>
            <tbody>{especes.map(x => <tr key={`${x.fournisseur}-${x.mois}`}>
              <td>{x.fournisseur}</td><td>{x.mois.slice(5)}/{x.mois.slice(0, 4)}</td>
              <td className={styles.num}>{formatMAD(x.total_especes)}</td><td className={styles.num}>{formatMAD(x.montant_admis)}</td>
              <td className={styles.num}><strong>{formatMAD(x.montant_au_dela)}</strong></td>
              <td>{x.jours_au_dela.map(j => dateFr(j.date)).join(', ') || '—'}</td>
            </tr>)}</tbody>
          </table></div>
          <div className={styles.discret} style={{ padding: '8px 16px' }}>CGI 2026 art. 11-II et 106-II : au-delà de ces limites, la charge n'est pas entièrement déductible et la TVA n'est pas récupérable. Les montants sont repris dans Résultat fiscal / IS (à confirmer) et signalés dans la déclaration de TVA.</div>
        </div>}

        {situation.mouvements.length > 0 && <div className={styles.card}>
          <div className={styles.cardHeader}><span className={styles.cardTitle}><i className="ti ti-list" aria-hidden="true" />Derniers mouvements de banque et de caisse</span></div>
          <div className={styles.tableWrapper}><table className={styles.table}>
            <thead><tr><th>Date</th><th>Journal</th><th>Libellé</th><th>Compte</th><th className={styles.num}>Entrée</th><th className={styles.num}>Sortie</th><th>État</th></tr></thead>
            <tbody>{situation.mouvements.map((m, i) => <tr key={`${m.ecriture_id}-${m.compte}-${i}`}>
              <td>{dateFr(m.date)}</td><td>{m.journal}</td><td>{m.libelle}</td><td>{m.compte}</td>
              <td className={styles.num}>{m.debit ? formatMAD(m.debit) : ''}</td>
              <td className={styles.num}>{m.credit ? formatMAD(m.credit) : ''}</td>
              <td>{m.est_validee ? 'Validée' : <span className={styles.discret}>Brouillon</span>}</td>
            </tr>)}</tbody>
          </table></div>
        </div>}
      </>}
    </div>

    {virement && situation && <FormulaireVirement situation={situation} sensInitial={virement} onFermer={() => setVirement(null)} onSucces={charger} />}
  </div>
}
