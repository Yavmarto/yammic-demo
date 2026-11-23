import copy
import hashlib
import json
from pathlib import Path

import pytest

from app.export.sdtm_offline import export

FIXTURE = Path(__file__).parents[1] / 'fixtures/sdtm/fictional_weight.json'


def test_selection_mapping_and_stable_checksum():
    data = json.loads(FIXTURE.read_text())
    csv, sidecar = export(data)
    assert csv.decode().splitlines() == [
        'STUDYID,DOMAIN,USUBJID,VSSEQ,VSTESTCD,VSTEST,VSORRES,VSORRESU,VSSTRESC,VSSTRESN,VSSTRESU,VSDTC',
        'SYNTH01,VS,SYNTH01-P01,1,WEIGHT,Weight,70.50,kg,70.5,70.5,kg,2026-01-02',
    ]
    provenance = json.loads(sidecar)
    assert provenance['csv_sha256'] == hashlib.sha256(csv).hexdigest()
    assert provenance['records'] == [{'USUBJID': 'SYNTH01-P01', 'VSSEQ': 1, 'source_id': 'document1', 'verified_by': 'reviewer1'}]
    assert export(data) == (csv, sidecar)
    data['rows'].reverse()
    assert export(data) == (csv, sidecar)


@pytest.mark.parametrize('change', [
    lambda d: d.update(fictional=False),
    lambda d: d['rows'][0].update(checked='true'),
    lambda d: d['rows'][0].update(unit='lb'),
    lambda d: d['rows'][0].update(value='NaN'),
    lambda d: d['rows'][0].update(date='2026-02-30'),
    lambda d: d['rows'][0].update(source_id=''),
    lambda d: d['rows'].append(copy.deepcopy(d['rows'][0])),
])
def test_invalid_inputs_fail_closed(change):
    data = json.loads(FIXTURE.read_text())
    change(data)
    with pytest.raises(ValueError):
        export(data)
