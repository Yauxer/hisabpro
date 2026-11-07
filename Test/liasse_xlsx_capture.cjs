// Banc Node : sérialiseur de production réel ; seule la destination DOM est remplacée.
const { readFileSync } = require('node:fs');
const assert = require('node:assert/strict');
const source = readFileSync('src/services/exportXlsxLogo.js', 'utf8').replaceAll('export ', '');
const construire = new Function(source + '; return construireXlsxAvecLogo;')();

function capturerXlsx() {
  let bytes, nom, appels = 0;
  return {
    telecharger(XLSX, workbook, filename, societe) {
      bytes = construire(XLSX, workbook, societe);
      nom = filename;
      appels++;
    },
    lire() {
      assert.equal(appels, 1, 'Un téléchargement attendu par export');
      assert.ok(bytes && bytes.byteLength > 0, 'Classeur sérialisé attendu');
      return bytes;
    },
    nom() { return nom; },
  };
}
module.exports = { capturerXlsx };
