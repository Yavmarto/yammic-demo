import os
from sqlalchemy import text
from app.db import engine
from app.security import hash_password


def test_assignment_roles_reload_completion_and_audit(client, auth):
    with engine.begin() as c:
        if os.environ.get("TEST_SITE_ID"):
            assert c.execute(text("SELECT count(*) FROM site")).scalar_one() == 1
        c.execute(text("INSERT INTO app_user (username, display_name, role, password_hash) VALUES ('nurse2','Second demo reviewer','nurse',:p)"), {"p": hash_password('demo')})
    pi, nurse, other, monitor = (auth(x) for x in ('pi', 'nurse', 'nurse2', 'monitor'))
    path = '/extractions/EXT-0001/assignment'
    assignment = {'assignedTo': 'nurse', 'dueDate': '2026-12-01'}
    assert client.post(path, headers=nurse, json=assignment).status_code == 403
    assert client.post(path, headers=monitor, json=assignment).status_code == 403
    for who in ('monitor', 'pi', 'missing'):
        assert client.post(path, headers=pi, json={**assignment, 'assignedTo': who}).status_code == 422
    assert client.post(path, headers=pi, json={**assignment, 'dueDate': 'invalid'}).status_code == 422
    assert client.post(path, headers=pi, json=assignment).status_code == 200
    assignment['dueDate'] = '2026-12-02'
    assert client.post(path, headers=pi, json=assignment).status_code == 200
    item = next(x for x in client.get('/participants/GBM-NL-001/extractions', headers=nurse).json() if x['id'] == 'EXT-0001')
    assert (item['assignedTo'], item['dueDate'], item['reviewState']) == ('nurse', '2026-12-02', 'pending')
    assert client.post('/extractions/EXT-0001/decision', headers=other, json={'decision': 'defer'}).status_code == 403
    assert client.post('/extractions/EXT-0001/decision', headers=nurse, json={'decision': 'defer'}).json()['extraction']['reviewState'] == 'deferred'
    assert client.post(path, headers=pi, json={**assignment, 'assignedTo': 'nurse2'}).status_code == 200
    assert client.post('/extractions/EXT-0001/decision', headers=other, json={'decision': 'accept'}).json()['extraction']['reviewState'] == 'accepted'
    assert client.post(path, headers=pi, json=assignment).status_code == 409
    assert client.post('/extractions/EXT-0002/decision', headers=nurse, json={'decision': 'accept'}).status_code == 200
    events = client.get('/audit', params={'entityId': 'EXT-0001'}, headers=pi).json()['items']
    changes = [e for e in events if e['action'] == 'extraction.assignment']
    assert len(changes) == 3 and all(e['actor'] == 'pi' for e in changes)
    assert any(e['before']['dueDate'] == '2026-12-01' and e['after']['dueDate'] == '2026-12-02' for e in changes)
    assert client.get('/audit/verify', headers=pi).json()['ok']
