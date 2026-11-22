import json
import sqlite3

from app.writeback import LocalReceiver, TemporaryReceiverError


def test_synthetic_api_retry_roles_and_unavailable(client, auth, tmp_path, monkeypatch):
    path = tmp_path / 'receiver.sqlite'
    url = '/participants/GBM-NL-001/export/synthetic-writeback'
    monitor, nurse = auth('monitor'), auth('nurse')
    assert client.get(url, headers=monitor).status_code == 503
    monkeypatch.setenv('YAMICC_SYNTHETIC_WRITEBACK', '1')
    monkeypatch.setenv('YAMICC_SYNTHETIC_RECEIVER_PATH', str(path))
    assert client.get(url, headers=nurse).status_code == 403
    assert client.post(url, json={'deliveryId': 'x'}, headers=nurse).status_code == 403
    assert not path.exists()
    assert client.get('/participants/other/export/synthetic-writeback', headers=monitor).status_code == 422
    proposals = client.get('/participants/GBM-NL-001/extractions', headers=nurse).json()
    kps = next(x for x in proposals if x['field'] == 'KPS' and x['status'] == 'proposed')
    assert client.post(f"/extractions/{kps['id']}/decision", json={'decision': 'correct', 'correctedValue': '80', 'reason': 'Synthetic review'}, headers=nurse).status_code == 200
    preview = client.get(url, headers=monitor).json()
    assert preview['value'] == '80' and preview['source_id'] == kps['documentId']
    assert preview['destination_field'] == 'performance.karnofsky'
    request = {'deliveryId': preview['deliveryId']}
    assert client.post(url, json={'deliveryId': 'stale'}, headers=monitor).status_code == 409
    original = LocalReceiver.receive
    def lost(self, delivery_id, payload, **kwargs):
        original(self, delivery_id, payload, fail_after_commit=True)
    monkeypatch.setattr(LocalReceiver, 'receive', lost)
    assert client.post(url, json=request, headers=monitor).status_code == 503
    monkeypatch.setattr(LocalReceiver, 'receive', original)
    result = client.post(url, json=request, headers=monitor)
    assert result.status_code == 200 and result.json()['outcome'] == 'delivered'
    with sqlite3.connect(path) as db:
        rows = db.execute('select delivery_id, payload from deliveries').fetchall()
    assert len(rows) == 1 and rows[0][0] == preview['deliveryId']
    assert json.loads(rows[0][1])['value'] == '80'
    monkeypatch.setenv('YAMICC_SYNTHETIC_RECEIVER_PATH', str(tmp_path / 'missing' / 'receiver.sqlite'))
    assert client.post(url, json=request, headers=monitor).status_code == 503
    assert client.get('/studies/GBM-NL-2026-01/export/odm', headers=monitor).status_code == 200
