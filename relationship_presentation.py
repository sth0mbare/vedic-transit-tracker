"""Display-only summaries; never change or supplement calculation scores."""
from datetime import datetime
from zoneinfo import ZoneInfo

CATEGORY_LABELS = {'meeting/dating': 'Meeting / attraction',
                   'relationship formation': 'Relationship formation',
                   'commitment/marriage': 'Commitment / marriage'}


def activation_level(score):
    return 'Low' if score < 2 else 'Moderate' if score < 4 else 'High'


def result_heading(result, zone):
    day = datetime.fromisoformat(result['at_utc']).astimezone(ZoneInfo(zone))
    event = result.get('event', {})
    label = (event.get('custom_type') if event.get('event_type') == 'custom'
             else event.get('event_type')) or 'Transit snapshot'
    return f"{day.strftime('%B')} {day.day}, {day.year} — {label[0].upper() + label[1:]}"


def dasha_chain(result):
    return ' → '.join(p['lord'] for p in result['dashas'])


def standout_indicators(result):
    """Rank existing evidence, deduplicate contacts, and reserve a slot for dashas."""
    candidates = []
    meanings = {1:'self and identity', 5:'romance', 7:'partnership',
                8:'intimacy and shared resources', 11:'social connections'}
    for fact in result['activations']:
        family, source, target = fact['family'], fact['source'], fact['target']
        kind = fact['signature'].split('|', 3)[-1]
        text = None
        key = (source, target, kind)
        if family == 'dasha':
            continue
        if kind == 'occupancy':
            house = int(target.removeprefix('house'))
            text = f'{source} was transiting your natal house {house}, associated with {meanings[house]}.'
        elif kind == 'projected-sign':
            label = {'house7':'7th house of partnership', '7th lord':'7th-house ruler',
                     'Lagna':'Lagna', 'Lagna lord':'Lagna ruler'}.get(target, target)
            text = f'{source}’s transit projected into the same D9 sign as your natal {label}.'
        elif target == 'UL':
            action = 'occupied' if kind == 'sign-1' else 'cast a whole-sign aspect on'
            text = f'{source} {action} your Upapada Lagna, a traditional partnership indicator.'
        elif ':' in kind:
            contact, planet = kind.split(':', 1)
            key = (source, planet, contact)
            if contact == 'conjunction':
                text = f'Transiting {source} was close to your natal {planet}, within the selected degree orb.'
            elif contact == 'opposition':
                text = f'Transiting {source} opposed your natal {planet}, within the selected degree orb.'
            elif contact.startswith('whole-sign aspect'):
                text = f'Transiting {source} cast a whole-sign aspect on your natal {planet}; this is a sign connection, not necessarily an exact angle.'
        if text:
            candidates.append((not fact['score_eligible'], key, text))
    candidates.sort(key=lambda item: item[0])  # stable: preserve calculation order within each rank
    seen, selected = set(), []
    for _, key, text in candidates:
        if key not in seen:
            seen.add(key)
            selected.append(text)
        if len(selected) == 5:
            break
    if dasha_chain(result):
        selected.append(f'Your active Vimshottari period was {dasha_chain(result)}.')
    return selected
