import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { dashboardAPI } from '../services/api.js'
import { formatMAD } from '../data/donnees.js'
import styles from './DashboardCommercial.module.css'

const MOIS = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Août', 'Sep', 'Oct', 'Nov', 'Déc']
const connu = value => typeof value === 'number' && Number.isFinite(value)
const montantOuDiagnostic = value => connu(value) ? `${formatMAD(value)} MAD` : 'À vérifier'

function Montant({ value }) {
  return <>{connu(value) ? <>{formatMAD(value)}<span className={styles.devise}> MAD</span></> : 'À vérifier'}</>
}

function Kpi({ icon, label, value, suffix = 'MAD', detail, tone = 'blue', onClick }) {
  return (
    <button type="button" className={`${styles.kpi} ${styles[`tone_${tone}`]}`} onClick={onClick} disabled={!onClick}>
      <div className={styles.kpiTop}><span className={styles.kpiIcon}><i className={`ti ${icon}`} /></span><span>{label}</span></div>
      <div className={styles.kpiValue}>{connu(value) ? <>{suffix === '%' ? value.toFixed(1) : formatMAD(value)}<small>{suffix === '%' ? ' %' : ' MAD'}</small></> : 'À vérifier'}</div>
      {detail && <div className={styles.kpiDetail}>{detail}</div>}
    </button>
  )
}

function BarChart({ data }) {
  const max = Math.max(1, ...data.flatMap(x => [Number(x.ventes_ht || 0), Number(x.achats_ht || 0)]))
  return (
    <div className={styles.chart}>
      <div className={styles.legend}><span><i className={styles.dotVentes} />Ventes HT</span><span><i className={styles.dotAchats} />Achats HT</span></div>
      <div className={styles.chartBars}>
        {data.map((x, idx) => (
          <div className={styles.month} key={x.mois} title={`${MOIS[idx]} — Ventes ${formatMAD(x.ventes_ht)} MAD · Achats ${formatMAD(x.achats_ht)} MAD`}>
            <div className={styles.barSlot}>
              <i className={styles.barVentes} style={{ height: `${Math.max(2, Number(x.ventes_ht || 0) / max * 100)}%` }} />
              <i className={styles.barAchats} style={{ height: `${Math.max(2, Number(x.achats_ht || 0) / max * 100)}%` }} />
            </div>
            <span>{MOIS[idx]}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function Ranking({ title, subtitle, rows, valueKey, valueLabel, onOpen, empty = 'Aucune donnée' }) {
  const max = Math.max(1, ...rows.map(x => Number(x[valueKey] || 0)))
  return (
    <div className={styles.card}>
      <div className={styles.cardHeader}><div><strong>{title}</strong><span>{subtitle}</span></div>{onOpen && <button onClick={onOpen}>Voir tout →</button>}</div>
      <div className={styles.ranking}>
        {!rows.length && <div className={styles.empty}>{empty}</div>}
        {rows.slice(0, 6).map((row, i) => (
          <div className={styles.rankRow} key={row.tiers_id ?? row.article_id ?? `${row.tiers}-${i}`}>
            <span className={styles.rankIndex}>{i + 1}</span>
            <div className={styles.rankMain}>
              <div className={styles.rankLine}><strong>{row.tiers || row.designation}</strong><span>{formatMAD(row[valueKey])} MAD</span></div>
              <div className={styles.miniBar}><i style={{ width: `${Number(row[valueKey] || 0) / max * 100}%` }} /></div>
              <div className={styles.rankMeta}>{valueLabel(row)}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default function DashboardCommercial({ exercice }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    let alive = true
    setLoading(true); setError('')
    dashboardAPI.commercial(exercice)
      .then(d => { if (alive) setData(d) })
      .catch(e => { if (alive) setError(e.message || 'Impossible de charger le pilotage commercial') })
      .finally(() => { if (alive) setLoading(false) })
    return () => { alive = false }
  }, [exercice])

  const maxMonth = useMemo(() => {
    if (!data?.mensuel?.length) return null
    return data.mensuel.reduce((best, x) => Number(x.ventes_ht || 0) > Number(best.ventes_ht || 0) ? x : best, data.mensuel[0])
  }, [data])

  if (loading) return <div className={styles.loading}>Chargement du pilotage commercial…</div>
  if (error) return <div className={styles.error}><i className="ti ti-alert-circle" />{error}</div>
  if (!data) return null

  const r = data.resume
  const pipeline = data.pipeline
  return (
    <section className={styles.section}>
      <div className={styles.sectionHead}>
        <div><h2>Pilotage commercial</h2><p>Ventes, achats, marge, encours et performance — exercice {exercice}</p></div>
        <button className={styles.linkBtn} onClick={() => navigate('/situation')}>Situation financière →</button>
      </div>
      {(r.calcul_incomplet_clients || r.calcul_incomplet_fournisseurs) && <div role="alert" className={styles.method}>
        Encours incomplets : {r.calcul_incomplet_clients ? 'clients à vérifier. ' : ''}{r.calcul_incomplet_fournisseurs ? 'fournisseurs à vérifier. ' : ''}
        {(data.diagnostics_ras || []).map(d => <div key={d.id}>{d.numero || `Facture #${d.id}`} : {d.ras_anomalie}</div>)}
      </div>}

      <div className={styles.kpis}>
        <Kpi icon="ti-trending-up" label="Chiffre d’affaires HT" value={r.ca_ht} detail={`${r.nb_factures_vente} facture${r.nb_factures_vente > 1 ? 's' : ''} client`} tone="green" onClick={() => navigate('/factures')} />
        <Kpi icon="ti-shopping-cart" label="Achats HT" value={r.achats_ht} detail={`${r.nb_factures_achat} facture${r.nb_factures_achat > 1 ? 's' : ''} fournisseur`} tone="amber" onClick={() => navigate('/factures')} />
        <Kpi icon="ti-chart-dots-3" label="Marge commerciale estimée" value={r.marge_estimee} detail={`${Number(r.taux_marge_estime || 0).toFixed(1)} % du CA HT`} tone={r.marge_estimee >= 0 ? 'blue' : 'red'} />
        <Kpi icon="ti-receipt" label="Panier moyen HT" value={r.panier_moyen_ht} detail={maxMonth ? `Meilleur mois : ${MOIS[(maxMonth.mois || 1) - 1]}` : '—'} tone="purple" />
      </div>

      <div className={styles.kpisSecondary}>
        <Kpi icon="ti-wallet" label="Encours clients" value={r.encours_clients} detail={`${montantOuDiagnostic(r.retard_clients)} en retard`} tone={r.retard_clients > 0 ? 'red' : 'blue'} onClick={() => navigate('/situation')} />
        <Kpi icon="ti-building-bank" label="Encours fournisseurs" value={r.encours_fournisseurs} detail={`${montantOuDiagnostic(r.retard_fournisseurs)} en retard`} tone="amber" onClick={() => navigate('/situation')} />
        <Kpi icon="ti-circle-percentage" label="Taux de recouvrement" value={r.taux_recouvrement_clients} suffix="%" detail={connu(r.nb_clients_en_retard) ? `${r.nb_clients_en_retard} facture${r.nb_clients_en_retard > 1 ? 's' : ''} client en retard` : 'Nombre de factures en retard à vérifier'} tone="green" onClick={() => navigate('/situation')} />
        <Kpi icon="ti-file-check" label="Conversion devis" value={pipeline.taux_conversion} suffix="%" detail={`${pipeline.nb_convertis}/${pipeline.nb_devis} devis transformés`} tone="blue" onClick={() => navigate('/commercial')} />
      </div>

      <div className={styles.gridMain}>
        <div className={styles.card}>
          <div className={styles.cardHeader}><div><strong>Évolution mensuelle</strong><span>Ventes HT vs achats HT</span></div></div>
          <BarChart data={data.mensuel || []} />
        </div>
        <div className={styles.card}>
          <div className={styles.cardHeader}><div><strong>Pipeline devis</strong><span>Transformation commerciale de l’exercice</span></div><button onClick={() => navigate('/commercial')}>Cycle commercial →</button></div>
          <div className={styles.pipeline}>
            <div><span>Devis émis</span><strong>{pipeline.nb_devis}</strong><small><Montant value={pipeline.valeur_devis_ht} /></small></div>
            <i className="ti ti-arrow-right" />
            <div><span>Transformés</span><strong>{pipeline.nb_convertis}</strong><small><Montant value={pipeline.valeur_convertie_ht} /></small></div>
            <div className={styles.pipelineRate}><strong>{Number(pipeline.taux_conversion || 0).toFixed(1)}%</strong><span>taux de conversion</span></div>
          </div>
          <div className={styles.method}><i className="ti ti-info-circle" />{data.methodologie?.marge}</div>
        </div>
      </div>

      <div className={styles.gridRank}>
        <Ranking title="Top clients" subtitle="CA net HT, avoirs déduits" rows={data.top_clients || []} valueKey="ca_ht"
          valueLabel={x => `${x.nb_factures} facture${x.nb_factures > 1 ? 's' : ''} · Encours ${montantOuDiagnostic(x.encours)}${x.retard_max ? ` · ${x.retard_max} j max` : ''}${x.encours_anomalie ? ` · ${x.encours_anomalie}` : ''}`}
          onOpen={() => navigate('/tiers')} />
        <Ranking title="Top fournisseurs" subtitle="Achats net HT, avoirs déduits" rows={data.top_fournisseurs || []} valueKey="achats_ht"
          valueLabel={x => `${x.nb_factures} facture${x.nb_factures > 1 ? 's' : ''} · Encours ${montantOuDiagnostic(x.encours)}${x.encours_anomalie ? ` · ${x.encours_anomalie}` : ''}`}
          onOpen={() => navigate('/tiers')} />
        <Ranking title="Top articles / services" subtitle="Contribution au CA net HT" rows={data.top_articles || []} valueKey="ca_ht"
          valueLabel={x => `${formatMAD(x.quantite)} vendu · ${Number(x.part_ca || 0).toFixed(1)} % du CA · marge est. ${formatMAD(x.marge_estimee)} MAD`}
          onOpen={() => navigate('/articles')} />
      </div>
    </section>
  )
}
