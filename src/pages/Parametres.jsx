import { useState, useEffect } from 'react'
import { useModules } from '../data/ModulesContext.jsx'
import { useExercice } from '../data/ExerciceContext.jsx'
import styles from './Parametres.module.css'
import CompteSecurite from '../components/CompteSecurite.jsx'
import LogoSociete from '../components/LogoSociete.jsx'
import SocietesLiees from '../components/SocietesLiees.jsx'
import { API_BASE, utilisateursAPI, authAPI, setRole, LIBELLE_ROLE, formatErreurAPI, estAdmin } from '../services/api.js'
import { normaliserIceSaisie, normaliserIfSaisie, normaliserTpSaisie } from '../utils/formUtils.js'
import { notifier } from '../services/notifications.js'

const MODULES_CONFIG = [
  {
    id:          'facturation',
    label:       'Facturation',
    icon:        'ti-file-invoice',
    description: 'Factures achat/vente, clients, fournisseurs, articles, devis, bons de commande',
    couleur:     '#185FA5',
  },
  {
    id:          'comptabilite',
    label:       'Comptabilité',
    icon:        'ti-calculator',
    description: 'Journal, plan de comptes CGNC, TVA, bilan, CPC, grand livre, liasse fiscale',
    couleur:     '#3B6D11',
  },
  {
    id:          'paie_grh',
    label:       'Paie / GRH',
    icon:        'ti-users-group',
    description: 'Bulletins de paie, CNSS/AMO/IR, congés, contrats, attestations',
    couleur:     '#854F0B',
  },
]

const TOKEN = () => localStorage.getItem('hisabpro_token')
const API = API_BASE

async function apiFetch(url, opts = {}) {
  const res = await fetch(API + url, {
    ...opts,
    headers: { Authorization: `Bearer ${TOKEN()}`, 'Content-Type': 'application/json', ...(opts.headers || {}) },
  })
  if (!res.ok) { const e = await res.json().catch(() => ({ detail: 'Erreur' })); throw new Error(formatErreurAPI(e.detail)) }
  if (res.status === 204) return null
  return res.json()
}

const BANQUES_MAROC = [
  'Attijariwafa Bank', 'Banque Populaire', 'BMCE Bank of Africa',
  'BMCI', 'CIH Bank', 'Société Générale Maroc', 'Crédit du Maroc',
  'CFG Bank', 'Al Barid Bank', 'CDG Capital', 'Autre',
]

function OngletUtilisateurs() {
  const [users, setUsers]       = useState([])
  const [roles, setRoles]       = useState([])
  const [chargement, setCharge] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [showInvitation, setShowInvitation] = useState(false)
  const [invitation, setInvitation] = useState({ email: '', role: 'comptable' })
  const [societeId, setSocieteId] = useState(null)
  const [form, setForm]         = useState({ nom: '', email: '', mot_de_passe: '', role: 'comptable' })
  const [erreur, setErreur]     = useState('')
  const [enCours, setEnCours]   = useState(false)
  const [admin, setAdmin] = useState(false)

  async function charger() {
    setCharge(true)
    try {
      // Le rôle vient du serveur : le stockage local peut dater d'une session
      // ouverte avant la mise en place des rôles.
      const [u, r, moi] = await Promise.all([
        utilisateursAPI.lister(), utilisateursAPI.roles(), authAPI.me(),
      ])
      setUsers(u); setRoles(r)
      setAdmin(moi?.role === 'admin')
      setSocieteId(moi?.societe_id || null)
      setRole(moi?.role)   // resynchronise le stockage local pour le reste de l'app
    } catch (e) { setErreur(e.message) }
    finally { setCharge(false) }
  }
  useEffect(() => { charger() }, [])

  async function creer() {
    setErreur('')
    if (!form.nom.trim())   return setErreur("Le nom est obligatoire.")
    if (!form.email.trim()) return setErreur("L'adresse e-mail est obligatoire.")
    if (form.mot_de_passe.length < 8) return setErreur('Le mot de passe doit contenir au moins 8 caractères.')
    setEnCours(true)
    try {
      await utilisateursAPI.creer(form)
      setForm({ nom: '', email: '', mot_de_passe: '', role: 'comptable' })
      setShowForm(false)
      charger()
    } catch (e) { setErreur(e.message) }
    finally { setEnCours(false) }
  }

  async function changerRole(u, role) {
    try { await utilisateursAPI.modifier(u.id, { role }); charger() }
    catch (e) { notifier.erreur(e.message) }
  }
  async function inviter() {
    setErreur('')
    if (!invitation.email.trim()) return setErreur("L'adresse e-mail est obligatoire.")
    if (!societeId) return setErreur('La société active est indisponible. Rechargez les utilisateurs.')
    setEnCours(true)
    try {
      const query = new URLSearchParams({ email: invitation.email.trim(), role: invitation.role })
      const response = await fetch(`${API_BASE}/api/societes/${societeId}/inviter?${query}`, {
        method: 'POST', headers: { Authorization: `Bearer ${localStorage.getItem('hisabpro_token')}` },
      })
      const body = await response.json().catch(() => ({}))
      if (!response.ok) throw new Error(formatErreurAPI(body.detail))
      setShowInvitation(false)
      setInvitation({ email: '', role: 'comptable' })
      await charger()
    } catch (error) { setErreur(error.message) }
    finally { setEnCours(false) }
  }
  async function basculerActif(u) {
    try { await utilisateursAPI.modifier(u.id, { actif: !accesActif(u) }); charger() }
    catch (e) { notifier.erreur(e.message) }
  }
  function accesActif(u) { return u.acces_invite ? (u.actif_acces ?? u.actif) : u.actif }
  async function supprimer(u) {
    const message = u.acces_invite
      ? `Retirer l'accès de ${u.nom} à cette société ? Son compte restera disponible dans ses autres sociétés.`
      : `Supprimer définitivement le compte de ${u.nom} ?`
    if (!confirm(message)) return
    try { await utilisateursAPI.supprimer(u.id); charger() }
    catch (e) { notifier.erreur(e.message) }
  }

  return (
    <div className={styles.card}>
      <div className={styles.cardHeader}>
        <div>
          <div className={styles.cardTitle}>Utilisateurs</div>
          <div style={{ fontSize: 11.5, color: 'var(--text-tertiary)' }}>
            Comptes ayant accès à cette société et niveau d&apos;accès de chacun
          </div>
        </div>
        {admin && !showForm && !showInvitation && (
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <button className={styles.btnPrim} onClick={() => { setErreur(''); setShowForm(true) }}>
              <i className="ti ti-user-plus" /> Ajouter un utilisateur
            </button>
            <button className={styles.btnSec} onClick={() => { setErreur(''); setShowInvitation(true) }}>Donner accès à un utilisateur existant</button>
          </div>
        )}
      </div>

      <div className={styles.cardBody}>
        {!chargement && !admin && (
          <div style={{ padding: '10px 14px', borderRadius: 8, background: 'var(--bg-secondary)',
            fontSize: 12.5, color: 'var(--text-secondary)', marginBottom: 14 }}>
            Seuls les administrateurs peuvent ajouter ou modifier des utilisateurs.
          </div>
        )}

        {showInvitation && (
          <form onSubmit={event => { event.preventDefault(); inviter() }} style={{ border: '0.5px solid var(--border-light)', borderRadius: 10, padding: 16, marginBottom: 16 }}>
            <p style={{ fontSize: 12.5, marginTop: 0 }}>Le compte doit déjà exister dans HisabPro. Ses accès à ses autres sociétés sont conservés.</p>
            <div className={styles.formRow}>
              <div className={styles.formGroup}>
                <label className={styles.label} htmlFor="invitation-email">E-mail du compte existant</label>
                <input id="invitation-email" className={styles.input} type="email" required value={invitation.email}
                  onChange={event => setInvitation(prev => ({ ...prev, email: event.target.value }))} />
              </div>
              <div className={styles.formGroup}>
                <label className={styles.label} htmlFor="invitation-role">Rôle dans cette société</label>
                <select id="invitation-role" className={styles.input} value={invitation.role}
                  onChange={event => setInvitation(prev => ({ ...prev, role: event.target.value }))}>
                  {roles.map(role => <option key={role.code} value={role.code}>{role.libelle}</option>)}
                </select>
              </div>
            </div>
            {erreur && <p role="alert" style={{ color: 'var(--red)', fontSize: 12.5 }}>{erreur}</p>}
            <div style={{ display: 'flex', gap: 8 }}>
              <button className={styles.btnPrim} type="submit" disabled={enCours}>{enCours ? 'Attribution…' : 'Accorder cet accès'}</button>
              <button className={styles.btnSec} type="button" disabled={enCours} onClick={() => { setShowInvitation(false); setErreur('') }}>Annuler</button>
            </div>
          </form>
        )}

        {showForm && (
          <div style={{ border: '0.5px solid var(--border-light)', borderRadius: 10, padding: 16, marginBottom: 16 }}>
            <div className={styles.formRow}>
              <div className={styles.formGroup}>
                <label className={styles.label}>Nom complet</label>
                <input className={styles.input} value={form.nom}
                  onChange={e => setForm(p => ({ ...p, nom: e.target.value }))} />
              </div>
              <div className={styles.formGroup}>
                <label className={styles.label}>Adresse e-mail</label>
                <input className={styles.input} type="email" value={form.email}
                  onChange={e => setForm(p => ({ ...p, email: e.target.value }))} />
              </div>
            </div>
            <div className={styles.formRow}>
              <div className={styles.formGroup}>
                <label className={styles.label}>Mot de passe provisoire</label>
                <input className={styles.input} type="password" autoComplete="new-password" value={form.mot_de_passe}
                  placeholder="8 caractères minimum"
                  onChange={e => setForm(p => ({ ...p, mot_de_passe: e.target.value }))} />
              </div>
              <div className={styles.formGroup}>
                <label className={styles.label}>Rôle</label>
                <select className={styles.input} value={form.role}
                  onChange={e => setForm(p => ({ ...p, role: e.target.value }))}>
                  {roles.map(r => <option key={r.code} value={r.code}>{r.libelle}</option>)}
                </select>
              </div>
            </div>
            <div style={{ fontSize: 11.5, color: 'var(--text-tertiary)', marginBottom: 12 }}>
              {roles.find(r => r.code === form.role)?.description}
            </div>
            {erreur && <div style={{ color: 'var(--red)', fontSize: 12.5, marginBottom: 10 }}>{erreur}</div>}
            <div style={{ display: 'flex', gap: 8 }}>
              <button className={styles.btnPrim} onClick={creer} disabled={enCours}>
                {enCours ? 'Création…' : 'Créer le compte'}
              </button>
              <button className={styles.btnSec} onClick={() => { setShowForm(false); setErreur('') }}>Annuler</button>
            </div>
          </div>
        )}

        {chargement ? (
          <div style={{ padding: 24, textAlign: 'center', color: 'var(--text-tertiary)' }}>Chargement…</div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ color: 'var(--text-tertiary)', fontSize: 11.5, textAlign: 'left' }}>
                <th style={{ padding: '8px 0', fontWeight: 500 }}>Nom</th>
                <th style={{ padding: '8px 0', fontWeight: 500 }}>E-mail</th>
                <th style={{ padding: '8px 0', fontWeight: 500 }}>Rôle</th>
                <th style={{ padding: '8px 0', fontWeight: 500 }}>Statut</th>
                {admin && <th style={{ padding: '8px 0', fontWeight: 500, textAlign: 'right' }}>Actions</th>}
              </tr>
            </thead>
            <tbody>
              {users.map(u => (
                <tr key={u.id} style={{ borderTop: '0.5px solid var(--border-light)', opacity: u.actif ? 1 : 0.5 }}>
                  <td style={{ padding: '10px 0' }}>
                    {u.nom}
                    {u.acces_invite && <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>Accès invité</div>}
                  </td>
                  <td style={{ padding: '10px 0', color: 'var(--text-secondary)' }}>{u.email}</td>
                  <td style={{ padding: '10px 0' }}>
                    {admin ? (
                      <select value={u.role} onChange={e => changerRole(u, e.target.value)}
                        style={{ fontSize: 12, padding: '4px 8px', borderRadius: 6,
                          border: '0.5px solid var(--border-medium)', background: 'var(--bg-primary)' }}>
                        {roles.map(r => <option key={r.code} value={r.code}>{r.libelle}</option>)}
                      </select>
                    ) : (LIBELLE_ROLE[u.role] || u.role)}
                  </td>
                  <td style={{ padding: '10px 0' }}>
                    <span style={{ fontSize: 11.5, padding: '3px 8px', borderRadius: 20,
                      background: u.actif ? '#EAF3DE' : 'var(--bg-secondary)',
                      color: u.actif ? '#3B6D11' : 'var(--text-tertiary)' }}>
                      {u.acces_invite && u.actif_compte === false ? 'Compte désactivé' : u.actif ? 'Actif' : 'Désactivé'}
                    </span>
                    {u.acces_invite && u.actif_compte === false && <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 4 }}>
                      Accès à cette société {accesActif(u) ? 'actif' : 'désactivé'}. Le compte doit être réactivé par son administrateur principal.
                    </div>}
                  </td>
                  {admin && (
                    <td style={{ padding: '10px 0', textAlign: 'right' }}>
                      <button onClick={() => basculerActif(u)} title={u.acces_invite ? (accesActif(u) ? "Désactiver l'accès" : "Activer l'accès") : (u.actif ? 'Désactiver' : 'Réactiver')}
                        style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-tertiary)', fontSize: 15, marginRight: 4 }}>
                        <i className={accesActif(u) ? 'ti ti-user-off' : 'ti ti-user-check'} />
                      </button>
                      <button onClick={() => supprimer(u)} title={u.acces_invite ? "Retirer l'accès" : "Supprimer"}
                        style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--red)', fontSize: 15 }}><i className="ti ti-trash" /><span className="libelle-action" aria-hidden="true">{u.acces_invite ? "Retirer l'accès" : "Supprimer"}</span></button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

function OngletBanques() {
  const [comptes, setComptes]   = useState([])
  const [loading, setLoading]   = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [selected, setSelected] = useState(null)
  const [form, setForm]         = useState({ banque: '', agence: '', rib: '', iban: '', devise: 'MAD', compte_comptable: '5141' })
  const [banqueAutre, setBanqueAutre] = useState(false)
  const [saving, setSaving]     = useState(false)
  const [erreur, setErreur]     = useState('')

  async function charger() {
    setLoading(true)
    try { setComptes(await apiFetch('/api/banques')) }
    catch { setComptes([]) }
    finally { setLoading(false) }
  }

  useEffect(() => { charger() }, [])

  function ouvrirForm(compte = null) {
    setSelected(compte)
    setBanqueAutre(Boolean(compte && (compte.banque === 'Autre' || !BANQUES_MAROC.includes(compte.banque))))
    setForm(compte ? {
      banque: compte.banque, agence: compte.agence || '',
      rib: compte.rib || '', iban: compte.iban || '',
      devise: compte.devise || 'MAD', compte_comptable: compte.compte_comptable || '5141',
    } : { banque: '', agence: '', rib: '', iban: '', devise: 'MAD', compte_comptable: '5141' })
    setShowForm(true)
    setErreur('')
  }

  async function handleSave() {
    if (!form.banque.trim()) return
    setSaving(true); setErreur('')
    try {
      if (selected) {
        await apiFetch(`/api/banques/${selected.id}`, { method: 'PATCH', body: JSON.stringify(form) })
      } else {
        await apiFetch('/api/banques', { method: 'POST', body: JSON.stringify(form) })
      }
      setShowForm(false)
      charger()
    } catch (e) { setErreur(e.message) }
    finally { setSaving(false) }
  }

  async function supprimer(id) {
    if (!confirm('Supprimer ce compte bancaire ?')) return
    try { await apiFetch(`/api/banques/${id}`, { method: 'DELETE' }); charger() } catch {}
  }

  const COMPTES_BQ = ['5141', '5142', '5143', '5144', '5145']

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>
          {comptes.length} compte{comptes.length !== 1 ? 's' : ''} bancaire{comptes.length !== 1 ? 's' : ''}
        </span>
        <button className={styles.btnPrim} onClick={() => ouvrirForm()}>
          <i className="ti ti-plus" /> Ajouter un compte
        </button>
      </div>

      {/* Formulaire */}
      {showForm && (
        <div style={{
          background: 'var(--bg-secondary)', border: '0.5px solid var(--border-medium)',
          borderRadius: 'var(--radius-lg)', padding: 20, display: 'flex', flexDirection: 'column', gap: 14,
        }}>
          <div style={{ fontSize: 13, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8 }}>
            <i className="ti ti-building-bank" style={{ color: 'var(--blue)' }} />
            {selected ? 'Modifier le compte' : 'Nouveau compte bancaire'}
          </div>

          <div className={styles.formRow}>
            <div className={styles.formGroup}>
              <label>Banque *</label>
              <select className={styles.input} value={banqueAutre ? 'Autre' : form.banque}
                onChange={e => {
                  const choix = e.target.value
                  setBanqueAutre(choix === 'Autre')
                  setForm(p => ({ ...p, banque: choix === 'Autre' ? '' : choix }))
                }}>
                <option value="">— Choisir —</option>
                {BANQUES_MAROC.map(b => <option key={b} value={b}>{b}</option>)}
              </select>
              {banqueAutre && (
                <input className={styles.input} style={{ marginTop: 6 }} type="text"
                  placeholder="Nom de la banque..."
                  aria-label="Nom de la banque"
                  value={form.banque}
                  onChange={e => setForm(p => ({ ...p, banque: e.target.value }))} />
              )}
            </div>
            <div className={styles.formGroup}>
              <label>Agence</label>
              <input className={styles.input} type="text" placeholder="ex: Agence Hay Riad"
                value={form.agence} onChange={e => setForm(p => ({ ...p, agence: e.target.value }))} />
            </div>
          </div>

          <div className={styles.formGroup}>
            <label>RIB</label>
            <input className={styles.input} type="text"
              placeholder="000 000 0000000000000000 00"
              value={form.rib} onChange={e => setForm(p => ({ ...p, rib: e.target.value }))} />
          </div>

          <div className={styles.formRow}>
            <div className={styles.formGroup}>
              <label>IBAN (optionnel)</label>
              <input className={styles.input} type="text" placeholder="MA..."
                value={form.iban} onChange={e => setForm(p => ({ ...p, iban: e.target.value }))} />
            </div>
            <div className={styles.formGroup}>
              <label>Devise</label>
              <select className={styles.input} value={form.devise}
                onChange={e => setForm(p => ({ ...p, devise: e.target.value }))}>
                {['MAD', 'EUR', 'USD', 'GBP'].map(d => <option key={d} value={d}>{d}</option>)}
              </select>
            </div>
            <div className={styles.formGroup}>
              <label>Compte CGNC</label>
              <select className={styles.input} value={form.compte_comptable}
                onChange={e => setForm(p => ({ ...p, compte_comptable: e.target.value }))}>
                {COMPTES_BQ.map(n => <option key={n} value={n}>{n} — Banque</option>)}
                <option value="5161">5161 — Caisse</option>
              </select>
            </div>
          </div>

          {erreur && (
            <div style={{ fontSize: 12, color: 'var(--red)', background: 'var(--red-light)', padding: '8px 12px', borderRadius: 6 }}>
              {erreur}
            </div>
          )}

          <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
            <button className={styles.btnSec} onClick={() => setShowForm(false)}>Annuler</button>
            <button className={styles.btnPrim} onClick={handleSave}
              disabled={!form.banque.trim() || saving}>
              {saving ? 'Enregistrement...' : <><i className="ti ti-device-floppy" /> {selected ? 'Modifier' : 'Créer'}</>}
            </button>
          </div>
        </div>
      )}

      {/* Liste des comptes */}
      {loading ? (
        <div style={{ padding: 32, textAlign: 'center', color: 'var(--text-tertiary)' }}>
          <i className="ti ti-loader-2 ti-spin" style={{ fontSize: 24 }} />
        </div>
      ) : comptes.length === 0 ? (
        <div style={{ padding: 48, textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 13, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10 }}>
          <i className="ti ti-building-bank" style={{ fontSize: 32 }} />
          <span>Aucun compte bancaire — ajoutez votre premier compte</span>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {comptes.map(compte => (
            <div key={compte.id} style={{
              background: 'var(--bg-primary)', border: '0.5px solid var(--border-light)',
              borderRadius: 'var(--radius-lg)', padding: '14px 18px',
              display: 'flex', alignItems: 'center', gap: 16,
            }}>
              {/* Icone banque */}
              <div style={{
                width: 44, height: 44, borderRadius: 10, flexShrink: 0,
                background: 'var(--blue-light)', display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <i className="ti ti-building-bank" style={{ fontSize: 20, color: 'var(--blue)' }} />
              </div>

              {/* Infos principales */}
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 3 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ fontSize: 14, fontWeight: 600 }}>{compte.banque}</span>
                  <span style={{ fontSize: 10, background: 'var(--blue-light)', color: 'var(--blue)', padding: '1px 7px', borderRadius: 100, fontWeight: 500 }}>
                    {compte.devise}
                  </span>
                  <span style={{ fontSize: 10, background: 'var(--bg-secondary)', color: 'var(--text-tertiary)', padding: '1px 7px', borderRadius: 100 }}>
                    {compte.compte_comptable}
                  </span>
                </div>
                {compte.agence && (
                  <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                    <i className="ti ti-map-pin" style={{ fontSize: 11, marginRight: 4 }} />
                    {compte.agence}
                  </span>
                )}
                {compte.rib && (
                  <span style={{ fontSize: 11, fontFamily: 'monospace', color: 'var(--text-tertiary)', letterSpacing: 0.5 }}>
                    RIB : {compte.rib}
                  </span>
                )}
                {compte.iban && (
                  <span style={{ fontSize: 11, fontFamily: 'monospace', color: 'var(--text-tertiary)' }}>
                    IBAN : {compte.iban}
                  </span>
                )}
              </div>

              {/* Actions */}
              <div style={{ display: 'flex', gap: 6 }}>
                <button onClick={() => ouvrirForm(compte)} aria-label={`Modifier le compte bancaire ${compte.banque}`}
                  style={{ width: 32, height: 32, borderRadius: 6, border: '0.5px solid var(--border-medium)', background: 'var(--bg-primary)', cursor: 'pointer', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <i className="ti ti-pencil" style={{ fontSize: 14 }} />
                </button>
                <button onClick={() => supprimer(compte.id)} aria-label={`Supprimer le compte bancaire ${compte.banque}`}
                  style={{ width: 32, height: 32, borderRadius: 6, border: '0.5px solid #F5BEBE', background: 'var(--bg-primary)', cursor: 'pointer', color: 'var(--red)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <i className="ti ti-trash" style={{ fontSize: 14 }} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function OngletProduction() {
  const [controle, setControle] = useState(null)
  const [audit, setAudit] = useState([])
  const [loading, setLoading] = useState(false)
  const [erreur, setErreur] = useState('')
  const admin = estAdmin()

  async function charger() {
    if (!admin) return
    setLoading(true); setErreur('')
    try {
      const [c, a] = await Promise.all([
        apiFetch('/api/production/controle'),
        apiFetch('/api/production/audit-actions?limit=100'),
      ])
      setControle(c); setAudit(a)
    } catch (e) { setErreur(e.message) }
    finally { setLoading(false) }
  }

  useEffect(() => { charger() }, [])

  if (!admin) {
    return <div className={styles.card}><div className={styles.cardBody}>
      <div style={{ fontSize: 12.5, color: 'var(--text-secondary)' }}>
        Le contrôle production et la piste d’audit sont réservés aux administrateurs.
      </div>
    </div></div>
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      <div className={styles.card}>
        <div className={styles.cardHeader}>
          <div>
            <div className={styles.cardTitle}><i className="ti ti-shield-check" /> Contrôle production</div>
            <div style={{ fontSize: 11.5, color: 'var(--text-tertiary)', marginTop: 3 }}>
              Vérification lecture seule des pièces, écritures, échéanciers, acomptes, stocks et liens inter-sociétés.
            </div>
          </div>
          <button className={styles.btnPrim} onClick={charger} disabled={loading}>
            <i className="ti ti-refresh" /> {loading ? 'Contrôle…' : 'Relancer le contrôle'}
          </button>
        </div>
        <div className={styles.cardBody}>
          {erreur && <div style={{ color: 'var(--red)', fontSize: 12.5, marginBottom: 12 }}>{erreur}</div>}
          {controle && <>
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 14 }}>
              <span style={{ padding: '6px 10px', borderRadius: 20, fontSize: 12, fontWeight: 600,
                background: controle.pret_production ? '#EAF3DE' : '#FCEBEB',
                color: controle.pret_production ? '#3B6D11' : '#A32D2D' }}>
                {controle.pret_production ? 'Aucun blocage détecté' : `${controle.nb_bloquants} blocage(s) détecté(s)`}
              </span>
              <span style={{ padding: '6px 10px', borderRadius: 20, fontSize: 12, background: 'var(--bg-secondary)', color: 'var(--text-secondary)' }}>
                {controle.nb_avertissements} avertissement(s)
              </span>
            </div>
            <div style={{ border: '0.5px solid var(--border-light)', borderRadius: 9, overflow: 'hidden' }}>
              {controle.checks.map(c => <div key={c.code} style={{ display: 'grid', gridTemplateColumns: '28px 1fr auto', gap: 8,
                alignItems: 'center', padding: '9px 11px', borderBottom: '0.5px solid var(--border-light)', fontSize: 12 }}>
                <i className={`ti ${c.ok ? 'ti-circle-check' : c.niveau === 'bloquant' ? 'ti-alert-triangle' : 'ti-alert-circle'}`}
                  style={{ color: c.ok ? '#3B6D11' : c.niveau === 'bloquant' ? '#A32D2D' : '#946200' }} />
                <span>{c.libelle}</span>
                <strong style={{ color: c.ok ? 'var(--text-tertiary)' : 'var(--text-primary)' }}>{c.ok ? 'OK' : c.nb}</strong>
              </div>)}
            </div>
          </>}
        </div>
      </div>

      <div className={styles.card}>
        <div className={styles.cardHeader}>
          <div>
            <div className={styles.cardTitle}><i className="ti ti-history" /> Piste d’audit applicative</div>
            <div style={{ fontSize: 11.5, color: 'var(--text-tertiary)', marginTop: 3 }}>
              100 dernières opérations modifiantes. Aucun contenu sensible des formulaires n’est dupliqué dans ce journal.
            </div>
          </div>
        </div>
        <div className={styles.cardBody} style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11.5 }}>
            <thead><tr style={{ textAlign: 'left', color: 'var(--text-tertiary)' }}>
              <th style={{ padding: 8 }}>Date</th><th>Utilisateur</th><th>Rôle</th><th>Méthode</th><th>Action</th><th>Résultat</th>
            </tr></thead>
            <tbody>{audit.map(a => <tr key={a.id} style={{ borderTop: '0.5px solid var(--border-light)' }}>
              <td style={{ padding: 8, whiteSpace: 'nowrap' }}>{a.created_at ? new Date(a.created_at).toLocaleString('fr-FR') : '—'}</td>
              <td>{a.acteur_nom || a.acteur_email || (a.acteur_id ? `#${a.acteur_id}` : 'Système')}</td>
              <td>{a.acteur_role || '—'}</td>
              <td><strong>{a.methode}</strong></td>
              <td style={{ fontFamily: 'monospace' }}>{a.chemin}</td>
              <td><span style={{ color: a.succes ? '#3B6D11' : '#A32D2D', fontWeight: 600 }}>{a.statut_http}</span></td>
            </tr>)}</tbody>
          </table>
          {!audit.length && !loading && <div style={{ padding: 18, textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 12 }}>Aucune action journalisée pour le moment.</div>}
        </div>
      </div>
    </div>
  )
}

export default function Parametres() {
  const { societe, modules, toggleModule, mettreAJourSociete } = useModules()
  const { annee, rechargerExercices } = useExercice()
  const [onglet,   setOnglet]   = useState('societe')
  const [form,     setForm]     = useState(societe || {})
  const [saving,   setSaving]   = useState(false)
  const [saved,    setSaved]    = useState(false)
  const [erreur,   setErreur]   = useState('')

  // Les paramètres arrivent après le chargement du profil de société.
  // Ne pas laisser un formulaire initialisé à {} écraser la fiche courante.
  useEffect(() => { setForm(societe || {}) }, [societe?.id])

  function majChamp(champ, val) {
    setForm(prev => ({ ...prev, [champ]: val }))
    setSaved(false)
  }

  async function handleSave() {
    setSaving(true)
    setErreur('')
    try {
      const ancienDebut = Number(societe?.exercice_debut)
      const nouveauDebut = Number(form.exercice_debut)
      if (!Number.isInteger(nouveauDebut) || nouveauDebut < 1900 || nouveauDebut > 2200) {
        throw new Error('Renseignez une année de premier exercice comprise entre 1900 et 2200.')
      }
      const resultat = await mettreAJourSociete({
        ...form,
        // Un ancien logo reste inchangé lorsqu'on édite un autre paramètre.
        logo_url: form.logo_url !== societe?.logo_url ? form.logo_url : undefined,
        ice: normaliserIceSaisie(form.ice) || null,
        identifiant_fiscal: normaliserIfSaisie(form.identifiant_fiscal) || null,
        patente: normaliserTpSaisie(form.patente) || null,
      })
      if (!resultat) throw new Error('La mise à jour n’a pas été confirmée par le serveur.')
      if (nouveauDebut !== ancienDebut && Number.isInteger(nouveauDebut)) {
        await rechargerExercices(nouveauDebut)
      }
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch (e) {
      setErreur(e.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className={styles.page} data-form-page>
      <div className={styles.topbar}>
        <h1 className={styles.pageTitle}>Paramètres</h1>
      </div>

      <div className={styles.content}>
        {/* Onglets */}
        <div className={styles.onglets}>
          {[
            { id: 'societe',  label: 'Fiche société',   icon: 'ti-building' },
            { id: 'modules',  label: 'Modules',          icon: 'ti-puzzle'   },
            { id: 'fiscalite',label: 'Fiscalité',        icon: 'ti-receipt'  },
            { id: 'banques',  label: 'Comptes bancaires', icon: 'ti-building-bank' },
            { id: 'utilisateurs', label: 'Utilisateurs',  icon: 'ti-users' },
            { id: 'liaisons', label: 'Sociétés liées', icon: 'ti-building-community' },
            { id: 'production', label: 'Sécurité & contrôle', icon: 'ti-shield-check' },
            { id: 'compte', label: 'Mon compte', icon: 'ti-user' },
          ].map(o => (
            <button key={o.id}
              className={`${styles.ongletBtn} ${onglet === o.id ? styles.ongletBtnActif : ''}`}
              onClick={() => setOnglet(o.id)}>
              <i className={`ti ${o.icon}`} aria-hidden="true" /> {o.label}
            </button>
          ))}
        </div>

        {onglet === 'liaisons' && <SocietesLiees societeId={societe?.id} />}
        {/* ── FICHE SOCIÉTÉ ── */}
        {onglet === 'societe' && (
          <div className={styles.card}>
            <div className={styles.cardHeader}>
              <span className={styles.cardTitle}>
                <i className="ti ti-building" aria-hidden="true" /> Informations de la société
              </span>
              <div style={{ display: 'flex', gap: 8 }}>
                {saved && <span className={styles.savedBadge}><i className="ti ti-check" aria-hidden="true" /> Enregistré</span>}
                {erreur && <span style={{ color: 'var(--red)', fontSize: 12 }}>{erreur}</span>}
                <button className={styles.btnPrim} onClick={handleSave} disabled={saving}>
                  {saving ? 'Enregistrement...' : <><i className="ti ti-device-floppy" aria-hidden="true" /> Enregistrer</>}
                </button>
              </div>
            </div>

            <div className={styles.formGrid}>
              {/* Identité */}
              <div className={styles.section}>
                <div className={styles.sectionTitle}>Identité</div>
                <div className={styles.formGroup}>
                  <LogoSociete key={societe?.id} value={form.logo_url} onChange={value => majChamp('logo_url', value)} disabled={!estAdmin() || saving} />
                </div>
                <div className={styles.formGroup}>
                  <label>Raison sociale *</label>
                  <input className={styles.input} type="text"
                    value={form.raison_sociale || ''}
                    onChange={e => majChamp('raison_sociale', e.target.value)} />
                </div>
                <div className={styles.formRow}>
                  <div className={styles.formGroup}>
                    <label>Forme juridique</label>
                    <select className={styles.input}
                      value={form.forme_juridique || ''}
                      onChange={e => majChamp('forme_juridique', e.target.value)}>
                      <option value="">— Choisir —</option>
                      {['SARL', 'SARL AU', 'SA', 'SAS', 'SNC', 'SCS', 'GIE', 'Auto-entrepreneur', 'Personne physique'].map(f =>
                        <option key={f} value={f}>{f}</option>)}
                    </select>
                  </div>
                  <div className={styles.formGroup}>
                    <label>Capital social (MAD)</label>
                    <input className={styles.input} type="number" min="0" step="1000" placeholder="100000"
                      value={form.capital_social ?? ''}
                      onChange={e => majChamp('capital_social', e.target.value === '' ? null : parseFloat(e.target.value))} />
                  </div>
                </div>
                <div className={styles.formRow}>
                  <div className={styles.formGroup}>
                    <label>Identifiant Fiscal (IF)</label>
                    <input className={styles.input} type="text" placeholder="00000000"
                      value={form.identifiant_fiscal || ''}
                      onChange={e => majChamp('identifiant_fiscal', normaliserIfSaisie(e.target.value))} />
                  </div>
                  <div className={styles.formGroup}>
                    <label>ICE</label>
                    <input className={styles.input} type="text" placeholder="000000000000000"
                      value={form.ice || ''}
                      onChange={e => majChamp('ice', normaliserIceSaisie(e.target.value))} />
                  </div>
                </div>
                <div className={styles.formRow}>
                  <div className={styles.formGroup}>
                    <label>RC (Registre Commerce)</label>
                    <input className={styles.input} type="text"
                      value={form.rc || ''}
                      onChange={e => majChamp('rc', e.target.value)} />
                  </div>
                  <div className={styles.formGroup}>
                    <label>Patente</label>
                    <input className={styles.input} type="text"
                      value={form.patente || ''}
                      onChange={e => majChamp('patente', normaliserTpSaisie(e.target.value))} />
                  </div>
                </div>
                <div className={styles.formGroup}>
                  <label>N° CNSS</label>
                  <input className={styles.input} type="text"
                    value={form.cnss_numero || ''}
                    onChange={e => majChamp('cnss_numero', e.target.value)} />
                </div>
              </div>

              {/* Coordonnées */}
              <div className={styles.section}>
                <div className={styles.sectionTitle}>Coordonnées</div>
                <div className={styles.formGroup}>
                  <label>Adresse</label>
                  <textarea className={styles.input} rows={2}
                    value={form.adresse || ''}
                    onChange={e => majChamp('adresse', e.target.value)} />
                </div>
                <div className={styles.formRow}>
                  <div className={styles.formGroup}>
                    <label>Ville</label>
                    <input className={styles.input} type="text"
                      value={form.ville || ''}
                      onChange={e => majChamp('ville', e.target.value)} />
                  </div>
                  <div className={styles.formGroup}>
                    <label>Pays</label>
                    <input className={styles.input} type="text"
                      value={form.pays || 'Maroc'}
                      onChange={e => majChamp('pays', e.target.value)} />
                  </div>
                </div>
                <div className={styles.formRow}>
                  <div className={styles.formGroup}>
                    <label>Téléphone</label>
                    <input className={styles.input} type="tel"
                      value={form.telephone || ''}
                      onChange={e => majChamp('telephone', e.target.value)} />
                  </div>
                  <div className={styles.formGroup}>
                    <label>FAX</label>
                    <input className={styles.input} type="tel"
                      value={form.fax || ''}
                      onChange={e => majChamp('fax', e.target.value)} />
                  </div>
                </div>
                <div className={styles.formRow}>
                  <div className={styles.formGroup}>
                    <label>Email</label>
                    <input className={styles.input} type="email"
                      value={form.email || ''}
                      onChange={e => majChamp('email', e.target.value)} />
                  </div>
                  <div className={styles.formGroup}>
                    <label>Site web</label>
                    <input className={styles.input} type="url"
                      value={form.site_web || ''}
                      onChange={e => majChamp('site_web', e.target.value)} />
                  </div>
                </div>
              </div>

              {/* Banque */}
              <div className={styles.section}>
                <div className={styles.sectionTitle}>Banque</div>
                <div className={styles.formRow}>
                  <div className={styles.formGroup}>
                    <label>Banque</label>
                    <input className={styles.input} type="text" placeholder="Banque Populaire, CIH..."
                      value={form.banque || ''}
                      onChange={e => majChamp('banque', e.target.value)} />
                  </div>
                  <div className={styles.formGroup}>
                    <label>Agence</label>
                    <input className={styles.input} type="text"
                      value={form.agence || ''}
                      onChange={e => majChamp('agence', e.target.value)} />
                  </div>
                </div>
                <div className={styles.formGroup}>
                  <label>RIB</label>
                  <input className={styles.input} type="text" placeholder="000 000 0000000000000000 00"
                    value={form.rib || ''}
                    onChange={e => majChamp('rib', e.target.value)} />
                </div>
              </div>

              {/* Paramètres comptables */}
              <div className={styles.section}>
                <div className={styles.sectionTitle}>Paramètres comptables</div>
                <div className={styles.formRow}>
                  <div className={styles.formGroup}>
                    <label>Premier exercice (année de clôture)</label>
                    <input className={styles.input} type="number" min="1900" max="2200" step="1"
                      value={form.exercice_debut ?? new Date().getFullYear()}
                      onChange={e => majChamp('exercice_debut', e.target.value ? Number(e.target.value) : null)} />
                    <small style={{ color: 'var(--text-tertiary)', fontSize: 11 }}>
                      Enregistrer crée les exercices antérieurs manquants sans effacer l’historique.
                      Les dates exactes se règlent dans Comptabilité → Clôture.
                    </small>
                  </div>
                  <div className={styles.formGroup}>
                    <label>Périodicité TVA</label>
                    <select className={styles.input}
                      value={form.periodicite_tva || 'mensuelle'}
                      onChange={e => majChamp('periodicite_tva', e.target.value)}>
                      <option value="mensuelle">Mensuelle</option>
                      <option value="trimestrielle">Trimestrielle</option>
                    </select>
                  </div>
                </div>

                <div className={styles.formRow}>
                  <div className={styles.formGroup}>
                    <label>Régime fiscal</label>
                    <select className={styles.input}
                      value={form.regime_fiscal || 'is'}
                      onChange={e => majChamp('regime_fiscal', e.target.value)}>
                      <option value="is">Impôt sur les sociétés (IS)</option>
                      <option value="ir">Impôt sur le revenu (IR)</option>
                      <option value="auto_entrepreneur">Auto-entrepreneur</option>
                      <option value="exonere">Exonéré</option>
                    </select>
                  </div>
                  <div className={styles.formGroup}>
                    <label>Régime de TVA</label>
                    <select className={styles.input}
                      value={form.regime_tva || 'encaissement'}
                      onChange={e => majChamp('regime_tva', e.target.value)}>
                      <option value="encaissement">Encaissement</option>
                      <option value="debit">Débit</option>
                      <option value="exonere">Exonéré de TVA</option>
                      <option value="hors_champ">Hors champ d&apos;application</option>
                    </select>
                    <span style={{ fontSize: 10.5, color: 'var(--text-tertiary)', marginTop: 3 }}>
                      Encaissement : TVA exigible au paiement. Débit : exigible à la facturation.
                    </span>
                  </div>
                </div>

                <div className={styles.formRow}>
                  <div className={styles.formGroup}>
                    <label>Devise de tenue de comptabilité</label>
                    <select className={styles.input}
                      value={form.devise || 'MAD'}
                      onChange={e => majChamp('devise', e.target.value)}>
                      <option value="MAD">Dirham marocain (MAD)</option>
                      <option value="EUR">Euro (EUR)</option>
                      <option value="USD">Dollar américain (USD)</option>
                    </select>
                  </div>
                  <div className={styles.formGroup}>
                    <label>Secteur d&apos;activité</label>
                    <input className={styles.input} type="text"
                      placeholder="Négoce, BTP, services, industrie…"
                      value={form.secteur || ''}
                      onChange={e => majChamp('secteur', e.target.value)} />
                  </div>
                </div>
              </div>

              {/* Numérotation des documents */}
              <div className={styles.section}>
                <div className={styles.sectionTitle}>Numérotation des documents</div>
                <p style={{ fontSize: 11, color: 'var(--text-tertiary)', margin: '0 0 10px 0' }}>
                  Format : PRÉFIXE-EXERCICE-SÉQUENCE (ex: FA-2026-001). La séquence repart à 1 chaque exercice,
                  le numéro définitif est attribué à la validation. Le préfixe s’applique aux nouvelles factures.
                </p>
                <div className={styles.formRow}>
                  <div className={styles.formGroup}>
                    <label>Préfixe Factures</label>
                    <input className={styles.input} type="text" maxLength="10" placeholder="FA"
                      value={form.prefixe_facture ?? 'FA'}
                      onChange={e => majChamp('prefixe_facture', e.target.value.toUpperCase())} />
                  </div>
                  <div className={styles.formGroup}>
                    <label>Préfixe Devis</label>
                    <input className={styles.input} type="text" maxLength="10" placeholder="DV"
                      value={form.prefixe_devis ?? 'DV'}
                      onChange={e => majChamp('prefixe_devis', e.target.value.toUpperCase())} />
                  </div>
                </div>
                <div className={styles.formRow}>
                  <div className={styles.formGroup}>
                    <label>Préfixe Bons de commande</label>
                    <input className={styles.input} type="text" maxLength="10" placeholder="BC"
                      value={form.prefixe_bc ?? 'BC'}
                      onChange={e => majChamp('prefixe_bc', e.target.value.toUpperCase())} />
                  </div>
                  <div className={styles.formGroup}>
                    <label>Préfixe Bons de livraison</label>
                    <input className={styles.input} type="text" maxLength="10" placeholder="BL"
                      value={form.prefixe_bl ?? 'BL'}
                      onChange={e => majChamp('prefixe_bl', e.target.value.toUpperCase())} />
                  </div>
                </div>
                <div className={styles.formRow}>
                  <div className={styles.formGroup}>
                    <label>Préfixe Avoirs</label>
                    <input className={styles.input} type="text" maxLength="10" placeholder="AV"
                      value={form.prefixe_avoir ?? 'AV'}
                      onChange={e => majChamp('prefixe_avoir', e.target.value.toUpperCase())} />
                  </div>
                  <div className={styles.formGroup} />
                </div>
              </div>

              {/* Déclenchement des mouvements de stock */}
              <div className={styles.section}>
                <div className={styles.sectionTitle}>Gestion du stock</div>
                <p style={{ fontSize: 12, color: 'var(--text-tertiary)', margin: '0 0 12px 0' }}>
                  Choisissez le document qui déclenche les mouvements de stock. Par défaut, le stock
                  bouge à la facturation. Vous pouvez le déclencher à la livraison (BL passé en « livré »)
                  ou à la réception (BR passé en « livré ») selon votre organisation.
                </p>
                <div className={styles.formRow}>
                  <div className={styles.formGroup}>
                    <label className={styles.label}>Ventes — sortie de stock</label>
                    <select className={styles.input}
                      value={form.stock_declencheur_vente ?? 'facture'}
                      onChange={e => majChamp('stock_declencheur_vente', e.target.value)}>
                      <option value="facture">À la facturation (défaut)</option>
                      <option value="bl">À la livraison — BL passé en « livré »</option>
                    </select>
                  </div>
                  <div className={styles.formGroup}>
                    <label className={styles.label}>Achats — entrée de stock</label>
                    <select className={styles.input}
                      value={form.stock_declencheur_achat ?? 'facture'}
                      onChange={e => majChamp('stock_declencheur_achat', e.target.value)}>
                      <option value="facture">À la facturation (défaut)</option>
                      <option value="br">À la réception — BR passé en « livré »</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ── MODULES ── */}
        {onglet === 'modules' && (
          <div className={styles.card}>
            <div className={styles.cardHeader}>
              <span className={styles.cardTitle}>
                <i className="ti ti-puzzle" aria-hidden="true" /> Gestion des modules
              </span>
            </div>
            <div className={styles.modulesGrid}>
              {MODULES_CONFIG.map(m => {
                const actif = modules[m.id] === true
                return (
                  <div key={m.id} className={`${styles.moduleCard} ${actif ? styles.moduleActif : styles.moduleInactif}`}>
                    <div className={styles.moduleHeader}>
                      <div className={styles.moduleIcone} style={{ background: actif ? m.couleur : 'var(--border-medium)' }}>
                        <i className={`ti ${m.icon}`} aria-hidden="true" />
                      </div>
                      <div className={styles.moduleInfo}>
                        <div className={styles.moduleLabel}>{m.label}</div>
                        <div className={styles.moduleDesc}>{m.description}</div>
                      </div>
                      <label className={styles.toggle}>
                        <input type="checkbox" checked={actif}
                          onChange={e => toggleModule(m.id, e.target.checked)} />
                        <span className={styles.toggleSlider} />
                      </label>
                    </div>
                    <div className={styles.moduleStatut}>
                      {actif
                        ? <span className={styles.statutActif}><i className="ti ti-check" aria-hidden="true" /> Module actif</span>
                        : <span className={styles.statutInactif}><i className="ti ti-x" aria-hidden="true" /> Module inactif</span>}
                    </div>
                  </div>
                )
              })}
            </div>

            <div className={styles.modulesNote}>
              <i className="ti ti-info-circle" aria-hidden="true" />
              Désactiver un module masque ses fonctionnalités dans l'interface. Les données existantes sont conservées.
              Les modules connectés (ex: Facturation + Comptabilité) génèrent automatiquement les écritures comptables depuis les factures.
            </div>
          </div>
        )}

        {/* ── COMPTES BANCAIRES ── */}
        {onglet === 'banques' && <OngletBanques />}
        {onglet === 'utilisateurs' && <OngletUtilisateurs />}
        {onglet === 'production' && <OngletProduction />}
        {onglet === 'compte' && <CompteSecurite />}

        {/* ── FISCALITÉ ── */}
        {onglet === 'fiscalite' && (
          <div className={styles.card}>
            <div className={styles.cardHeader}>
              <span className={styles.cardTitle}>
                <i className="ti ti-receipt" aria-hidden="true" /> Paramètres fiscaux
              </span>
              <div style={{ display: 'flex', gap: 8 }}>
                {saved && <span className={styles.savedBadge}><i className="ti ti-check" aria-hidden="true" /> Enregistré</span>}
                {erreur && <span style={{ color: 'var(--red)', fontSize: 12 }}>{erreur}</span>}
                <button className={styles.btnPrim} onClick={handleSave} disabled={saving}>
                  {saving ? 'Enregistrement...' : <><i className="ti ti-device-floppy" aria-hidden="true" /> Enregistrer</>}
                </button>
              </div>
            </div>
            <div style={{ padding: 24, color: 'var(--text-secondary)', fontSize: 13 }}>
              <p>Les barèmes IR et taux CNSS/AMO sont configurés par année dans la base de données.</p>
              <p style={{ marginTop: 8 }}>Pour mettre à jour les taux suite à une nouvelle Loi de Finances, exécutez le script SQL correspondant dans pgAdmin.</p>
              <div style={{ marginTop: 16, padding: 12, background: 'var(--blue-light)', borderRadius: 8, fontSize: 12, color: 'var(--blue)' }}>
                <strong>Taux actuellement configurés :</strong> 2025 et 2026
              </div>

              {/* Format des libellés */}
              <div style={{ marginTop: 24, borderTop: '0.5px solid var(--border-light)', paddingTop: 20 }}>
                <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 12, color: 'var(--text-primary)' }}>
                  <i className="ti ti-text-size" style={{ marginRight: 6 }} />
                  Format des libellés d'écritures
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {[
                    { key: 'format_libelle_vente',  label: 'Facture de vente', defaut: 'Facture {numero} {tiers}' },
                    { key: 'format_libelle_achat',  label: "Facture d'achat",  defaut: "Facture d'achat {numero} {tiers}" },
                    { key: 'format_libelle_avoir',  label: 'Avoir',            defaut: 'Avoir {numero} {tiers}' },
                    { key: 'format_libelle_banque', label: 'Règlement',        defaut: 'Règlement {tiers} {ref}' },
                  ].map(f => {
                    const valeur = form[f.key] ?? f.defaut
                    // Exemple uniquement : aucune réservation de numéro.
                    const anneeExemple = annee || new Date().getFullYear()
                    const prefixeExemple = f.key === 'format_libelle_avoir'
                      ? (form.prefixe_avoir || 'AV') : (form.prefixe_facture || 'FA')
                    const apercu = String(valeur)
                      .replace(/\{numero\}/g, `${prefixeExemple}-${anneeExemple}-014`)
                      .replace(/\{tiers\}/g, 'SOCIÉTÉ ALPHA CONSULTING SARL')
                      .replace(/\{ref\}/g, `${form.prefixe_bl || 'BL'}-${anneeExemple}-003`)
                      .replace(/\{date\}/g, `26/07/${anneeExemple}`)
                      .replace(/\s+/g, ' ').trim()
                    return (
                      <div key={f.key} style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                        <label style={{ fontSize: 12, fontWeight: 500 }}>{f.label}</label>
                        <input
                          className={styles.input}
                          value={valeur}
                          placeholder={f.defaut}
                          onChange={e => majChamp(f.key, e.target.value)}
                        />
                        <span style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>
                          Aperçu (exemple) : <em>{apercu || '—'}</em>
                        </span>
                      </div>
                    )
                  })}
                </div>
                <div style={{ marginTop: 12, padding: 10, background: 'var(--bg-secondary)', borderRadius: 6, fontSize: 11, color: 'var(--text-secondary)' }}>
                  <i className="ti ti-info-circle" style={{ marginRight: 4 }} />
                  Variables disponibles : <strong>{'{numero}'}</strong> (n° du document),{' '}
                  <strong>{'{tiers}'}</strong> (client ou fournisseur),{' '}
                  <strong>{'{ref}'}</strong> (référence),{' '}
                  <strong>{'{date}'}</strong> (date du document).
                  Ces formats sont appliqués à la comptabilisation des factures, des avoirs et des règlements.
                  N'oubliez pas d'enregistrer.
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
