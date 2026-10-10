#!/usr/bin/env python3
"""Idempotent import from a reviewed article prepared by the scheduled publisher.
The source chat is read using the app's read_thread tool, never scraped by this script.
Commit the input, compiled archive, and state together after this succeeds.
"""
import argparse, importlib.util, json, os
from pathlib import Path
from datetime import datetime, timezone

spec = importlib.util.spec_from_file_location('publisher', Path(__file__).with_name('publish-briefings.py'))
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)

def pending(snapshot, state):
    known = set(state['known_message_ids'])
    messages = []
    for turn in snapshot.get('turns', []):
        if turn.get('status') != 'completed':
            continue
        for item in turn.get('items', []):
            if item.get('type') == 'agentMessage' and item.get('id') not in known:
                messages.append(item)
    return messages

def ingest(root, article, message_id):
    state_path = root / 'publishing-state.json'
    state = json.loads(state_path.read_text())
    if message_id in state['known_message_ids']:
        return False
    article = dict(article, source_message_id=message_id, source_thread_id=state['source_thread_id'])
    article = publisher.validate(article, datetime.now(timezone.utc))
    destination = root / 'briefings' / (article['id'] + '.json')
    if destination.exists():
        raise ValueError('Edition already exists; require explicit correction review')
    destination.write_text(json.dumps(article, ensure_ascii=False, indent=2) + '\n')
    try:
        publisher.build(root)
    except Exception:
        destination.unlink()
        raise
    state['known_message_ids'].append(message_id)
    temp = state_path.with_suffix('.tmp')
    temp.write_text(json.dumps(state, indent=2) + '\n')
    os.replace(temp, state_path)
    return True

if __name__ == '__main__':
    cli = argparse.ArgumentParser()
    cli.add_argument('--root', type=Path, default=Path('bumble'))
    cli.add_argument('--snapshot', type=Path)
    cli.add_argument('--article', type=Path)
    cli.add_argument('--message-id')
    args = cli.parse_args()
    if args.snapshot:
        state = json.loads((args.root / 'publishing-state.json').read_text())
        found = pending(json.loads(args.snapshot.read_text()), state)
        print(json.dumps({'pending': [{'id': x['id'], 'truncated': bool(x.get('truncated')), 'text': x.get('text', '')} for x in found]}))
    elif args.article and args.message_id:
        print('Imported' if ingest(args.root, json.loads(args.article.read_text()), args.message_id) else 'Already handled; no changes')
    else:
        cli.error('provide --snapshot or both --article and --message-id')
