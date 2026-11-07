from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JOURNAL = ROOT / "src" / "pages" / "Journal.jsx"


def source():
    return JOURNAL.read_text(encoding="utf-8")


def test_fec_bloquant_ouvre_un_diagnostic_exhaustif():
    s = source()
    assert "const [fecControle, setFecControle] = useState(null)" in s
    assert "setFecControle(apercu)" in s
    assert "La liste ci-dessous est exhaustive : aucune anomalie n’est masquée." in s
    assert "(fecControle.bloquants || []).map" in s
    assert ".slice(0, 8)" not in s
    assert "… ${(apercu.bloquants || []).length - 8} autre(s) anomalie(s)" not in s


def test_diagnostic_affiche_identifiants_et_contexte_ecriture():
    s = source()
    assert "a.code || 'ANOMALIE'" in s
    assert "a.numero_ecriture" in s
    assert "a.ecriture_id" in s
    assert "a.details?.compte" in s
    assert "ecriture?.libelle" in s
    assert "ecritures.find" in s
