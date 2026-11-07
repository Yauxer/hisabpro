import { useEffect, useRef, useState } from 'react'
import { etatsAPI, getToken } from '../services/api.js'
import { formatMAD } from '../data/donnees.js'
import styles from './BalancePreparationDetail.module.css'

const montant = value => value == null ? 'Indisponible' : formatMAD(value)
const TAILLE_PAGE = 50

export default function BalancePreparationDetail({ dossier }) {
  const [ouvert, setOuvert] = useState(false)
  const [lecture, setLecture] = useState(null)
  const [essai, setEssai] = useState(0)
  const [cote, setCote] = useState('actif')
  const [periode, setPeriode] = useState('n')
  const [filtre, setFiltre] = useState('')
  const [page, setPage] = useState(0)
  const generation = useRef(0)
  const token = getToken()
  const cle = JSON.stringify([dossier.id, dossier.empreinte_sha256, token])

  useEffect(() => {
    const numero = ++generation.current
    setLecture(null)
    setCote('actif'); setPeriode('n'); setFiltre(''); setPage(0)
    if (!ouvert) return () => { generation.current += 1 }
    etatsAPI.preparationBalanceDetail(dossier.id).then(data => {
      if (numero !== generation.current || token !== getToken()) return
      if (data.id !== dossier.id || data.empreinte_sha256 !== dossier.empreinte_sha256) {
        throw new Error('La version reçue ne correspond pas à la préparation sélectionnée. Rouvrez cette version.')
      }
      setLecture({ cle, data })
    }).catch(e => {
      if (numero === generation.current && token === getToken()) setLecture({ cle, erreur: e.message })
    })
    return () => { generation.current += 1 }
  }, [cle, ouvert, essai])

  const courant = lecture?.cle === cle ? lecture : null
  const data = courant?.data
  const source = data?.balances[periode]
  const comptes = (source || []).filter(r => r.compte.includes(filtre.trim()))
  const nbPages = Math.max(1, Math.ceil(comptes.length / TAILLE_PAGE))
  const lignes = comptes.slice(page * TAILLE_PAGE, (page + 1) * TAILLE_PAGE)
  const changerFiltre = value => { setFiltre(value); setPage(0) }

  return <section className={styles.detail} aria-label="Détail de la préparation conservée">
    <button type="button" className={styles.bouton} aria-expanded={ouvert} onClick={() => setOuvert(!ouvert)}>
      {ouvert ? 'Masquer le bilan et les comptes sources' : 'Consulter le bilan et les comptes sources'}
    </button>
    {ouvert && <>
      {!courant && <p role="status">Chargement de la version conservée…</p>}
      {courant?.erreur && <div role="alert" className={styles.erreur}>
        <p>{courant.erreur}</p>
        <button type="button" className={styles.bouton} onClick={() => setEssai(v => v + 1)}>Réessayer le détail</button>
      </div>}
      {data && <>
        <h3>Bilan de la version {data.version}</h3>
        <p>{data.note}</p>
        <label className={styles.champ}>Côté du bilan
          <select aria-label="Côté du bilan" value={cote} onChange={e => setCote(e.target.value)}><option value="actif">Actif</option><option value="passif">Passif</option></select>
        </label>
        <div className={styles.tableWrap} tabIndex={0} role="region" aria-label="Bilan détaillé de la préparation">
          <table className={styles.bilan}>
            <thead><tr><th scope="col">Rubrique</th>{(cote === 'actif'
              ? ['Brut N MAD', 'Amort. / prov. N MAD', 'Net N MAD', 'Net N-1 MAD']
              : ['N MAD', 'N-1 MAD']).map(label => <th scope="col" key={label}>{label}</th>)}</tr></thead>
            <tbody>{data.bilan[cote].map((r, i) => <tr key={i} className={r.type === 'total' || r.type === 'titre' ? styles.total : r.type === 'detail' ? styles.memoire : ''}>
              <th scope="row">{r.type === 'detail' ? 'Pour mémoire · ' : ''}{r.numero ? r.numero + ' · ' : ''}{r.label}</th>
              {r.valeurs.length ? r.valeurs.map((v, j) => <td key={j}>{montant(v)}</td>) : <td colSpan={cote === 'actif' ? 4 : 2} />}
            </tr>)}</tbody>
          </table>
        </div>
        <h3>Comptes sources normalisés</h3>
        <p>Comptes et montants conservés à l’import. Les intitulés non conservés ne sont pas reconstitués depuis le plan courant.</p>
        <div className={styles.outils}>
          <label className={styles.champ}>Balance source
            <select aria-label="Balance source" value={periode} onChange={e => { setPeriode(e.target.value); setPage(0); setFiltre('') }}>
              <option value="n">N</option><option value="n1">N-1</option>
            </select>
          </label>
          <label className={styles.champ}>Rechercher un compte source
            <input aria-label="Rechercher un compte source" value={filtre} onChange={e => changerFiltre(e.target.value)} placeholder="Ex. 232" />
          </label>
        </div>
        {source == null ? <p>Balance source {periode === 'n' ? 'N' : 'N-1'} indisponible dans cette version.</p> : <>
          <p>{comptes.length} compte(s) affichable(s) sur {source.length} conservé(s).</p>
          {comptes.length === 0 ? <p>Aucun compte ne correspond à cette recherche.</p> : <>
            <div className={styles.tableWrap} tabIndex={0} role="region" aria-label="Comptes sources de la préparation">
              <table className={styles.sources}>
                <thead><tr><th scope="col">Compte</th><th scope="col">Débit MAD</th><th scope="col">Crédit MAD</th></tr></thead>
                <tbody>{lignes.map(r => <tr key={r.compte}><th scope="row">{r.compte}</th><td>{montant(r.debit)}</td><td>{montant(r.credit)}</td></tr>)}</tbody>
              </table>
            </div>
            <nav aria-label="Pages des comptes sources" className={styles.outils}>
              <button type="button" className={styles.bouton} disabled={page === 0} onClick={() => setPage(v => v - 1)}>Comptes précédents</button>
              <span>Page {page + 1} sur {nbPages}</span>
              <button type="button" className={styles.bouton} disabled={page + 1 >= nbPages} onClick={() => setPage(v => v + 1)}>Comptes suivants</button>
            </nav>
          </>}
        </>}
      </>}
    </>}
  </section>
}
