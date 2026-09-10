"""Read-only legacy protection with fabricated astronomy/periods only."""
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch
from tests.test_relationship_v2 import chart,positions,periods,AT
from vedic_astro.relationships import analyze,RULE_VERSION
from vedic_astro.relationship_v2 import analyze_v2


def test_v1_1_frozen_sources_still_exact():
    manifest=json.loads(Path('tests/fixtures/relationship_v1_1_lock.json').read_text())
    assert manifest['version']==RULE_VERSION
    for p,digest in manifest['files'].items():assert sha256(Path(p).read_bytes()).hexdigest()==digest,p


def test_v1_1_outputs_before_and_after_v2_remain_identical():
    rows=json.loads(Path('tests/fixtures/relationship_v1_1_synthetic_preservation.json').read_text())
    for row in rows:
        pos=positions(**row['positions']);c=chart()
        with patch('vedic_astro.relationships.get_planet_positions',return_value=pos),patch('vedic_astro.relationships.dasha_at',return_value=periods()):
            before=analyze(c,AT)
            analyze_v2(c,AT,position_provider=lambda *a:pos,period_provider=lambda *a:periods())
            after=analyze(c,AT)
        assert before==after
        assert sha256(json.dumps(after,default=str,sort_keys=True).encode()).hexdigest()==row['sha256']
