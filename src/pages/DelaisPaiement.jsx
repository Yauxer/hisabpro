import { useEffect, useMemo, useState } from 'react'
import { useExercice } from '../data/ExerciceContext.jsx'
import { delaisPaiementAPI, peutEcrire } from '../services/api.js'
import styles from './DelaisPaiement.module.css'

function mad(v) {
  if (v === null || v === undefined || Number.isNaN(Number(v))) return '—'
  return `${Number(v).toLocaleString('fr-MA', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} MAD`
}

function dateFR(v) {
  if (!v) return '—'
  const [y, m, d] = String(v).slice(0, 10).split('-')
  return `${d}/${m}/${y}`
}

function Badge({ tone = 'neutral', children }) {
  return <span className={`${styles.badge} ${styles[`badge_${tone}`] || ''}`}>{children}</span>
}

function MetaModal({ ligne, onClose, onSaved }) {
  const [form, setForm] = useState({
    date_livraison_service: ligne.date_livraison_service || '',
    litige_judiciaire: !!ligne.litige_judiciaire,
    reference_litige: ligne.reference_litige || '',
    hors_champ: !!ligne.hors_champ,
    motif_hors_champ: ligne.motif_hors_champ || '',
  })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  async function save(e) {
    e.preventDefault()
    setSaving(true); setError('')
    try {
      await delaisPaiementAPI.completer(ligne.facture_id, {
        date_livraison_service: form.date_livraison_service || null,
        litige_judiciaire: form.litige_judiciaire,
        reference_litige: form.litige_judiciaire ? form.reference_litige : null,
        hors_champ: form.hors_champ,
        motif_hors_champ: form.hors_champ ? form.motif_hors_champ : null,
      })
      await onSaved()
      onClose()
    } catch (err) { setError(err.message || 'Erreur') }
    finally { setSaving(false) }
  }

  return (
    <div className={styles.overlay} onMouseDown={e => e.target === e.currentTarget && onClose()}>
      <form className={styles.modal} onSubmit={save}>
        <div className={styles.modalHeader}>
          <div>
            <h3>Compléter la déclaration</h3>
            <span>{ligne.reference_facture || ligne.numero_interne} · {ligne.fournisseur}</span>
          </div>
          <button type="button" className={styles.iconBtn} onClick={onClose}><i className="ti ti-x" /></button>
        </div>
        {error && <div className={styles.error}>{error}</div>}
        <label className={styles.field}>
          <span>Date de livraison / service</span>
          <input type="date" value={form.date_livraison_service} onChange={e => setForm(f => ({ ...f, date_livraison_service: e.target.value }))} />
        </label>
        <label className={styles.checkLine}>
          <input type="checkbox" checked={form.litige_judiciaire} onChange={e => setForm(f => ({ ...f, litige_judiciaire: e.target.checked }))} />
          <span>Facture faisant l’objet d’un litige judiciaire</span>
        </label>
        {form.litige_judiciaire && (
          <label className={styles.field}>
            <span>Référence du litige</span>
            <input value={form.reference_litige} onChange={e => setForm(f => ({ ...f, reference_litige: e.target.value }))} placeholder="Tribunal / dossier / référence" />
          </label>
        )}
        <label className={styles.checkLine}>
          <input type="checkbox" checked={form.hors_champ} onChange={e => setForm(f => ({ ...f, hors_champ: e.target.checked }))} />
          <span>Transaction hors champ de la loi 69-21</span>
        </label>
        {form.hors_champ && (
          <label className={styles.field}>
            <span>Motif d’exclusion</span>
            <input value={form.motif_hors_champ} onChange={e => setForm(f => ({ ...f, motif_hors_champ: e.target.value }))} placeholder="Motif à documenter" />
          </label>
        )}
        <div className={styles.modalActions}>
          <button type="button" className={styles.secondaryBtn} onClick={onClose}>Annuler</button>
          <button type="submit" className={styles.primaryBtn} disabled={saving || !peutEcrire()}>{saving ? 'Enregistrement…' : 'Enregistrer'}</button>
        </div>
      </form>
    </div>
  )
}

export default function DelaisPaiement() {
  const { annee } = useExercice()
  const now = new Date()
  const trimestreDefaut = annee === now.getFullYear() ? Math.min(4, Math.floor(now.getMonth() / 3) + 1) : 4
  const [trimestre, setTrimestre] = useState(trimestreDefaut)
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [edit, setEdit] = useState(null)
  const [exporting, setExporting] = useState(false)

  useEffect(() => { setTrimestre(trimestreDefaut) }, [annee])

  async function load() {
    setLoading(true); setError('')
    try { setData(await delaisPaiementAPI.rapport(annee, trimestre)) }
    catch (err) { setError(err.message || 'Erreur') }
    finally { setLoading(false) }
  }
  useEffect(() => { load() }, [annee, trimestre])

  async function exporter() {
    setExporting(true); setError('')
    try {
      const file = await delaisPaiementAPI.exporterCSV(annee, trimestre)
      if (!file) return
      const url = URL.createObjectURL(file.blob)
      const a = document.createElement('a'); a.href = url; a.download = file.filename; a.click()
      URL.revokeObjectURL(url)
    } catch (err) { setError(err.message || 'Erreur export') }
    finally { setExporting(false) }
  }

  const assujetti = data?.assujettissement?.assujetti
  const rows = data?.factures || []
  const incomplete = useMemo(() => rows.filter(r => !r.completude?.complete).length, [rows])

  return (
    <div className={styles.page} data-form-page>
      <div className={styles.header}>
        <div>
          <h1>Délais de paiement</h1>
          <p>Loi 69-21 · état préparatoire des factures fournisseurs</p>
        </div>
        <div className={styles.headerActions}>
          <select value={trimestre} onChange={e => setTrimestre(Number(e.target.value))}>
            <option value={1}>T1 · Jan–Mar</option><option value={2}>T2 · Avr–Juin</option>
            <option value={3}>T3 · Juil–Sep</option><option value={4}>T4 · Oct–Déc</option>
          </select>
          <button className={styles.secondaryBtn} onClick={load} disabled={loading}><i className="ti ti-refresh" /> Actualiser</button>
          <button className={styles.primaryBtn} onClick={exporter} disabled={loading || exporting}><i className="ti ti-file-spreadsheet" /> {exporting ? 'Export…' : 'Exporter CSV'}</button>
        </div>
      </div>

      {error && <div className={styles.error}>{error}</div>}

      <div className={styles.legalBox}>
        <div>
          <strong>Situation {annee} · T{trimestre}</strong>
          <span>Déclaration trimestrielle à partir de 2026 pour les entreprises dont le CA HT de référence dépasse 2 M MAD.</span>
        </div>
        {assujetti === true && <Badge tone="red">Déclaration requise</Badge>}
        {assujetti === false && <Badge tone="green">Sous le seuil de 2 M MAD</Badge>}
        {assujetti == null && <Badge tone="orange">Assujettissement à confirmer</Badge>}
      </div>

      <div className={styles.kpis}>
        <div className={styles.kpi}><span>CA HT de référence</span><strong>{mad(data?.assujettissement?.ca_ht_reference)}</strong><small>Exercice {data?.assujettissement?.exercice_reference || '—'}{data?.assujettissement?.exercice_reference_cloture === false ? ' · non clôturé' : ''}</small></div>
        <div className={styles.kpi}><span>Factures à déclarer</span><strong>{data?.resume?.nb_factures ?? '—'}</strong><small>{incomplete ? `${incomplete} à compléter` : 'Données complètes'}</small></div>
        <div className={styles.kpi}><span>Impayé fin de période</span><strong>{mad(data?.resume?.montant_non_paye_fin_periode)}</strong><small>Factures échues</small></div>
        <div className={styles.kpi}><span>Payé hors délai</span><strong>{mad(data?.resume?.montant_paye_hors_delai_periode)}</strong><small>Pendant le trimestre</small></div>
        <div className={styles.kpi}><span>Amende indicative</span><strong>{mad(data?.resume?.amende_indicative)}</strong><small>Simulation · à contrôler</small></div>
      </div>

      {(data?.avertissements || []).length > 0 && (
        <div className={styles.warnings}>{data.avertissements.map((w, i) => <div key={i}><i className="ti ti-alert-triangle" /> {w}</div>)}</div>
      )}

      <div className={styles.tableCard}>
        <div className={styles.tableHeader}>
          <div><strong>État détaillé</strong><span>{dateFR(data?.date_debut)} → {dateFR(data?.date_fin)}</span></div>
          <span className={styles.note}>Export préparatoire — contrôle/visa professionnel avant dépôt DGI</span>
        </div>
        <div className={styles.tableScroll}>
          <table>
            <thead><tr>
              <th>Facture</th><th>Fournisseur</th><th>Émission</th><th>Livraison</th><th>Échéance</th>
              <th className={styles.right}>TTC</th><th className={styles.right}>Impayé</th><th className={styles.right}>Payé en retard</th>
              <th>Retard</th><th className={styles.right}>Amende indic.</th><th>Complétude</th><th></th>
            </tr></thead>
            <tbody>
              {loading && <tr><td colSpan={12} className={styles.empty}>Chargement…</td></tr>}
              {!loading && rows.length === 0 && <tr><td colSpan={12} className={styles.empty}>Aucune facture fournisseur en retard sur cette période.</td></tr>}
              {!loading && rows.map(r => (
                <tr key={r.facture_id}>
                  <td><strong>{r.reference_facture || '—'}</strong><small>{r.numero_interne || ''}</small></td>
                  <td><strong>{r.fournisseur}</strong><small>{r.fournisseur_ice ? `ICE ${r.fournisseur_ice}` : 'ICE manquant'}</small></td>
                  <td>{dateFR(r.date_facture)}</td><td>{dateFR(r.date_livraison_service)}</td><td>{dateFR(r.date_echeance)}</td>
                  <td className={styles.right}>{mad(r.montant_ttc)}</td><td className={styles.right}>{mad(r.montant_non_paye_fin_periode)}</td>
                  <td className={styles.right}>{mad(r.montant_paye_hors_delai_periode)}</td><td>{r.mois_retard_max} mois</td>
                  <td className={styles.right}>{mad(r.amende_indicative)}</td>
                  <td>{r.completude?.complete ? <Badge tone="green">OK</Badge> : <Badge tone="orange">À compléter</Badge>}</td>
                  <td><button className={styles.iconBtn} title="Compléter" onClick={() => setEdit(r)}><i className="ti ti-edit" /><span className="libelle-action" aria-hidden="true">Compléter</span></button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {edit && <MetaModal ligne={edit} onClose={() => setEdit(null)} onSaved={load} />}
    </div>
  )
}
