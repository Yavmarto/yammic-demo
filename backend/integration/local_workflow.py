"""Destructive only to uniquely named, disposable Docker containers; synthetic data only."""
import json, os, socket, sqlite3, subprocess, tempfile, time, urllib.request, uuid
from pathlib import Path
from lxml import etree
from app.ai.client import HttpApiClient
from app.ai.service import process_run

ROOT = Path(__file__).resolve().parents[2]
PID, DOC = 'GBM-NL-001', 'DOC-001-DIS'

def cmd(*args, **kw):
    return subprocess.run(args, check=True, **kw)

def port():
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]

def wait(fn, seconds=240):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        try:
            return fn()
        except Exception:
            time.sleep(2)
    raise TimeoutError(f'service not ready after {seconds}s')

def raw(url, data=None, token=None):
    headers = {'Content-Type': 'application/json'}
    if token: headers['Authorization'] = 'Bearer ' + token
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data is not None else None, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as response: return response.read()

def main():
    ident = 'cel1855-' + uuid.uuid4().hex[:10]
    network, pg, hapi = ident, ident+'-pg', ident+'-hapi'
    pgport, fhirport, apiport = port(), port(), port()
    server = None
    with tempfile.TemporaryDirectory(prefix='cel1855-', dir=os.environ.get('PAPERCLIP_RUN_SCRATCH_DIR')) as temp:
        env = os.environ.copy()
        env.update(DATABASE_URL=f'postgresql+psycopg://yamicc:synthetic@127.0.0.1:{pgport}/yamicc',
                   JWT_SECRET='local-synthetic-jwt-'+'x'*32, PSEUDONYM_KEY='local-synthetic-pseudo-'+'x'*32,
                   AUDIT_KEY='local-synthetic-audit-'+'x'*32, AUDIT_ANCHOR=temp+'/audit.log',
                   FHIR_BASE_URL=f'http://127.0.0.1:{fhirport}/fhir', YAMICC_SYNTHETIC_WRITEBACK='1',
                   YAMICC_SYNTHETIC_RECEIVER_PATH=temp+'/receiver.sqlite')
        try:
            cmd('docker','network','create',network, stdout=subprocess.DEVNULL)
            cmd('docker','run','-d','--pull=never','--name',pg,'--network',network,'-p',f'127.0.0.1:{pgport}:5432',
                '-e','POSTGRES_USER=yamicc','-e','POSTGRES_PASSWORD=synthetic','-e','POSTGRES_DB=yamicc',
                'postgres:16', stdout=subprocess.DEVNULL)
            wait(lambda: cmd('docker','exec',pg,'pg_isready','-U','yamicc',stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL), 60)
            cmd('docker','exec',pg,'createdb','-U','yamicc','hapi')
            cmd('docker','run','-d','--pull=never','--name',hapi,'--network',network,'-p',f'127.0.0.1:{fhirport}:8080',
                '-e',f'spring.datasource.url=jdbc:postgresql://{pg}:5432/hapi', '-e','spring.datasource.username=yamicc',
                '-e','spring.datasource.password=synthetic','-e','spring.datasource.driverClassName=org.postgresql.Driver',
                '-e','spring.jpa.properties.hibernate.dialect=org.hibernate.dialect.PostgreSQLDialect', '-e','hapi.fhir.fhir_version=R4','-e','JAVA_TOOL_OPTIONS=-Xmx1024m','hapiproject/hapi:latest',stdout=subprocess.DEVNULL)
            print('Waiting for isolated HAPI...', flush=True)
            wait(lambda: raw(env['FHIR_BASE_URL']+'/metadata'), 300)
            for name in ('shared/codesystems.json', 'baseline/organizations.json', 'baseline/patient-GBM-NL-001.json'):
                bundle=json.loads((ROOT/'fhir-seed'/name).read_text())
                try: raw(env['FHIR_BASE_URL'], bundle)
                except urllib.error.HTTPError as exc: raise RuntimeError(f'{name}: {exc.read().decode()}') from exc
            # Keep seeded study, sites and users, but force participant 001 and its documents to arrive via HAPI.
            seed = '''from app import seed\nfrom app.db import migrate\norig=seed.J\ndef filtered(name):\n d=orig(name)\n if name=="participants.json": d["participants"]=[x for x in d["participants"] if x["id"]!="GBM-NL-001"]\n if name=="documents.json": d["documents"]=[x for x in d["documents"] if x["participantId"]!="GBM-NL-001"]\n return d\nseed.J=filtered\nmigrate()\nseed.load()\n'''
            cmd(os.sys.executable,'-c',seed,cwd=ROOT/'backend',env=env)
            server=subprocess.Popen([os.sys.executable,'-m','uvicorn','app.main:app','--host','127.0.0.1','--port',str(apiport)],cwd=ROOT/'backend',env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            base=f'http://127.0.0.1:{apiport}'
            wait(lambda: raw(base+'/openapi.json'), 30)
            nurse=HttpApiClient(base,'nurse'); monitor=HttpApiClient(base,'monitor'); ai=HttpApiClient(base,'ai')
            sync=nurse.post('/integrations/fhir/hospital-1/sync',{})
            assert sync['status']=='completed' and sync['counts']['participants']['created']==1 and sync['counts']['documents']['created'] >= 1, sync
            doc=nurse.get('/documents/'+DOC)
            assert 'Karnofsky Performance Status bij ontslag: 80%' in doc['text']
            run=nurse.post(f'/participants/{PID}/extract?provider=rules',{'documentId':DOC})
            outcome=process_run(ai,run,provider='rules')
            assert outcome['status']=='completed'
            proposals=nurse.get(f'/participants/{PID}/extractions?documentId={DOC}')
            proposal=next(x for x in proposals if x['runId']==run['id'] and x['field']=='KPS' and x['status']=='proposed')
            assert proposal['value']=='80' and proposal['provider']=='rules' and proposal['evidence'] and proposal['spanStart'] is not None
            decision=nurse.post('/extractions/'+proposal['id']+'/decision',{'decision':'accept'})
            assert decision['extraction']['reviewState']=='accepted'
            url=f'/participants/{PID}/export/synthetic-writeback'
            preview=monitor.get(url)
            assert (preview['subject'],preview['site'],preview['source_id'],preview['extraction_id'],preview['value']) == (PID,'SITE-01',DOC,proposal['id'],'80')
            assert preview['evidence_link']==f"/documents/{DOC}#extraction-{proposal['id']}" and preview['review_state']=='accepted'
            for _ in range(2): assert monitor.post(url,{'deliveryId':preview['deliveryId']})['outcome']=='delivered'
            with sqlite3.connect(env['YAMICC_SYNTHETIC_RECEIVER_PATH']) as db: rows=db.execute('select delivery_id,payload from deliveries').fetchall()
            assert len(rows)==1 and rows[0][0]==preview['deliveryId'] and json.loads(rows[0][1])['value']=='80'
            monitor.login()
            xml=raw(base+'/studies/GBM-NL-2026-01/export/odm',token=monitor.token)
            root=etree.fromstring(xml)
            etree.XMLSchema(etree.parse(str(ROOT/'backend/app/export/xsd/ODM1-3-2.xsd'))).assertValid(root)
            ns={'o':'http://www.cdisc.org/ns/odm/v1.3'}
            items=root.xpath("//o:SubjectData[@SubjectKey=$pid]//o:ItemData[@ItemOID='IT.KPS' and @Value='80']",namespaces=ns,pid=PID)
            assert len(items)==1 and items[0].xpath('./o:AuditRecord/o:SourceID/text()',namespaces=ns)==[proposal['id']]
            print(f'PASS sync -> rules run {run["id"]} -> reviewed {proposal["id"]} -> two sends / one receiver record -> ODM XSD; site SITE-01, {PID}, {DOC}, KPS 80',flush=True)
        finally:
            if server:
                server.terminate(); server.wait(timeout=15)
            for name in (hapi,pg): subprocess.run(['docker','rm','-f',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            subprocess.run(['docker','network','rm',network],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

if __name__=='__main__': main()
