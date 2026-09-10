"""Consumer copy only. Reads frozen results; never recalculates or changes scores."""
from relationship_presentation import activation_level

DIMENSIONS = (
    ('meeting/dating', 'Romance / attraction', ('Few romance indicators were recognized for this moment.', 'Some romance and attraction indicators were present.', 'Several romance and attraction indicators were present.')),
    ('relationship formation', 'Relationship potential', ('Few relationship-building indicators were recognized.', 'Some relationship-building indicators were present.', 'Several relationship-building indicators were present.')),
    ('commitment/marriage', 'Commitment potential', ('Few commitment indicators were recognized.', 'Some commitment indicators were present.', 'Several commitment indicators were present.')),
    ('ending/separation', 'Ending pressure', ('Few pressure or change indicators were recognized.', 'Some pressure or change indicators were present.', 'Several pressure or change indicators were present.')),
)


def dimension_cards(result):
    cards = []
    for key, label, explanations in DIMENSIONS:
        level = activation_level(result['scores'][key]['score'])
        cards.append((label, level, explanations[('Low','Moderate','High').index(level)]))
    return cards


def moment_summary(result):
    levels = [c[1] for c in dimension_cards(result)]
    romance, formation, commitment, ending = [('Low','Moderate','High').index(v) for v in levels]
    if ending > max(romance, formation, commitment):
        return 'This model emphasized pressure or change more than relationship-building for this moment.'
    if ending and ending == max(romance, formation, commitment):
        return 'This moment showed a mix of relationship themes and pressure or change.'
    if commitment and commitment >= max(romance, formation):
        return 'Commitment themes stood out in this model’s reading of the moment.'
    if formation and formation >= romance:
        return 'Relationship-building themes stood out in this model’s reading of the moment.'
    if romance:
        return 'Romance and attraction stood out more than longer-term partnership themes in this model.'
    return 'This model found few clear relationship signals for this moment; that does not make the experience less meaningful.'


def top_reasons(result):
    """Only actual eligible legacy evidence or selected ending evidence; never pad."""
    reasons, seen = [], set()
    for fact in result['activations']:
        ending = 'ending/separation' in fact.get('categories', ())
        if not (fact.get('counted') if ending else fact.get('score_eligible') and fact.get('categories')):
            continue
        source, family = fact['source'], fact['family']
        kind = fact['condition_id'] if ending else fact['signature'].split('|', 3)[-1]
        key, text = None, None
        if family == 'dasha':
            levels = [p['level'] for p in result['dashas'] if p['lord'] == source]
            names = {'MD':'main', 'AD':'secondary', 'PD':'shorter'}
            periods = ' and '.join(names[level] for level in levels)
            key, text = ('dasha',source), f'{source} was active in your {periods} planetary periods.' if levels else None
        elif kind.startswith('house') or kind == 'occupancy':
            house = int((kind if ending else fact['target']).removeprefix('house'))
            meaning = {1:'self and identity',5:'romance',6:'conflict and obligations',7:'partnership',8:'shared resources and change',12:'release and withdrawal'}.get(house,'relationships')
            key, text = ('house',source,house), f'{source} was transiting house {house} from Moon / Chandra Lagna, associated with {meaning}.'
        elif family == 'd9':
            if ending:
                sign = kind.split(':',1)[1]
                natal = result['natal']
                targets = {'the partnership house':natal['d9_seventh'], 'the partnership ruler':natal['d9_placements'][natal['d9_seventh_lord']]['rashi'], 'Venus':natal['d9_placements']['Venus']['rashi']}
                labels = [label for label, value in targets.items() if value == sign]
            else:
                labels = [{'house7':'the partnership house','7th lord':'the partnership ruler'}.get(fact['target'],fact['target'])]
            key = ('d9',source)
            if labels:
                text = f'{source}’s transit aligned with {" and ".join(labels)} by sign in your D9 chart.'
        elif fact['target'] == 'UL':
            key, text = ('ul',source), f'{source} occupied your Upapada Lagna sign, a traditional partnership indicator.'
        elif ':' in kind:
            contact, planet = kind.split(':',1)
            key = ('contact',source,planet,contact)
            if contact == 'conjunction':
                text = f'{source} was closely aligned with your natal {planet}.'
            elif contact == 'opposition':
                text = f'{source} was closely opposite your natal {planet}.'
        if text and key not in seen:
            seen.add(key)
            reasons.append(text)
        if len(reasons) == 5:
            break
    return reasons
