import React, { useEffect, useMemo, useRef, useState } from 'react'
import { tiersAPI } from '../services/api.js'

function normaliser(value) {
  return String(value || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim()
}

function typeAPI(type) {
  if (type === 'vente') return 'client'
  if (type === 'achat') return 'fournisseur'
  if (type === 'client' || type === 'fournisseur') return type
  return null
}

function libelleType(t) {
  if (t === 'client') return 'Client'
  if (t === 'fournisseur') return 'Fournisseur'
  if (t === 'les_deux' || t === 'client_fournisseur' || t === 'les deux') return 'Client · Fournisseur'
  return t || 'Tiers'
}

function compteTiers(t, contexte) {
  if (!t) return ''
  if (contexte === 'client' || contexte === 'vente') return t.compte_client || ''
  if (contexte === 'fournisseur' || contexte === 'achat') return t.compte_fournisseur || ''
  return t.compte_client || t.compte_fournisseur || ''
}

export default function TiersPicker({
  value = '',
  onChange,
  onSelect,
  type = 'tous',
  placeholder,
  disabled = false,
  allowCreate = false,
  onCreate,
  emptyLabel = 'Aucun tiers trouvé',
}) {
  const [liste, setListe] = useState([])
  const [ouvert, setOuvert] = useState(false)
  const [loading, setLoading] = useState(false)
  const [indexActif, setIndexActif] = useState(-1)
  const [erreur, setErreur] = useState('')
  const ref = useRef(null)
  const inputRef = useRef(null)
  const contexte = typeAPI(type)

  useEffect(() => {
    let actif = true
    setLoading(true)
    setErreur('')
    tiersAPI.lister({ type: contexte || undefined, limit: 300 })
      .then(data => {
        if (!actif) return
        const map = new Map()
        ;(Array.isArray(data) ? data : []).forEach(t => map.set(t.id, t))
        setListe([...map.values()])
      })
      .catch(() => { if (actif) { setListe([]); setErreur('Impossible de charger les tiers') } })
      .finally(() => { if (actif) setLoading(false) })
    return () => { actif = false }
  }, [contexte])

  useEffect(() => {
    function fermer(e) {
      if (ref.current && !ref.current.contains(e.target)) {
        setOuvert(false)
        setIndexActif(-1)
      }
    }
    document.addEventListener('mousedown', fermer)
    return () => document.removeEventListener('mousedown', fermer)
  }, [])

  const resultats = useMemo(() => {
    const q = normaliser(value)
    const tries = [...liste].sort((a, b) => String(a.nom || '').localeCompare(String(b.nom || ''), 'fr'))
    if (!q) return tries.slice(0, 14)
    return tries.filter(t => {
      const compte = compteTiers(t, type)
      return [t.nom, t.ice, compte, t.compte_client, t.compte_fournisseur, t.ville, t.telephone]
        .some(x => normaliser(x).includes(q))
    }).slice(0, 14)
  }, [liste, value, type])

  const exact = useMemo(() => {
    const q = normaliser(value)
    return q ? liste.find(t => normaliser(t.nom) === q) || null : null
  }, [liste, value])

  const peutCreer = allowCreate && typeof onCreate === 'function' && value.trim().length > 2 && !exact

  function choisir(t) {
    onChange?.(t.nom)
    onSelect?.(t)
    setOuvert(false)
    setIndexActif(-1)
  }

  async function creer() {
    if (!peutCreer) return
    try {
      const nouveau = await onCreate(value.trim())
      if (!nouveau) return
      setListe(prev => [...prev.filter(t => t.id !== nouveau.id), nouveau])
      choisir(nouveau)
    } catch (e) {
      setErreur(e?.message || 'Création impossible')
    }
  }

  function handleChange(val) {
    onChange?.(val)
    onSelect?.(null)
    setOuvert(true)
    setIndexActif(-1)
    setErreur('')
  }

  function handleKeyDown(e) {
    if (disabled) return
    const total = resultats.length + (peutCreer ? 1 : 0)
    if (e.key === 'ArrowDown') {
      e.preventDefault(); setOuvert(true)
      setIndexActif(i => total ? (i + 1) % total : -1)
    } else if (e.key === 'ArrowUp') {
      e.preventDefault(); setOuvert(true)
      setIndexActif(i => total ? (i <= 0 ? total - 1 : i - 1) : -1)
    } else if (e.key === 'Enter' && ouvert && indexActif >= 0) {
      e.preventDefault()
      if (indexActif < resultats.length) choisir(resultats[indexActif])
      else creer()
    } else if (e.key === 'Escape') {
      setOuvert(false); setIndexActif(-1)
    }
  }

  const placeholderFinal = placeholder || (contexte === 'fournisseur'
    ? 'Rechercher un fournisseur : nom, ICE, compte…'
    : contexte === 'client'
      ? 'Rechercher un client : nom, ICE, compte…'
      : 'Rechercher un tiers : nom, ICE, compte…')

  return (
    <div className={`hp-tiers-picker ${ouvert ? 'is-open' : ''}`} ref={ref}>
      <div className={`hp-tiers-picker__control ${ouvert ? 'is-open' : ''}`}>
        <i className="ti ti-search hp-tiers-picker__search" aria-hidden="true" />
        <input
          ref={inputRef}
          type="text"
          value={value}
          disabled={disabled}
          placeholder={placeholderFinal}
          autoComplete="off"
          role="combobox"
          aria-expanded={ouvert}
          aria-autocomplete="list"
          onChange={e => handleChange(e.target.value)}
          onFocus={() => { if (!disabled) setOuvert(true) }}
          onKeyDown={handleKeyDown}
        />
        {value && !disabled && (
          <button type="button" className="hp-tiers-picker__clear" title="Effacer"
            onMouseDown={e => e.preventDefault()}
            onClick={() => { handleChange(''); inputRef.current?.focus() }}>
            <i className="ti ti-x" aria-hidden="true" />
          </button>
        )}
        <i className={`ti ti-chevron-down hp-tiers-picker__chevron ${ouvert ? 'is-open' : ''}`} aria-hidden="true" />
      </div>

      {ouvert && !disabled && (
        <div className="hp-tiers-picker__menu" role="listbox">
          <div className="hp-tiers-picker__menu-head">
            <span>{contexte === 'client' ? 'Clients' : contexte === 'fournisseur' ? 'Fournisseurs' : 'Clients & fournisseurs'}</span>
            <small>{loading ? 'Chargement…' : `${resultats.length}${resultats.length === 14 ? '+' : ''} résultat${resultats.length !== 1 ? 's' : ''}`}</small>
          </div>

          {erreur && <div className="hp-tiers-picker__empty hp-tiers-picker__empty--error"><i className="ti ti-alert-circle" /> {erreur}</div>}

          {!loading && !erreur && resultats.length === 0 && (
            <div className="hp-tiers-picker__empty">
              <i className="ti ti-user-search" aria-hidden="true" />
              <strong>{emptyLabel}</strong>
              <span>Recherche possible par nom, ICE, compte ou ville.</span>
            </div>
          )}

          {resultats.map((t, idx) => {
            const compte = compteTiers(t, type)
            const details = [compte ? `Compte ${compte}` : null, t.ice ? `ICE ${t.ice}` : null, t.ville || null].filter(Boolean)
            return (
              <button
                key={t.id}
                type="button"
                role="option"
                aria-selected={indexActif === idx}
                className={`hp-tiers-picker__item ${indexActif === idx ? 'is-active' : ''}`}
                onMouseEnter={() => setIndexActif(idx)}
                onMouseDown={e => e.preventDefault()}
                onClick={() => choisir(t)}>
                <span className="hp-tiers-picker__avatar"><i className={`ti ${contexte === 'fournisseur' ? 'ti-building-store' : 'ti-user'}`} /></span>
                <span className="hp-tiers-picker__identity">
                  <strong>{t.nom}</strong>
                  <small>{details.length ? details.join(' · ') : 'Aucune information complémentaire'}</small>
                </span>
                <span className="hp-tiers-picker__badge">{libelleType(t.type)}</span>
              </button>
            )
          })}

          {peutCreer && (
            <button type="button"
              className={`hp-tiers-picker__create ${indexActif === resultats.length ? 'is-active' : ''}`}
              onMouseEnter={() => setIndexActif(resultats.length)}
              onMouseDown={e => e.preventDefault()}
              onClick={creer}>
              <span className="hp-tiers-picker__create-icon"><i className="ti ti-plus" /></span>
              <span><strong>Créer « {value.trim()} »</strong><small>Créer rapidement ce {contexte === 'fournisseur' ? 'fournisseur' : 'client'}</small></span>
              <i className="ti ti-arrow-right" aria-hidden="true" />
            </button>
          )}
        </div>
      )}
    </div>
  )
}
