import { useEffect, useRef, useState } from 'react'
import { facturesLieesAPI, getToken } from '../services/api.js'
import { montantDecimalExact } from '../utils/montantDecimalExact.js'
import styles from './SocietesLiees.module.css'

export default function SuiviCorrespondances({ liaisonId, active }) {
  return <Panneau key={`${liaisonId}|${active}|${getToken()}`} liaisonId={liaisonId} />
}

function Panneau({ liaisonId }) {
  const token = getToken(), vivant = useRef(true), sequence = useRef(0)
  const [ouvert, setOuvert] = useState(false), [page, setPage] = useState(1)
  const [data, setData] = useState(null), [attente, setAttente] = useState(false), [erreur, setErreur] = useState('')
  const actuel = () => vivant.current && getToken() === token
  useEffect(() => { vivant.current = true; return () => { vivant.current = false; sequence.current += 1 } }, [])
  useEffect(() => { if (ouvert) charger(page) }, [ouvert, page])
  async function charger(p = page) {
    const n = ++sequence.current
    setAttente(true); setErreur(''); setData(null)
    try { const d = await facturesLieesAPI.lister(liaisonId, p); if (actuel() && n === sequence.current) setData(d) }
    catch (e) { if (actuel() && n === sequence.current) setErreur(e.message) }
    finally { if (actuel() && n === sequence.current) setAttente(false) }
  }
  const argent = v => v == null ? 'À vérifier' : `${montantDecimalExact(v)} MAD`
  return <details onToggle={e => setOuvert(e.currentTarget.open)}>
    <summary>Factures de la liaison {liaisonId}</summary>
    {ouvert && <section aria-label={`Factures de la liaison ${liaisonId}`}>
      <p>Suivi courant des factures correspondantes dans les deux sociétés.</p>
      <button type="button" disabled={attente} onClick={() => charger()}>Actualiser les factures liées</button>
      {attente && <p role="status">Chargement…</p>}
      {erreur && <p role="alert" className={styles.erreur}>{erreur}</p>}
      {data && <>
        <p>{data.total} correspondance(s) · {data.active ? 'Liaison active' : 'Liaison retirée, historique conservé'}</p>
        <p>{data.note}</p>
        {data.items.map(item => <article className={styles.liaison} key={item.id} aria-label={`Correspondance ${item.id}`}>
          <strong>Vente {item.vente.numero} → Achat {item.achat.numero || `brouillon #${item.facture_achat_id}`}</strong>
          {['vente', 'achat'].map(cote => {
            const doc = item[cote], f = doc.finances
            return <div key={cote} aria-label={cote === 'vente' ? 'Situation vendeur' : 'Situation acheteur'}>
              <h4>{cote === 'vente' ? 'Vendeur' : 'Acheteur'} · Exercice {doc.exercice}</h4>
              <p>{doc.statut === 'annulee' ? 'Facture annulée' : (doc.validee ? 'Facture validée' : 'Brouillon à vérifier')} · {doc.comptabilisee ? 'Comptabilisée' : 'À comptabiliser'}</p>
              <p>{f.etat_solde} · TTC {argent(f.total_ttc)} · {doc.statut === 'annulee' ? 'Reste calculé' : 'Reste à régler'} {argent(f.solde_restant)}</p>
              {f.diagnostic ? <p role="alert" className={styles.erreur}>{f.diagnostic}</p> : <>
                <p>Encaissé / payé : {argent(f.total_encaisse)} · Règlements en cours : {argent(f.total_reglement_en_cours)}</p>
                <p>Avoirs : {argent(f.total_avoirs)} · Acomptes : {argent(f.total_acomptes)} · RAS imputée : {argent(f.montant_ras)} · Crédit tiers : {argent(f.credit_tiers)}</p>
              </>}
            </div>
          })}
          {item.ecarts.length > 0 && <div role="alert"><strong>Écarts à vérifier</strong><ul>{item.ecarts.map(e => <li key={e}>{e}</li>)}</ul></div>}
        </article>)}
        {data.total === 0 && <p>Aucune facture correspondante enregistrée pour cette liaison.</p>}
        {data.total > data.taille && <nav aria-label={`Pages des factures liées ${liaisonId}`} className={styles.actions}>
          <button type="button" disabled={attente || page === 1} onClick={() => setPage(p => p - 1)}>Précédentes</button>
          <span>Page {page} / {Math.ceil(data.total / data.taille)}</span>
          <button type="button" disabled={attente || page * data.taille >= data.total} onClick={() => setPage(p => p + 1)}>Suivantes</button>
        </nav>}
      </>}
    </section>}
  </details>
}
