"""Read-only freeze metadata; no source writes or automatic model changes."""
import hashlib
import json
from pathlib import Path


def freeze_metadata():
    path=Path(__file__).with_name('freeze.json')
    if not path.exists():return {'status':'not yet frozen'}
    manifest=json.loads(path.read_text())
    root=Path(__file__).resolve().parents[2]
    mismatches=[p for p,digest in manifest['files'].items()
                if not (root/p).is_file() or hashlib.sha256((root/p).read_bytes()).hexdigest()!=digest]
    return {'status':'verified' if not mismatches else 'source mismatch',
            'version':manifest['version'],'implementation_sha256':manifest['implementation_sha256'],
            'methodology_sha256':manifest['methodology_sha256'],
            'base_git_commit':manifest['base_git_commit'],
            'mismatched_files':mismatches}
