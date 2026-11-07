import { useEffect, useRef, useState } from 'react'
import { getToken, rasTvaRegistreAPI } from '../services/api.js'
import { montantDecimalExact } from '../utils/montantDecimalExact.js'
import styles from './RasTvaRegistre.module.css'
import RasTvaPreparation from './RasTvaPreparation.jsx'
import RasTvaPieces from './RasTvaPieces.jsx'
import RasTvaRapprochement from './RasTvaRapprochement.jsx'

const montant = v => `${montantDecimalExact(v)} MAD`

export default function RasTvaRegistre({ annee }) {
  const [data, setData] = useState(null)
  const [erreur, setErreur] = useState('')
  const [chargement, setChargement] = useState(false)
  const [telechargement, setTelechargement] = useState('')
  const [version, setVersion] = useState(0)
  const [page, setPage] = useState(0)
  const generation = useRef(0)
  const token = getToken()
  useEffect(() => {
    const id = ++generation.current
    setChargement(true); setData(null); setErreur(''); setPage(0); setTelechargement('')
    rasTvaRegistreAPI.lire(annee)
      .then(d => { if (id === generation.current && getToken() === token) setData(d) })
      .catch(e => { if (id === generation.current && getToken() === token) setErreur(e.message) })
      .finally(() => { if (id === generation.current) setChargement(false) })
    return () => { generation.current += 1 }
  }, [annee, token, version])

  async function actualiserDocuments() {
    const id = ++generation.current
    setChargement(true); setErreur(''); setTelechargement('')
    try {
      const d = await rasTvaRegistreAPI.lire(annee)
      if (id === generation.current && getToken() === token) setData(d)
    } catch (e) {
      if (id === generation.current && getToken() === token) { setErreur(`Fichier enregistré ; registre à actualiser : ${e.message}`); setData(null) }
    } finally { if (id === generation.current) setChargement(false) }
  }

  async function exporter(format) {
    if (!data?.disponible || telechargement || chargement) return
    const id = generation.current
    setTelechargement(format); setErreur('')
    try {
      const r = await rasTvaRegistreAPI.exporter(annee, format, data.empreinte_sha256)
      if (!r || id !== generation.current || getToken() !== token) return
      const url = URL.createObjectURL(r.blob)
      const lien = document.createElement('a')
      lien.href = url; lien.download = r.filename; document.body.appendChild(lien); lien.click(); lien.remove()
      setTimeout(() => URL.revokeObjectURL(url), 1000)
    } catch (e) {
      if (id === generation.current && getToken() === token) { setErreur(e.message); setData(null) }
    } finally { if (id === generation.current) setTelechargement('') }
  }

  return <><details className={styles.panel}>
    <summary>Registre des retenues TVA · {annee}</summary>
    <section aria-label="Registre interne des retenues TVA" className={styles.contenu}>
      <div className={styles.actions}><button type="button" onClick={() => setVersion(v => v + 1)} disabled={chargement || Boolean(telechargement)}>Actualiser le registre</button></div>
      {chargement && <p role="status">Chargement du registre…</p>}
      {erreur && <p role="alert" className={styles.erreur}>{erreur}</p>}
      {data && !data.disponible && <p>Registre indisponible : migration {data.migration_requise} à appliquer par votre administrateur. Aucune migration n’est exécutée ici.</p>}
      {data?.disponible && <>
        <p className={styles.note}>{data.note}</p>
        <div className={styles.totaux}>
          {['achat', 'vente'].map(nature => <section key={nature} aria-label={nature === 'achat' ? 'Retenues opérées sur achats' : 'Retenues subies sur ventes'} className={styles.carte}>
            <strong>{nature === 'achat' ? 'Opérées sur achats' : 'Subies sur ventes'}</strong>
            <dl>
              {[['declarees', 'Saisies dans l’année'], ['actives', 'Captures actives'], ['actives_validees', 'Actives · OD validées'], ['annulees', 'Captures annulées'], ['annulations_annee', 'Annulations de l’année']].map(([cle, libelle]) => {
                const t = data.totaux[nature][cle]
                return <div key={cle}><dt>{libelle}</dt><dd>{montant(t.montant)}{t.montant === null && <small>Partie certaine : {montant(t.partie_certaine)}</small>}</dd></div>
              })}
            </dl>
          </section>)}
        </div>
        <div className={styles.actions}><span>Exporter l’année complète :</span>
          {[['csv', 'CSV'], ['xlsx', 'Excel'], ['pdf', 'PDF']].map(([fmt, nom]) => <button key={fmt} type="button" disabled={chargement || Boolean(telechargement)} onClick={() => exporter(fmt)}>{telechargement === fmt ? 'Téléchargement…' : nom}</button>)}
        </div>
        {!data.lignes.length && <p>Aucune capture TVA guidée tracée pour cette année.</p>}
        <ol className={styles.liste}>
          {data.lignes.slice(page * 20, (page + 1) * 20).map(r => <li key={r.capture_id}>
            <article aria-label={`Capture TVA ${r.capture_id}`} className={styles.ligne}>
              <div className={styles.entete}><strong>#{r.capture_id} · {r.nature === 'achat' ? 'Opérée' : 'Subie'} · {r.date_paiement}</strong><span>{r.annulation_id ? 'Annulée' : r.od_validee ? 'OD validée' : 'OD à valider'}</span></div>
              <p><strong>{r.numero_facture}</strong> · {r.tiers}</p>
              <dl className={styles.montants}>
                {[['retenue_tva', 'RAS saisie'], ['quote_part_ttc', 'Quote-part TTC'], ['quote_part_tva', 'TVA de la quote-part'], ['net_reglement', 'Trésorerie']].map(([k, label]) => <div key={k}><dt>{label}</dt><dd>{montant(r[k])}</dd></div>)}
              </dl>
              <details><summary>Pièces et écriture</summary>
                <p>Référence RAS : {r.reference} · Compte choisi : {r.compte_destination}</p>
                <p>OD : {r.numero_ecriture || `#${r.ecriture_id}`} · Justificatif : {r.justification_quote_part}</p>
                <p>Attestation déclarée : {r.reference_attestation || 'Référence non renseignée'}</p>
                <p>{r.nature === 'vente' ? 'Mois prévu chez le client payeur' : 'Mois de reversement prévu'} : {r.mois_reversement_prevu || 'À vérifier'}. Aucun versement n’est justifié par ce registre.</p>
                {r.annulation_id && <p>Annulation du {r.date_annulation} · OD de contrepassation #{r.od_annulation_id}</p>}
              </details>
              <RasTvaPieces key={`${token}:${r.capture_id}`} ligne={r} onChange={actualiserDocuments} />
              {r.nature === 'achat' && <RasTvaRapprochement key={`rapprochement:${token}:${r.capture_id}`} captureId={r.capture_id} />}
              {r.diagnostics.map(d => <p key={d} className={styles.erreur}>{d}</p>)}
            </article>
          </li>)}
        </ol>
        {data.lignes.length > 20 && <div className={styles.actions}>
          <button type="button" disabled={page === 0} onClick={() => setPage(p => p - 1)}>Précédent</button>
          <span>Page {page + 1} / {Math.ceil(data.lignes.length / 20)} · {data.lignes.length} captures</span>
          <button type="button" disabled={(page + 1) * 20 >= data.lignes.length} onClick={() => setPage(p => p + 1)}>Suivant</button>
        </div>}
      </>}
    </section>
  </details><RasTvaPreparation key={annee} annee={annee} /></>
}
