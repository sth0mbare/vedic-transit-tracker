from pathlib import Path
import json,hashlib
from vedic_astro.relationship_v2.provenance import freeze_metadata
from vedic_astro.relationship_v2.spec import VERSION


def test_frozen_sources_and_shared_dependencies_match():
    meta=freeze_metadata()
    assert meta['status']=='verified'
    assert meta['version']==VERSION
    manifest=json.loads(Path('vedic_astro/relationship_v2/freeze.json').read_text())
    assert hashlib.sha256(json.dumps(manifest['implementation_files'],sort_keys=True).encode()).hexdigest()==manifest['implementation_sha256']


def test_engine_has_no_legacy_scoring_calls():
    import ast
    for p in Path('vedic_astro/relationship_v2').glob('*.py'):
        tree=ast.parse(p.read_text())
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom) and node.module and node.module.endswith('relationships'):
                assert {n.name for n in node.names}<={'indicators','SIGN_LORDS','CLASSICAL','contact_rows'}
