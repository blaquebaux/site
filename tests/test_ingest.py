import importlib.util,json,tempfile
from pathlib import Path
from datetime import datetime,timezone
spec=importlib.util.spec_from_file_location('ingest',Path(__file__).resolve().parents[1]/'scripts/ingest-briefing.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
with tempfile.TemporaryDirectory() as folder:
    root=Path(folder);(root/'briefings').mkdir()
    state={'source_thread_id':'test','known_message_ids':['handled']}
    (root/'publishing-state.json').write_text(json.dumps(state))
    snap={'turns':[{'status':'completed','items':[{'type':'agentMessage','id':'handled'},{'type':'agentMessage','id':'new','text':'new report'}]},{'status':'active','items':[{'type':'agentMessage','id':'unfinished'}]}]}
    assert [x['id'] for x in m.pending(snap,state)]==['new']
    # Known messages require no publication and cause no writes.
    assert not m.ingest(root,{},'handled')
    assert not (root/'briefings.json').exists()
    now=datetime.now(timezone.utc).isoformat()
    a=dict(id='import-test',kind='weekly',edition_date='2026-10-10',status='archived-unverified',title='Import test',summary='No market figures',reviewed_by='Test',published_at=now,observed_at=now,sections=[{'heading':'Observed','paragraphs':['No data']}],sources=[{'label':'Provenance','url':'https://example.com/'}])
    assert m.ingest(root,a,'new')
    assert not m.ingest(root,a,'new')
    assert len(json.loads((root/'briefings.json').read_text())['articles'])==1
    assert json.loads((root/'publishing-state.json').read_text())['known_message_ids'].count('new')==1
print('New-message selection, incomplete-run exclusion, and duplicate-safe import passed')
