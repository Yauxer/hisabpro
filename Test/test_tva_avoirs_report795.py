"""Le report conserve les soldes signés déjà issus des factures/avoirs éligibles."""
from decimal import Decimal as D
import pytest
from services.tva_service import appliquer_credit_periode

@pytest.mark.parametrize('credit,collectee,recuperable,due,report',[
 ('1800','-500','2400','0','4700'),
 ('4700','3000','2400','0','4100'),
 ('50','100','-200','250','0'),
 ('100','-500','-200','0','400'),
 ('0','0','-80','80','0'),
])
def test_795_report_nets_signes_avoirs(credit,collectee,recuperable,due,report):
 r=appliquer_credit_periode(D(credit),D(collectee),D(recuperable));assert r=={'tva_due':D(due),'credit_fin':D(report)}
