import importlib.util, tempfile, json
from pathlib import Path
from datetime import datetime, timezone
spec=importlib.util.spec_from_file_location('publisher',str(Path(__file__).resolve().parents[1] / 'scripts/publish-briefings.py'))
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
now=datetime(2026,10,10,18,tzinfo=timezone.utc)
a=dict(id='example-afternoon',kind='afternoon',status='mock',title='Pulse — example',summary='Example — no market data',reviewed_by='Test editor',published_at='2026-10-09T15:47:00-04:00',observed_at='2026-10-09T15:45:00-04:00',sections=[dict(heading='Observed',paragraphs=['Example'])],sources=[dict(label='Example',url='https://example.com/')])
assert m.validate(a,now)['title']=='Pulse; example'
assert m.validate(dict(a,status='archived-unverified'),now)['status']=='archived-unverified'
for patch in [dict(status='live'),dict(sources=[]),dict(published_at='2026-10-11T12:00:00-04:00'),dict(title='chatgpt-content-reference'),dict(observed_at='2026-10-10T12:00:00-04:00'),dict(kind='weekly')]:
    try: m.validate(dict(a,**patch),now)
    except (AssertionError,ValueError): pass
    else: raise AssertionError(patch)
with tempfile.TemporaryDirectory() as d:
    root=Path(d);(root/'briefings').mkdir();(root/'briefings/a.json').write_text(json.dumps(a));m.build(root,now)
    assert len(json.loads((root/'briefings.json').read_text())['articles'])==1
    (root/'briefings/b.json').write_text(json.dumps(a))
    try: m.build(root,now)
    except AssertionError: pass
    else: raise AssertionError('duplicate id accepted')
    assert len(json.loads((root/'briefings.json').read_text())['articles'])==1
print('Publisher validation and atomic failure checks passed')
