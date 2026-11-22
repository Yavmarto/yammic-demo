from sqlalchemy import text
from app.db import engine

PID = 'GBM-NL-004'
URL = f'/participants/{PID}/ecrf/AGE/manual'
BODY = {'value': '52', 'documentId': 'DOC-004-CLIN', 'evidence': 'LEEFTIJD BIJ DIAGNOSE: 52 jaar'}


def test_manual_entry_and_export(client, auth):
    nurse = auth('nurse')
    for body in ({**BODY, 'value': '500'}, {**BODY, 'evidence': ''},
                 {**BODY, 'evidence': 'invented'}, {**BODY, 'documentId': 'DOC-002-DIS'}):
        assert client.post(URL, json=body, headers=nurse).status_code in (404, 422)
    assert client.post(URL, json=BODY, headers=auth('monitor')).status_code == 403
    r = client.post(URL, json=BODY, headers=nurse)
    assert r.status_code == 201, r.text
    result = r.json()
    assert result['ecrfValue']['entrySource'] == 'human'
    assert result['extraction']['provider'] == 'human'
    assert result['extraction']['evidence'][0]['text'] == BODY['evidence']
    assert client.post(URL, json=BODY, headers=nurse).status_code == 409
    with engine.connect() as c:
        other = c.execute(text("SELECT id FROM extraction WHERE participant_id=:p AND field_id='AGE' AND provider <> 'human' LIMIT 1"), {'p': PID}).scalar()
    assert other is None  # The presenter case has no AI proposal.
    assert client.post('/participants/GBM-NL-001/ecrf/AGE/manual', json={**BODY, 'value': '57', 'documentId': 'DOC-001-DIS', 'evidence': 'LEEFTIJD BIJ DIAGNOSE: 57 jaar'}, headers=nurse).status_code == 201
    with engine.connect() as c:
        other = c.execute(text("SELECT id FROM extraction WHERE participant_id='GBM-NL-001' AND field_id='AGE' AND provider <> 'human' LIMIT 1")).scalar_one()
    assert client.post(f'/extractions/{other}/decision', json={'decision': 'accept'}, headers=nurse).status_code == 409
    bundle = client.get(f'/participants/{PID}/export/fhir', headers=auth('monitor')).json()
    resources = [e['resource'] for e in bundle['entry']]
    qr = next(x for x in resources if x['resourceType'] == 'QuestionnaireResponse')
    assert any(x['linkId'] == 'AGE' and x['answer'][0]['valueInteger'] == 52 for x in qr['item'])
    prov = next(x for x in resources if x['resourceType'] == 'Provenance')
    assert any(e['what']['identifier']['value'] == BODY['documentId'] for e in prov['entity'])
    assert any(a['role'][0]['text'] == 'human entry' for a in prov['agent'])
    assert any(x['resourceType'] == 'AuditEvent' and x['subtype'][0]['code'] == 'ecrf.value_set' for x in resources)

    odm = client.get('/studies/GBM-NL-2026-01/export/odm', headers=auth('monitor')).text
    assert 'Human entry by nurse; document DOC-004-CLIN; evidence: LEEFTIJD BIJ DIAGNOSE: 52 jaar' in odm
