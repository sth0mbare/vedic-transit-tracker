"""Canonical physical evidence, aliases, dependencies and per-category audit use."""
from hashlib import sha256
import json
from copy import deepcopy
from .spec import SOURCES, FEATURE_CATEGORIES, CATEGORIES


def actor_group(actor):
    return 'Nodes' if actor in ('Rahu','Ketu') else actor


class EvidenceBook:
    def __init__(self, at):
        self.at = at.isoformat()
        self.atoms = {}
        self.features = {}
        self.redundant = []

    def add(self, actor, target, reference, operator, layer, role, reason,
            status='contextual', interval=None, details=None):
        interval = interval or [self.at, self.at]
        domain = 'natal sidereal zodiac' if reference in ('natal D1','natal UL/DK') and target.startswith('sign:') else reference
        key = [actor, target, domain, operator, interval]
        identifier = sha256(json.dumps(key, sort_keys=True).encode()).hexdigest()[:24]
        if identifier in self.atoms:
            a = self.atoms[identifier]
            if reference not in a['references']:
                a['references'].append(reference)
            if role not in a['roles']:
                a['roles'].append(role)
            if layer not in a['layers']:
                a['layers'].append(layer)
            a['provenance_by_layer'][layer] = deepcopy(SOURCES.get(layer,SOURCES['natal']))
            self.redundant.append({'evidence_id':identifier,'alias':role,
                                   'status':'redundant','reason':'Same physical condition; no new actor.'})
            return identifier
        self.atoms[identifier] = {
            'id':identifier,'actor':actor,'actor_group':actor_group(actor),
            'target':target,'reference':reference,'references':[reference],'operator':operator,
            'at_utc':self.at,'interval':interval,'layers':[layer],'roles':[role],
            'dependency_group':f'{actor_group(actor)}|{domain}|{target}',
            'status':status,'reason':reason,'details':details or {},
            'eligible_categories':[],'feature_roles':[], 'category_use':{},
            'provenance':deepcopy(SOURCES.get(layer, SOURCES['natal'])),
            'provenance_by_layer':{layer:deepcopy(SOURCES.get(layer,SOURCES['natal']))},
        }
        return identifier

    def feature(self, name, ids):
        ids = frozenset(ids)
        if not ids:
            return
        alternatives = self.features.setdefault(name, [])
        if ids not in alternatives:
            alternatives.append(ids)
        for identifier in ids:
            atom = self.atoms[identifier]
            atom['feature_roles'] = sorted(set(atom['feature_roles']) | {name})
            atom['eligible_categories'] = sorted(set(atom['eligible_categories']) |
                                                  set(FEATURE_CATEGORIES.get(name, ())))
            atom['status'] = 'included'

    def finalize(self, assessments):
        for atom in self.atoms.values():
            for category in CATEGORIES:
                assessment = assessments[category]
                used = atom['id'] in assessment['evidence_used']
                eligible = category in atom['eligible_categories']
                atom['category_use'][category] = {
                    'status':'included' if used else 'excluded' if eligible else atom['status'] if atom['status'] in ('obstructed','excluded') else 'contextual',
                    'reason':'Gate witness or active timing refinement.' if used else
                             'Eligible candidate; required gates failed or another equivalent witness selected.' if eligible else
                             'Not eligible for this category: '+atom['reason'],
                }
        return sorted(self.atoms.values(), key=lambda a:a['id'])
