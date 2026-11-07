import { useEffect, useRef, useState } from 'react'
import { getToken, rasTvaRegistreAPI } from '../services/api.js'
import { montantDecimalExact } from '../utils/montantDecimalExact.js'
import styles from './RasTvaRegistre.module.css'
import RasTvaPieces from './RasTvaPieces.jsx'

const initiale = annee => `${Math.max(2026, annee)}-${String(new Date().getMonth() + 1).padStart(2, '0')}`
const argent = v => `${montantDecimalExact(v)} MAD`

export default function RasTvaPreparation({ annee }) {
  const [ouvert, setOuvert] = useState(false)
  const [periode, setPeriode] = useState(() => initiale(annee))
  const [data, setData] = useState(null)
  const [erreur, setErreur] = useState('')
  const [charge, setCharge] = useState(false)
  const [exportEnCours, setExportEnCours] = useState('')
  const [version, setVersion] = useState(0)
  const [page, setPage] = useState(0)
  const generation = useRef(0)
  const token = getToken()
  useEffect(() => { setPeriode(initiale(annee)) }, [annee])
  useEffect(() => {
    const id = ++generation.current
    setData(null); setErreur(''); setPage(0); setExportEnCours('')
    const valide = /^\d{4}-(0[1-9]|1[0-2])$/.test(periode) && Number(periode.slice(0, 4)) >= 2026
    if (!ouvert || !valide) { setCharge(false); return }
    setCharge(true)
    const [a, m] = periode.split('-')
    rasTvaRegistreAPI.preparation(a, m)
      .then(d => { if (id === generation.current && getToken() === token) setData(d) })
      .catch(e => { if (id === generation.current && getToken() === token) setErreur(e.message) })
      .finally(() => { if (id === generation.current) setCharge(false) })
    return () => { generation.current += 1 }
  }, [ouvert, periode, version, token])

  async function actualiserDocuments() {
    const id = ++generation.current
    setCharge(true); setErreur(''); setExportEnCours('')
    try {
      const [a, m] = periode.split('-')
      const d = await rasTvaRegistreAPI.preparation(a, m)
      if (id === generation.current && getToken() === token) setData(d)
    } catch (e) {
      if (id === generation.current && getToken() === token) { setErreur(`Fichier enregistré ; préparation à actualiser : ${e.message}`); setData(null) }
    } finally { if (id === generation.current) setCharge(false) }
  }

  async function exporter(format) {
    if (!data?.disponible || charge || exportEnCours) return
    const id = generation.current
    setExportEnCours(format); setErreur('')
    try {
      const [a, m] = periode.split('-')
      const r = await rasTvaRegistreAPI.exporterPreparation(a, m, format, data.empreinte_sha256)
      if (!r || id !== generation.current || getToken() !== token) return
      const url = URL.createObjectURL(r.blob), lien = document.createElement('a')
      lien.href = url; lien.download = r.filename; document.body.appendChild(lien); lien.click(); lien.remove()
      setTimeout(() => URL.revokeObjectURL(url), 1000)
    } catch (e) {
      if (id === generation.current && getToken() === token) { setErreur(e.message); setData(null) }
    } finally { if (id === generation.current) setExportEnCours('') }
  }

  return <details className={styles.panel} onToggle={e => { if (e.target === e.currentTarget) setOuvert(e.currentTarget.open) }}>
    <summary>Préparation mensuelle des retenues opérées</summary>
    <section aria-label="Préparation mensuelle RAS TVA" className={styles.contenu}>
      <div className={styles.actions}>
        <label>Mois de versement prévu <input aria-label="Mois de versement prévu" type="month" min="2026-01" max="9999-12" value={periode} onChange={e => setPeriode(e.target.value)} /></label>
        <button type="button" disabled={charge || Boolean(exportEnCours)} onClick={() => setVersion(v => v + 1)}>Actualiser la préparation</button>
      </div>
      {charge && <p role="status">Chargement de la préparation…</p>}
      {erreur && <p role="alert" className={styles.erreur}>{erreur}</p>}
      {data && !data.disponible && <p>Préparation indisponible : migration {data.migration_requise} à appliquer par votre administrateur.</p>}
      {data?.disponible && <>
        <p><strong>Paiements du {data.mois_paiement} · Mois de versement prévu : {data.periode}</strong></p>
        <p className={styles.note}>{data.note}</p>
        <section className={styles.carte} aria-label="Montants capturés du mois">
          <dl>{data.presentation.groupes.map(([cle, libelle]) => {
            const t = data.totaux.achat[cle]
            return <div key={cle}><dt>{libelle} · {t.nombre}</dt><dd>{argent(t.montant)}{t.montant === null && <small>Partie certaine : {argent(t.partie_certaine)}</small>}</dd></div>
          })}</dl>
        </section>
        <div className={styles.actions}><span>Exporter la préparation du mois :</span>
          {[['csv', 'CSV'], ['xlsx', 'Excel'], ['pdf', 'PDF']].map(([fmt, nom]) => <button key={fmt} type="button" disabled={charge || Boolean(exportEnCours)} onClick={() => exporter(fmt)}>{exportEnCours === fmt ? 'Téléchargement…' : nom}</button>)}
        </div>
        {!data.lignes.length && <p>Aucune capture guidée opérée sur achats pour ces paiements.</p>}
        <ol className={styles.liste}>{data.lignes.slice(page * 20, (page + 1) * 20).map(r => <li key={r.capture_id}>
          <article className={styles.ligne} aria-label={`Préparation capture TVA ${r.capture_id}`}>
            <div className={styles.entete}><strong>{r.numero_facture} · {r.date_paiement}</strong><span>{r.annulation_id ? 'Annulée · à rapprocher' : r.od_validee ? 'OD validée' : 'OD à valider'}</span></div>
            <p>{r.tiers} · RAS saisie : {argent(r.retenue_tva)}</p>
            <p>Référence : {r.reference} · Compte choisi : {r.compte_destination} · OD : {r.numero_ecriture || `#${r.ecriture_id}`}</p>
            <p>Ventilation : {r.justification_quote_part} · Attestation : {r.reference_attestation || 'Référence non renseignée'}</p>
            {r.annulation_id && <p>Annulation du {r.date_annulation} · Contrepassation #{r.od_annulation_id}. Rapprocher le bordereau et son éventuelle régularisation.</p>}
            <RasTvaPieces key={`${token}:${r.capture_id}`} ligne={r} onChange={actualiserDocuments} />
            {r.diagnostics.map(d => <p key={d} className={styles.erreur}>{d}</p>)}
          </article>
        </li>)}</ol>
        {data.lignes.length > 20 && <div className={styles.actions}>
          <button type="button" disabled={page === 0} onClick={() => setPage(p => p - 1)}>Précédent</button>
          <span>Page {page + 1} / {Math.ceil(data.lignes.length / 20)} · {data.lignes.length} captures</span>
          <button type="button" disabled={(page + 1) * 20 >= data.lignes.length} onClick={() => setPage(p => p + 1)}>Suivant</button>
        </div>}
      </>}
    </section>
  </details>
}
