import { useState, useEffect, useRef } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { useModules } from '../data/ModulesContext.jsx'
import { usePersonnelAcces } from '../data/PersonnelAccesContext.jsx'
import { authAPI, getRole, LIBELLE_ROLE } from '../services/api.js'
import styles from './Sidebar.module.css'

const MODULES = [
  {
    id:    'facturation',
    label: 'Facturation',
    icon:  'ti-file-invoice',
    couleur: '#185FA5',
    items: [
      { to: '/commercial', icon: 'ti-git-merge',   label: 'Cycle commercial' },
      { to: '/situation', icon: 'ti-chart-pie',    label: 'Situation financière' },
      { to: '/factures', icon: 'ti-file-invoice',  label: 'Factures' },
      { to: '/avoirs',   icon: 'ti-receipt-refund', label: 'Avoirs' },
      { to: '/acomptes', icon: 'ti-coins',          label: 'Acomptes' },
      { to: '/effets',   icon: 'ti-wallet',         label: 'Effets & Chèques' },
      { to: '/delais-paiement', icon: 'ti-clock-dollar', label: 'Délais de paiement' },
      { to: '/tiers',    icon: 'ti-users',          label: 'Clients / Fournisseurs' },
      { to: '/articles', icon: 'ti-package',        label: 'Articles' },
      { to: '/inventaire', icon: 'ti-clipboard-list', label: 'Inventaire & stock' },
    ],
  },
  {
    id:    'comptabilite',
    label: 'Comptabilité',
    icon:  'ti-calculator',
    couleur: '#3B6D11',
    items: [
      { to: '/journal',         icon: 'ti-book',         label: 'Journal' },
      { to: '/plan-comptes',    icon: 'ti-list-tree',    label: 'Plan de comptes' },
      { to: '/declaration-tva', icon: 'ti-percentage',   label: 'Déclaration TVA' },
      { to: '/fiscalite-is',    icon: 'ti-receipt-tax',  label: 'Résultat fiscal / IS' },
      { to: '/liasse-fiscale',  icon: 'ti-report',       label: 'Liasse fiscale' },
      { to: '/grand-livre',     icon: 'ti-table',        label: 'Grand livre' },
      { to: '/rapprochement',   icon: 'ti-scale',        label: 'Rapprochement bancaire' },
      { to: '/lettrage',          icon: 'ti-link',         label: 'Lettrage' },
      { to: '/balances',          icon: 'ti-report-analytics', label: 'Balances' },
      { to: '/immobilisations',    icon: 'ti-building-factory',  label: 'Immobilisations' },
      { to: '/cloture',            icon: 'ti-lock',             label: 'Clôture d\'exercice' },
      { to: '/livre-inventaire',   icon: 'ti-book-2',           label: 'Livre d\'inventaire' },
    ],
  },
  {
    id:    'paie_grh',
    label: 'Personnel & Paie',
    icon:  'ti-users-group',
    couleur: '#854F0B',
    items: [
      { to: '/personnel-paie/paie-du-mois', icon: 'ti-list-check', label: 'Paie du mois' },
      { to: '/personnel-paie/personnel', icon: 'ti-users', label: 'Personnel' },
      { to:'/personnel-paie/elements', icon:'ti-list-details', label:'Éléments de paie' },
      { to:'/personnel-paie/traitement', icon:'ti-calculator', label:'Traitement de la paie' },
      { to:'/personnel-paie/charges-sociales', icon:'ti-building-community', label:'Charges sociales' },
      { to:'/personnel-paie/fiscalite', icon:'ti-receipt-tax', label:'Fiscalité salariale' },
      { to:'/personnel-paie/bulletins', icon:'ti-file-invoice', label:'Bulletins de paie' },
      { to:'/personnel-paie/avances', icon:'ti-coins', label:'Avances & prêts' },
      { to:'/personnel-paie/paiements', icon:'ti-wallet', label:'Paiements' },
      { to:'/personnel-paie/comptabilisation', icon:'ti-book', label:'Comptabilisation' },
      { to:'/personnel-paie/etats', icon:'ti-report', label:'États & reporting' },
    ],
  },
]

export default function Sidebar({ mobileOuvert = false, onFermer }) {
  const navigation = useRef(null)
  useEffect(() => {
    if (!mobileOuvert || !navigation.current) return
    const panneau = navigation.current
    const controles = () => [...panneau.querySelectorAll('a[href], button:not([disabled])')]
      .filter(el => el.getClientRects().length && getComputedStyle(el).visibility !== 'hidden')
    controles()[0]?.focus()
    function clavier(e) {
      if (e.key === 'Escape') { e.preventDefault(); onFermer?.(); return }
      if (e.key !== 'Tab') return
      const liste = controles(), premier = liste[0], dernier = liste.at(-1)
      if (e.shiftKey && document.activeElement === premier) { e.preventDefault(); dernier?.focus() }
      else if (!e.shiftKey && document.activeElement === dernier) { e.preventDefault(); premier?.focus() }
    }
    panneau.addEventListener('keydown', clavier)
    return () => panneau.removeEventListener('keydown', clavier)
  }, [mobileOuvert, onFermer])
  const { societe, modules, aComptabilite, aFacturation, aGRH } = useModules()
  const personnel=usePersonnelAcces()
  const personnelSeul=personnel?.user?.role==='personnel'||getRole()==='personnel'
  const location = useLocation()

  // Détermine quel module est ouvert par défaut selon la page courante
  function moduleParDefaut() {
    const path = location.pathname
    if (['/commercial','/situation','/factures','/avoirs','/acomptes','/effets','/delais-paiement','/tiers','/articles','/inventaire'].some(p => path.startsWith(p))) return 'facturation'
    if (['/journal','/plan-comptes','/declaration-tva','/fiscalite-is','/liasse-fiscale','/grand-livre','/bilan','/cpc','/etic','/rapprochement','/lettrage','/balances','/immobilisations','/cloture','/livre-inventaire'].some(p => path.startsWith(p))) return 'comptabilite'
    if (['/cnss','/personnel-paie'].some(p => path.startsWith(p))) return 'paie_grh'
    return null
  }

  const [ouvert, setOuvert] = useState(moduleParDefaut)
  useEffect(()=>{const id=moduleParDefaut();if(id)setOuvert(id)},[location.pathname])

  function toggle(id) {
    setOuvert(prev => prev === id ? null : id)
  }

  function moduleEstActif(id) {
    if (id === 'facturation')  return aFacturation
    if (id === 'comptabilite') return aComptabilite
    if (id === 'paie_grh')     return aGRH
    return false
  }

  return (
    <aside id="navigation-principale" ref={navigation} aria-label="Navigation principale"
      className={`${styles.sidebar} ${mobileOuvert ? styles.mobileOuvert : ''}`}>
      <button type="button" className={styles.fermerMobile} aria-label="Fermer le menu" onClick={onFermer}>
        <i className="ti ti-x" aria-hidden="true" />
      </button>
      <div className={styles.logo}>
        <span className={styles.logoName}>HisabPro</span>
        <span className={styles.logoSub}>
          {societe?.raison_sociale || 'Comptabilité Marocaine'}
        </span>
      </div>

      <nav className={styles.nav}>
        {/* Dashboard — toujours visible */}
        {!personnelSeul&&<NavLink to="/dashboard" onClick={onFermer}
          className={({ isActive }) => [styles.navItem, isActive ? styles.active : ''].join(' ')}>
          <i className="ti ti-layout-dashboard" aria-hidden="true" />
          <span>Tableau de bord</span>
        </NavLink>}

        {/* Modules déroulants */}
        {MODULES.map(mod => {
          const actif   = moduleEstActif(mod.id)
          const estOuvert = ouvert === mod.id
          const aUneLigneActive = mod.id==='paie_grh' ? location.pathname.startsWith('/personnel-paie') || location.pathname==='/cnss'
            : mod.items.some(item => item.to && location.pathname.startsWith(item.to))

          if (!actif || personnelSeul&&mod.id!=='paie_grh') return null

          return (
            <div key={mod.id} className={styles.moduleGroupe}>
              {/* En-tête du module — cliquable */}
              <button
                aria-expanded={estOuvert} aria-controls={`menu-${mod.id}`}
                className={`${styles.moduleHeader} ${aUneLigneActive ? styles.moduleHeaderActif : ''}`}
                style={aUneLigneActive ? { '--mod-color': mod.couleur } : {}}
                onClick={() => toggle(mod.id)}
              >
                <div className={styles.moduleHeaderLeft}>
                  <i className={`ti ${mod.icon}`} aria-hidden="true"
                    style={{ color: aUneLigneActive || estOuvert ? mod.couleur : 'var(--text-tertiary)' }} />
                  <span style={{ color: aUneLigneActive || estOuvert ? mod.couleur : 'var(--text-secondary)' }}>
                    {mod.label}
                  </span>
                </div>
                <i
                  className={`ti ${estOuvert ? 'ti-chevron-down' : 'ti-chevron-right'}`}
                  style={{
                    fontSize: 12,
                    color: 'var(--text-tertiary)',
                    transition: 'transform 0.2s',
                  }}
                  aria-hidden="true"
                />
              </button>

              {/* Sous-menu déroulant */}
              <div id={`menu-${mod.id}`} className={`${styles.sousMenu} ${estOuvert ? styles.sousMenuOuvert : ''}`}>
                {mod.items.map(item => item.avenir ? <div key={item.code} aria-disabled="true" className={`${styles.sousMenuItem} ${styles.aVenir}`}>
                  <i className={`ti ${item.icon}`} aria-hidden="true" /><span>{item.label}</span><small>À venir</small>
                </div> : mod.id==='paie_grh' && (personnel?.chargement || !personnel?.acces ||
                    personnel.acces.mode==='protege' && !personnel.acces.capacites.includes('personnel.lire_identite') && !personnel.acces.peut_gerer_habilitations)
                  ? <div key={item.to} aria-disabled="true" className={`${styles.sousMenuItem} ${styles.aVenir}`}><i className={`ti ${item.icon}`} aria-hidden="true"/><span>{item.label}</span><small>Accès restreint</small></div> : (
                  <NavLink
                    key={item.to}
                    to={item.to} onClick={onFermer}
                    className={({ isActive }) =>
                      [styles.sousMenuItem, isActive ? styles.sousMenuItemActif : ''].join(' ')
                    }
                    style={({ isActive }) => isActive ? { '--mod-color': mod.couleur } : {}}
                  >
                    <i className={`ti ${item.icon}`} aria-hidden="true" />
                    <span>{item.label}</span>
                  </NavLink>
                ))}
                {mod.id==='paie_grh' && !personnelSeul && <NavLink to="/cnss" onClick={onFermer} className={styles.sousMenuItem}>Espace historique Paie & GRH</NavLink>}
              </div>
            </div>
          )
        })}
      </nav>

      <div className={styles.footer}>
        {!personnelSeul&&<NavLink to="/parametres" onClick={onFermer}
          className={({ isActive }) => [styles.navItem, isActive ? styles.active : ''].join(' ')}>
          <i className="ti ti-settings" aria-hidden="true" />
          <span>Paramètres</span>
        </NavLink>}
        {getRole() === 'lecture' && (
          <div style={{ margin: '4px 10px 6px', padding: '6px 10px', borderRadius: 6,
            background: 'rgba(255,255,255,0.08)', fontSize: 11, lineHeight: 1.35, opacity: 0.85 }}>
            <i className="ti ti-eye" style={{ marginRight: 5 }} />
            {LIBELLE_ROLE.lecture} — les modifications sont désactivées
          </div>
        )}
        <button className={`${styles.navItem} ${styles.logout}`} onClick={() => authAPI.logout()}>
          <i className="ti ti-logout" aria-hidden="true" />
          <span>Déconnexion</span>
        </button>
      </div>
    </aside>
  )
}
