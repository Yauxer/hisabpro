export function dateLocaleISO(date = new Date()) {
  const d = date instanceof Date ? date : new Date(date)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

export function nombreOuDefaut(value, fallback = 0) {
  if (value === '' || value === null || value === undefined) return fallback
  const n = Number(value)
  return Number.isFinite(n) ? n : fallback
}

export function entierOuDefaut(value, fallback = 0) {
  if (value === '' || value === null || value === undefined) return fallback
  const n = Number.parseInt(value, 10)
  return Number.isFinite(n) ? n : fallback
}

export function emailValide(value) {
  if (!value) return true
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(value).trim())
}

export function iceValide(value) {
  if (!value) return true
  return /^\d{15}$/.test(String(value).trim())
}

export function normaliserIceSaisie(value) {
  return String(value ?? '').replace(/[^0-9]/g, '').slice(0, 15)
}

export function normaliserIfSaisie(value) {
  return String(value ?? '').replace(/[^0-9]/g, '').slice(0, 20)
}

export function normaliserTpSaisie(value) {
  return String(value ?? '').toUpperCase().replace(/[^A-Z0-9 .\-/]/g, '').slice(0, 50)
}

export function ifValide(value) {
  if (!value) return true
  return /^\d{1,20}$/.test(String(value).trim())
}
