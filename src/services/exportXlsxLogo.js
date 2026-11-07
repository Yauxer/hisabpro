// Logo OOXML avec le ZIP de SheetJS déjà installé ; cellules sources conservées.
const NS_REL = 'http://schemas.openxmlformats.org/package/2006/relationships'
const NS_DOC = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'

function lireLogo(value) {
  if (typeof value !== 'string' || value.length > 512 * 1024 * 4 / 3 + 40) return null
  const match = /^data:image\/(png|jpeg);base64,([A-Za-z0-9+/]+={0,2})$/.exec(value)
  if (!match) return null
  try {
    const raw = Uint8Array.from(atob(match[2]), c => c.charCodeAt(0))
    if (raw.length > 512 * 1024) return null
    const view = new DataView(raw.buffer)
    let width, height
    if (match[1] === 'png') {
      if (raw.length < 33 || view.getUint32(0) !== 0x89504e47 || view.getUint32(4) !== 0x0d0a1a0a || view.getUint32(12) !== 0x49484452) return null
      width = view.getUint32(16); height = view.getUint32(20)
    } else {
      if (view.getUint16(0) !== 0xffd8) return null
      for (let offset = 2; offset + 8 < raw.length;) {
        if (raw[offset++] !== 0xff) return null
        while (raw[offset] === 0xff) offset++
        const marker = raw[offset++]
        if (marker === 0xda || marker === 0xd9) break
        const length = view.getUint16(offset)
        if (length < 2 || offset + length > raw.length) return null
        if ([0xc0, 0xc1, 0xc2].includes(marker)) {
          height = view.getUint16(offset + 3); width = view.getUint16(offset + 5); break
        }
        offset += length
      }
    }
    if (!width || !height || width * height > 4000000) return null
    const ratio = Math.min(240 / width, 120 / height)
    return { raw, ext: match[1], cx: Math.round(width * ratio * 9525), cy: Math.round(height * ratio * 9525) }
  } catch { return null }
}

export function construireXlsxAvecLogo(XLSX, workbook, societe) {
  const logo = lireLogo(societe?.logo_url)
  const copie = structuredClone(workbook)
  if (!logo) return XLSX.write(copie, { type: 'array', bookType: 'xlsx' })
  // Une feuille d'identité évite de décaler les cellules comptables existantes.
  let nom = 'Logo société', index = 1
  while (copie.SheetNames.includes(nom)) nom = `Logo société ${++index}`
  const feuille = XLSX.utils.aoa_to_sheet([['Logo de la société'], [String(societe?.raison_sociale || '')]])
  feuille['!cols'] = [{ wch: 45 }]
  XLSX.utils.book_append_sheet(copie, feuille, nom)
  copie.SheetNames = [nom, ...copie.SheetNames.filter(n => n !== nom)]
  const zip = XLSX.CFB.read(new Uint8Array(XLSX.write(copie, { type: 'array', bookType: 'xlsx' })), { type: 'array' })
  const encoder = new TextEncoder(), decoder = new TextDecoder()
  const ajouter = (path, data) => XLSX.CFB.utils.cfb_add(zip, path, typeof data === 'string' ? encoder.encode(data) : data)
  const lire = path => decoder.decode(XLSX.CFB.find(zip, '/' + path).content)
  const relations = contenu => `<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="${NS_REL}">${contenu}</Relationships>`
  ajouter('xl/media/hisabpro-logo.' + logo.ext, logo.raw)
  ajouter('xl/worksheets/sheet1.xml', lire('xl/worksheets/sheet1.xml').replace('</worksheet>', `<drawing xmlns:r="${NS_DOC}" r:id="rIdLogo"/></worksheet>`))
  ajouter('xl/worksheets/_rels/sheet1.xml.rels', relations(`<Relationship Id="rIdLogo" Type="${NS_DOC}/drawing" Target="../drawings/hisabpro-logo.xml"/>`))
  ajouter('xl/drawings/_rels/hisabpro-logo.xml.rels', relations(`<Relationship Id="rIdImage" Type="${NS_DOC}/image" Target="../media/hisabpro-logo.${logo.ext}"/>`))
  ajouter('xl/drawings/hisabpro-logo.xml', `<?xml version="1.0" encoding="UTF-8"?><xdr:wsDr xmlns:xdr="http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><xdr:oneCellAnchor><xdr:from><xdr:col>0</xdr:col><xdr:colOff>0</xdr:colOff><xdr:row>3</xdr:row><xdr:rowOff>0</xdr:rowOff></xdr:from><xdr:ext cx="${logo.cx}" cy="${logo.cy}"/><xdr:pic><xdr:nvPicPr><xdr:cNvPr id="1" name="Logo de la société"/><xdr:cNvPicPr/></xdr:nvPicPr><xdr:blipFill><a:blip xmlns:r="${NS_DOC}" r:embed="rIdImage"/><a:stretch><a:fillRect/></a:stretch></xdr:blipFill><xdr:spPr><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></xdr:spPr></xdr:pic><xdr:clientData/></xdr:oneCellAnchor></xdr:wsDr>`)
  const types = lire('[Content_Types].xml')
  const imageType = types.includes(`Extension="${logo.ext}"`) ? '' : `<Default Extension="${logo.ext}" ContentType="image/${logo.ext}"/>`
  ajouter('[Content_Types].xml', types.replace('</Types>', `${imageType}<Override PartName="/xl/drawings/hisabpro-logo.xml" ContentType="application/vnd.openxmlformats-officedocument.drawing+xml"/></Types>`))
  return XLSX.CFB.write(zip, { type: 'array', fileType: 'zip' })
}

export function telechargerXlsxAvecLogo(XLSX, workbook, filename, societe) {
  const bytes = construireXlsxAvecLogo(XLSX, workbook, societe)
  const url = URL.createObjectURL(new Blob([bytes], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' }))
  const a = document.createElement('a')
  try {
    a.href = url; a.download = filename; document.body.appendChild(a); a.click()
  } finally {
    a.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000)
  }
}
