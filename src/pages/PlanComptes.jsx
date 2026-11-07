import { useEffect, useMemo, useState } from 'react'
import { CLASSES, TYPES_COMPTE } from '../data/planComptes.js'
import { enregistrerPlanSociete, notifierPlanModifie } from '../data/planComptableCache.js'
import { API_BASE, estAdmin, getToken, planComptableAPI, formatErreurAPI } from '../services/api.js'
import styles from './PlanComptes.module.css'
import { notifier } from '../services/notifications.js'

const COULEURS_CLASSE = {
  1: { bg: '#E6F1FB', color: '#185FA5', border: '#B5D4F4' },
  2: { bg: '#EAF3DE', color: '#3B6D11', border: '#C2DFA0' },
  3: { bg: '#FAEEDA', color: '#854F0B', border: '#F2D49A' },
  4: { bg: '#FCEBEB', color: '#A32D2D', border: '#F5BEBE' },
  5: { bg: '#EEEDFE', color: '#534AB7', border: '#C8C6F9' },
  6: { bg: '#FEF0E6', color: '#8B3A12', border: '#F8CCAB' },
  7: { bg: '#E6FAF0', color: '#0F6E56', border: '#A0DFC4' },
  8: { bg: '#F5F0FE', color: '#6D3BB7', border: '#D4C2F9' },
  9: { bg: '#FDF2F8', color: '#9D2463', border: '#F5C0DC' },
  0: { bg: '#F0F0EF', color: '#5A5955', border: '#D5D4D0' },
}

const COULEURS_TYPE = {
  CP: { bg: '#E6F1FB', color: '#185FA5' }, DE: { bg: '#FCEBEB', color: '#A32D2D' },
  PR: { bg: '#FAEEDA', color: '#854F0B' }, AI: { bg: '#EAF3DE', color: '#3B6D11' },
  AM: { bg: '#F0EFED', color: '#5A5955' }, ST: { bg: '#FAEEDA', color: '#854F0B' },
  AC: { bg: '#E6F1FB', color: '#185FA5' }, PC: { bg: '#FCEBEB', color: '#A32D2D' },
  TR: { bg: '#EEEDFE', color: '#534AB7' }, CH: { bg: '#FEF0E6', color: '#8B3A12' },
  PD: { bg: '#E6FAF0', color: '#0F6E56' }, RE: { bg: '#F5F0FE', color: '#6D3BB7' },
  DI: { bg: '#F0EFED', color: '#5A5955' }, AN: { bg: '#FDF2F8', color: '#9D2463' },
  SP: { bg: '#F0F0EF', color: '#5A5955' },
}

export default function PlanComptes() {
  const [comptes, setComptes] = useState([])
  const [recherche, setRecherche] = useState('')
  const [filtreClasse, setFiltreClasse] = useState('TOUTES')
  const [filtreEtat, setFiltreEtat] = useState('actifs')
  const [chargement, setChargement] = useState(true)
  const [erreur, setErreur] = useState('')
  const [preparation, setPreparation] = useState(false)
  const admin = estAdmin()

  async function charger() {
    setChargement(true); setErreur('')
    try {
      const rows = await planComptableAPI.lister(true)
      setComptes(rows || [])
      const { cle, modifie } = enregistrerPlanSociete(rows, getToken())
      if (modifie) notifierPlanModifie(cle)
    } catch (e) { setErreur(e.message || 'Impossible de charger le plan comptable.') }
    finally { setChargement(false) }
  }
  useEffect(() => { charger() }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const comptesFiltres = useMemo(() => comptes.filter(c => {
    if (filtreClasse !== 'TOUTES' && Number(c.classe) !== Number(filtreClasse)) return false
    if (filtreEtat === 'actifs' && !c.actif) return false
    if (filtreEtat === 'inactifs' && c.actif) return false
    if (recherche) {
      const q = recherche.toLowerCase().trim()
      if (!String(c.compte || c.numero).startsWith(q) && !String(c.libelle || '').toLowerCase().includes(q)) return false
    }
    return true
  }), [comptes, recherche, filtreClasse, filtreEtat])

  const stats = useMemo(() => {
    const s = {}; for (let i = 0; i <= 9; i++) s[i] = comptes.filter(c => Number(c.classe) === i && c.actif).length
    return s
  }, [comptes])

  async function ajouter() {
    const numero = window.prompt('Numéro de la nouvelle subdivision (5 à 10 chiffres) :')?.trim()
    if (!numero) return
    const libelle = window.prompt(`Libellé du compte ${numero} :`)?.trim()
    if (!libelle) return
    try { await planComptableAPI.creer({ numero, libelle }); await charger() }
    catch (e) { notifier.erreur(e.message) }
  }

  async function renommer(c) {
    const libelle = window.prompt(`Nouveau libellé de ${c.compte} :`, c.libelle)?.trim()
    if (!libelle || libelle === c.libelle) return
    try { await planComptableAPI.modifier(c.compte, { libelle }); await charger() }
    catch (e) { notifier.erreur(e.message) }
  }

  async function basculer(c) {
    if (!confirm(`${c.actif ? 'Désactiver' : 'Réactiver'} le compte ${c.compte} — ${c.libelle} ?`)) return
    try { await planComptableAPI.modifier(c.compte, { actif: !c.actif }); await charger() }
    catch (e) { notifier.erreur(e.message) }
  }

  async function supprimer(c) {
    if (!confirm(`Supprimer définitivement la subdivision ${c.compte} ?`)) return
    try { await planComptableAPI.supprimer(c.compte); await charger() }
    catch (e) { notifier.erreur(e.message) }
  }

  async function initialiser() {
    setPreparation(true); setErreur('')
    try {
      const response = await fetch(`${API_BASE}/api/plan-comptable/initialiser`, {
        method: 'POST', headers: { Authorization: `Bearer ${getToken()}` },
      })
      const data = await response.json().catch(() => ({}))
      if (!response.ok) throw new Error(formatErreurAPI(data.detail))
      await charger()
    } catch (error) { setErreur(error.message) }
    finally { setPreparation(false) }
  }

  const actifs = comptes.filter(c => c.actif).length
  const personnalises = comptes.filter(c => c.origine === 'personnalise').length

  return (
    <div className={styles.page} data-form-page>
      <div className={styles.topbar}>
        <h1 className={styles.pageTitle}>Plan comptable de la société</h1>
        <div className={styles.topbarRight}>
          <div className={styles.compteurTotal}>{actifs} actifs · {personnalises} personnalisés</div>
          {admin && <button className={styles.classeBtn} onClick={ajouter}><i className="ti ti-plus" /> Ajouter une subdivision</button>}
          {admin && <button className={styles.classeBtn} disabled={preparation || chargement} onClick={initialiser}>Compléter le plan CGNC</button>}
        </div>
      </div>

      <div className={styles.content}>
        <div className={styles.filtres}>
          <div className={styles.recherche}>
            <i className="ti ti-search" aria-hidden="true" />
            <input type="text" placeholder="Rechercher par numéro ou libellé..." value={recherche}
              onChange={e => setRecherche(e.target.value)} className={styles.inputRecherche} />
            {recherche && <button className={styles.clearBtn} onClick={() => setRecherche('')}><i className="ti ti-x" /></button>}
          </div>
          <div className={styles.classesBarre}>
            <button className={`${styles.classeBtn} ${filtreClasse === 'TOUTES' ? styles.classeBtnActif : ''}`} onClick={() => setFiltreClasse('TOUTES')}>Toutes les classes</button>
            {Object.entries(CLASSES).sort(([a], [b]) => (a === '0' ? 10 : Number(a)) - (b === '0' ? 10 : Number(b))).map(([num, label]) => {
              const c = COULEURS_CLASSE[num]
              return <button key={num} className={`${styles.classeBtn} ${filtreClasse === num ? styles.classeBtnActif : ''}`}
                style={filtreClasse === num ? { background: c.bg, color: c.color, borderColor: c.border } : {}}
                onClick={() => setFiltreClasse(filtreClasse === num ? 'TOUTES' : num)}>
                <span className={styles.classeNum}>Cl. {num}</span><span className={styles.classeLabel}>{label}</span><span className={styles.classeCount}>{stats[num] || 0}</span>
              </button>
            })}
            {['actifs', 'inactifs', 'tous'].map(v => <button key={v} className={`${styles.classeBtn} ${filtreEtat === v ? styles.classeBtnActif : ''}`} onClick={() => setFiltreEtat(v)}>{v === 'actifs' ? 'Actifs' : v === 'inactifs' ? 'Inactifs' : 'Tous'}</button>)}
          </div>
        </div>

        <div className={styles.resultatsInfo}>{chargement ? 'Chargement…' : `${comptesFiltres.length} compte(s)`}{erreur && <span style={{ color: 'var(--red)', marginLeft: 10 }}>{erreur}</span>}</div>
        <div className={styles.card}>
          <div className={styles.tableWrapper}>
            <table className={styles.table}>
              <thead><tr><th>N° compte</th><th>Libellé</th><th>Classe</th><th>Type</th><th>Origine</th><th>État</th><th>Usage</th>{admin && <th>Actions</th>}</tr></thead>
              <tbody>{comptesFiltres.map(c => {
                const cc = COULEURS_CLASSE[c.classe] || COULEURS_CLASSE[0]
                const ct = COULEURS_TYPE[c.type || c.type_compte] || COULEURS_TYPE.SP
                return <tr key={c.compte} style={!c.actif ? { opacity: .55 } : undefined}>
                  <td><span className={styles.numBadge} style={{ background: cc.bg, color: cc.color }}>{c.compte}</span></td>
                  <td><span className={styles.libelleCell}>{c.libelle}</span></td>
                  <td><span className={styles.classeBadge} style={{ background: cc.bg, color: cc.color, borderColor: cc.border }}>{c.classe} — {CLASSES[c.classe]}</span></td>
                  <td><span className={styles.typeBadge} style={{ background: ct.bg, color: ct.color }}>{TYPES_COMPTE[c.type || c.type_compte] || c.type || '—'}</span></td>
                  <td>{c.origine === 'cgnc' ? 'CGNC' : c.origine === 'personnalise' ? 'Personnalisé' : 'Historique'}</td>
                  <td>{c.actif ? 'Actif' : 'Inactif'}</td><td>{c.nb_ecritures || 0}</td>
                  {admin && <td style={{ whiteSpace: 'nowrap' }}>
                    <button className={styles.clearBtn} onClick={() => renommer(c)}>Renommer</button>{' '}
                    <button className={styles.clearBtn} onClick={() => basculer(c)}>{c.actif ? 'Désactiver' : 'Réactiver'}</button>{' '}
                    {c.origine === 'personnalise' && !c.nb_ecritures && <button className={styles.clearBtn} onClick={() => supprimer(c)}>Supprimer</button>}
                  </td>}
                </tr>
              })}</tbody>
            </table>
            {!chargement && !comptesFiltres.length && <div className={styles.vide}><i className="ti ti-search-off" /><span>Aucun compte trouvé</span></div>}
          </div>
        </div>
      </div>
    </div>
  )
}
