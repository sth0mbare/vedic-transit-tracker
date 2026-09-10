"""Independent prospective methodology; no event-calibrated parameters."""
VERSION = 'relationship_timing_v2_0'
CATEGORIES = ('romance', 'partner_entry', 'commitment', 'stress')
PARAMETERS = {
    'degree_orb': 3.0, 'degree_contacts': 'diagnostic_only',
    'transit_house_reference': 'Moon / Chandra Lagna',
    'natal_reference': 'D1 Ascendant', 'd9_reference': 'natal D9 Lagna',
    'node_graha_drishti': False, 'node_rashi_drishti': False,
    'projected_transit_d9': False, 'vedha_blockers': 'seven_classical',
    'structural_actor_minimum': 2, 'ingress_bracket_seconds': 3600,
    'boundary_precision_seconds': 1, 'window_minimum_duration': None,
    'gap_filling': False, 'weights': None, 'probability_calibration': None,
}
SOURCES = {
    'natal': {'classification': 'traditional + interpretive/engineering eligibility',
              'source': 'https://www.wisdomlib.org/hinduism/book/phaladeepika-by-mantreswara-text-and-translation/d/doc1621582.html'},
    'climate': {'classification': 'traditional pairs; seven-classical blocker choice',
                'source': 'https://www.wisdomlib.org/hinduism/book/phaladeepika-by-mantreswara-text-and-translation/d/doc1621598.html'},
    'ul_dk': {'classification': 'school-specific Jaimini + engineering transit restrictions',
              'source': 'https://lakshminarayanlenasia.com/articles/JAIMINISUTRAS.pdf'},
    'd9': {'classification': 'school-specific natal corroboration'},
    'period': {'classification': 'traditional Vimshottari + engineered role gates'},
    'structural': {'classification': 'school-specific natal-target transits + engineering climate qualification'},
    'trigger': {'classification': 'interpretive + engineering timing restrictions'},
    'diagnostic': {'classification': 'engineering; no gate eligibility'},
    'assessment': {'classification': 'engineering Boolean gates; no statistical probabilities'},
}
VEDHA = {
    'Sun': {3:9,6:12,10:4,11:5}, 'Moon': {1:5,3:9,6:12,7:2,10:4,11:8},
    'Mars': {3:12,6:9,11:5}, 'Mercury': {2:5,4:3,6:9,8:1,10:8,11:12},
    'Jupiter': {2:12,5:4,7:3,9:10,11:8},
    'Venus': {1:8,2:7,3:1,4:10,5:9,8:5,9:11,11:3,12:6},
    'Saturn': {3:12,6:9,11:5},
}
VEDHA_EXCEPTIONS = {'Sun':'Saturn','Saturn':'Sun','Moon':'Mercury','Mercury':'Moon'}
FEATURE_CATEGORIES = {
    'romance_period': ('romance',), 'partnership_period': ('partner_entry','commitment'),
    'stress_period': ('stress',), 'jupiter_support': ('partner_entry','commitment'),
    'd9_corroboration': ('partner_entry','commitment'),
    'positive_ul_dk': ('partner_entry',), 'continuity': ('commitment',),
    'saturn_stress': ('stress',), 'romance_trigger': ('romance',),
    'partner_trigger': ('partner_entry','commitment'), 'stress_trigger': ('stress',),
    'stress_reinforcement': ('stress',),
}
