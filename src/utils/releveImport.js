// Contrat de relevé explicite, identique pour Excel et CSV. Aucune date valeur
// n'est utilisée comme date d'opération et aucune ligne invalide n'est omise.
const normaliser = valeur => String(valeur ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g, '')
  .replace(/^\uFEFF/, '').trim().toLowerCase().replace(/\s+/g, ' ')
const vide = valeur => valeur == null || String(valeur).trim() === ''
const ALIAS = {
  date: ['date', 'date operation', "date d'operation", 'date opération'],
  libelle: ['libelle', 'description', 'operation'],
  debit: ['debit', 'd'], credit: ['credit', 'c'], montant: ['montant'], sens: ['sens'],
}

function colonnes(row) {
  const resultat = {}
  row.forEach((valeur, index) => {
    const titre = normaliser(valeur)
    for (const [champ, aliases] of Object.entries(ALIAS)) {
      if (!aliases.includes(titre)) continue
      if (champ in resultat) throw new Error(`Plusieurs colonnes ${champ} : choisissez une seule colonne explicite.`)
      resultat[champ] = index
    }
  })
  return resultat
}

export function montantReleve(valeur, { signe = false } = {}) {
  if (typeof valeur === 'boolean' || (typeof valeur === 'number' && !Number.isFinite(valeur))) {
    throw new Error('Montant invalide : nombre fini attendu.')
  }
  const texte = String(valeur ?? '').trim().replace(/[\u00a0\u202f]/g, ' ')
  // Groupement français explicite : 1 234,56. Le point est également accepté
  // comme séparateur décimal, mais une ponctuation ambiguë est refusée.
  const format = signe
    ? /^[+-]?(?:\d+|\d{1,3}(?: \d{3})+)(?:[.,]\d{1,2})?$/
    : /^\+?(?:\d+|\d{1,3}(?: \d{3})+)(?:[.,]\d{1,2})?$/
  if (!format.test(texte)) throw new Error('Montant invalide : utilisez 1234,56 ou 1 234,56, avec au plus deux décimales.')
  const nombre = Number(texte.replace(/ /g, '').replace(',', '.'))
  if (!Number.isFinite(nombre) || !Number.isSafeInteger(Math.round(nombre * 100))) {
    throw new Error('Montant trop grand pour garantir les centimes.')
  }
  return nombre
}

export function dateReleve(valeur) {
  let annee, mois, jour
  if (valeur instanceof Date) {
    if (!Number.isFinite(valeur.getTime())) throw new Error('Date invalide.')
    // Les dates Excel décrivent un jour civil, indépendamment du fuseau UTC.
    annee = valeur.getFullYear(); mois = valeur.getMonth() + 1; jour = valeur.getDate()
  } else {
    const texte = String(valeur ?? '').trim()
    let match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(texte)
    if (match) { annee = Number(match[1]); mois = Number(match[2]); jour = Number(match[3]) }
    else {
      match = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/.exec(texte)
      if (!match) throw new Error('Date invalide : utilisez JJ/MM/AAAA ou AAAA-MM-JJ.')
      jour = Number(match[1]); mois = Number(match[2]); annee = Number(match[3])
    }
  }
  const controle = new Date(Date.UTC(annee, mois - 1, jour))
  if (annee < 1900 || annee > 9999 || controle.getUTCFullYear() !== annee
      || controle.getUTCMonth() + 1 !== mois || controle.getUTCDate() !== jour) throw new Error('Date inexistante.')
  return `${annee}-${String(mois).padStart(2, '0')}-${String(jour).padStart(2, '0')}`
}

export function lignesDepuisTableauReleve(rows) {
  let indexEntete = -1, champs
  for (let i = 0; i < Math.min(rows.length, 10); i++) {
    const trouves = colonnes(rows[i])
    if (trouves.date == null) continue
    if (trouves.montant == null && trouves.debit == null && trouves.credit == null) continue
    indexEntete = i; champs = trouves; break
  }
  if (indexEntete < 0) throw new Error('En-tête introuvable : Date et Débit/Crédit ou Montant requis. Date valeur seule ne suffit pas.')
  const parColonnes = champs.debit != null || champs.credit != null
  if (parColonnes && (champs.debit == null || champs.credit == null || champs.montant != null)) {
    throw new Error('Choisissez les deux colonnes Débit/Crédit ou la colonne Montant, sans mélanger les formats.')
  }
  const resultat = []
  for (let i = indexEntete + 1; i < rows.length; i++) {
    const row = rows[i]
    if (!row || row.every(vide)) continue
    try {
      const date = dateReleve(row[champs.date])
      let montant, sens
      if (parColonnes) {
        const debit = vide(row[champs.debit]) ? 0 : montantReleve(row[champs.debit])
        const credit = vide(row[champs.credit]) ? 0 : montantReleve(row[champs.credit])
        if ((debit > 0) === (credit > 0)) throw new Error('Une seule colonne Débit ou Crédit doit porter un montant positif.')
        montant = debit || credit; sens = debit > 0 ? 'debit' : 'credit'
      } else if (champs.sens != null) {
        const valeurSens = normaliser(row[champs.sens])
        sens = { debit: 'debit', d: 'debit', credit: 'credit', c: 'credit' }[valeurSens]
        if (!sens) throw new Error('Sens invalide : Débit ou Crédit attendu.')
        montant = montantReleve(row[champs.montant])
      } else {
        const signe = montantReleve(row[champs.montant], { signe: true })
        montant = Math.abs(signe); sens = signe < 0 ? 'debit' : 'credit'
      }
      if (!(montant > 0)) throw new Error('Le montant doit être strictement positif.')
      resultat.push({ date, libelle: champs.libelle == null ? '' : String(row[champs.libelle] ?? '').trim(), montant, sens })
    } catch (erreur) { throw new Error(`Ligne ${i + 1} : ${erreur.message}`) }
  }
  if (!resultat.length) throw new Error('Aucune opération dans le fichier.')
  return resultat
}

function decouperCsv(texte, separateur) {
  const rows = [], row = []
  let cellule = '', dansGuillemets = false, ferme = false
  const ajouter = () => { row.push(cellule); cellule = ''; ferme = false }
  for (let i = 0; i < texte.length; i++) {
    const c = texte[i]
    if (dansGuillemets) {
      if (c === '"' && texte[i + 1] === '"') { cellule += '"'; i++ }
      else if (c === '"') { dansGuillemets = false; ferme = true }
      else cellule += c
    } else if (c === '"') {
      if (cellule || ferme) throw new Error('Guillemets CSV invalides.')
      dansGuillemets = true
    } else if (c === separateur) ajouter()
    else if (c === '\n' || c === '\r') {
      ajouter(); rows.push([...row]); row.length = 0
      if (c === '\r' && texte[i + 1] === '\n') i++
    } else {
      if (ferme) throw new Error('Caractère inattendu après les guillemets CSV.')
      cellule += c
    }
  }
  if (dansGuillemets) throw new Error('Guillemets CSV non fermés.')
  if (cellule || ferme || row.length) { ajouter(); rows.push([...row]) }
  return rows
}

export function tableauDepuisCsv(texte) {
  texte = String(texte).replace(/^\uFEFF/, '')
  const directive = /^sep=([;,\t])\r?\n/i.exec(texte)
  if (directive) return decouperCsv(texte.slice(directive[0].length), directive[1])
  const candidats = []
  for (const sep of [';', ',', '\t']) {
    try {
      const rows = decouperCsv(texte, sep)
      const reconnaissable = rows.slice(0, 10).some(row => {
        const c = colonnes(row)
        return c.date != null && (c.montant != null || c.debit != null || c.credit != null)
      })
      if (reconnaissable) candidats.push(rows)
    } catch { /* Le séparateur candidat ne produit pas de CSV exploitable. */ }
  }
  if (candidats.length !== 1) throw new Error('CSV non reconnu : séparateur point-virgule, virgule ou tabulation avec en-tête explicite requis.')
  return candidats[0]
}

export function decoderCsv(buffer) {
  try { return new TextDecoder('utf-8', { fatal: true }).decode(buffer) }
  catch { return new TextDecoder('windows-1252').decode(buffer) }
}
