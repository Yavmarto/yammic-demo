from concurrent.futures import ThreadPoolExecutor
from app.ai import service
from app.ai.types import ProviderError


def test_failed_retry_completion_and_race(client, auth, monkeypatch):
    nurse, monitor, ai = auth('nurse'), auth('monitor'), auth('ai')
    pid, doc = 'GBM-NL-001', 'DOC-001-PATH'
    proposals = client.get(f'/participants/{pid}/extractions', headers=nurse).json()
    kps = next(x for x in proposals if x['field'] == 'KPS' and x['status'] == 'proposed')
    decision = client.post(f"/extractions/{kps['id']}/decision", json={'decision': 'correct', 'correctedValue': '80', 'reason': 'Synthetic review'}, headers=nurse)
    assert decision.status_code == 200
    before = client.get(f'/participants/{pid}/ecrf', headers=nurse).json()
    assert any(f['id'] == 'KPS' and f['value'] is not None for f in before['fields'])
    created = client.post(f'/participants/{pid}/extract?provider=rules', json={'documentId': doc}, headers=nurse).json()
    class Api:
        def get_document(self, d): return client.get(f'/documents/{d}', headers=ai).json()
        def ecrf_fields(self, p): return client.get(f'/participants/{p}/ecrf', headers=ai).json()['fields']
        def update_run(self, i, data):
            res = client.patch(f'/runs/{i}', json=data, headers=ai)
            assert res.status_code == 200, res.text
            return res.json()
        def post_extractions(self, i, data):
            res = client.post(f'/runs/{i}/extractions', json=data, headers=ai)
            assert res.status_code == 201, res.text
            return res.json()
    real_provider = service.providers.get_provider
    class Failing:
        name, model = 'rules', 'simulated'
        def available(self): return True, None
        def extract(self, *args, **kwargs): raise ProviderError('sensitive simulated failure')
    monkeypatch.setattr(service.providers, 'get_provider', lambda _: Failing())
    assert service.process_run(Api(), created, provider='rules')['status'] == 'failed'
    monkeypatch.setattr(service.providers, 'get_provider', real_provider)
    listed = client.get(f'/runs?participant_id={pid}', headers=nurse)
    assert listed.status_code == 200
    assert any(r['id'] == created['id'] and r['status'] == 'failed' for r in listed.json())
    url = f"/runs/{created['id']}/retry"
    assert client.post(url, headers=monitor).status_code == 403
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: client.post(url, headers=nurse), range(2)))
    assert all(r.status_code == 200 for r in results)
    retry = results[0].json()
    assert results[1].json()['id'] == retry['id']
    assert (retry['participantId'], retry['documentId'], retry['retryOfRunId']) == (pid, doc, created['id'])
    assert service.process_run(Api(), retry, provider='rules')['status'] == 'completed'
    assert client.get(f"/runs/{created['id']}", headers=nurse).json()['status'] == 'failed'
    assert client.post(url, headers=nurse).json()['id'] == retry['id']
    after = client.get(f'/participants/{pid}/ecrf', headers=nurse).json()
    assert {f['id']: f['value'] for f in after['fields']} == {f['id']: f['value'] for f in before['fields']}
    events = client.get('/audit', headers=nurse).json()['items']
    assert any(e['action'] == 'run.retry_requested' and e['actor'] == 'nurse' and e['after']['originalRunId'] == created['id'] for e in events)
