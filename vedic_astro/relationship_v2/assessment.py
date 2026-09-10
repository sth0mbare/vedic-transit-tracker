"""Boolean gates with actual witness alternatives; no scores or probabilities."""
from itertools import product


def assess(book):
    features=book.features
    def alternatives(*names):return [v for name in names for v in features.get(name,[])]
    result={}
    def category(name,gates,actor_gates=()):
        passed={g:bool(options) for g,options in gates.items()}
        choices=[]
        if all(passed.values()):
            for values in product(*gates.values()):
                selected=dict(zip(gates,values))
                actor_ids=set().union(*(selected[g] for g in actor_gates)) if actor_gates else set()
                actors={book.atoms[i]['actor_group'] for i in actor_ids}
                if not actor_gates or len(actors)>=2:
                    union=set().union(*values)
                    choices.append((union,actors,selected))
        if actor_gates:passed['two_distinct_gate_actors']=bool(choices)
        chosen=min(choices,key=lambda x:(len(x[0]),sorted(x[0]))) if choices else (set(),set(),{})
        used,actors,witnesses=chosen
        missing=[g for g,v in passed.items() if not v]
        out={'gates':passed,'gates_passed':[g for g,v in passed.items() if v],
             'gates_failed':missing,'missing_requirements':[
                 {'gate':g,'reason':'No qualifying evidence under the frozen rule.' if g!='two_distinct_gate_actors' else 'Two distinct actors among qualifying period/structural witnesses are not established.'} for g in missing],
             'architecture_active':not missing,'evidence_used':sorted(used),
             'gate_witnesses':{g:sorted(v) for g,v in witnesses.items()},
             'evidence_candidates':{g:[sorted(v) for v in options] for g,options in gates.items()},
             'distinct_gate_actors':sorted(actors)}
        result[name]=out
        return out
    r=category('romance',{'romance_period':alternatives('romance_period'),'romance_trigger':alternatives('romance_trigger')})
    r['state']='elevated romance activity' if r['architecture_active'] else 'short-term trigger only' if alternatives('romance_trigger') else 'inactive'
    p=category('partner_entry',{'partnership_period':alternatives('partnership_period'),
        'jupiter_support':alternatives('jupiter_support'),
        'corroboration':alternatives('d9_corroboration','positive_ul_dk')},('partnership_period','jupiter_support'))
    c=category('commitment',{'partnership_period':alternatives('partnership_period'),
        'jupiter_support':alternatives('jupiter_support'),'d9_corroboration':alternatives('d9_corroboration'),
        'continuity':alternatives('continuity')},('partnership_period','jupiter_support'))
    for a,base,triggered in [(p,'structural window active','structural window + entry trigger active'),
                             (c,'commitment architecture active','commitment architecture + trigger active')]:
        a['trigger_active']=a['architecture_active'] and bool(alternatives('partner_trigger'))
        a['state']=triggered if a['trigger_active'] else base if a['architecture_active'] else 'not established'
        if a['trigger_active']:a['evidence_used']=sorted(set(a['evidence_used'])|set().union(*alternatives('partner_trigger')))
    s=category('stress',{'stress_period':alternatives('stress_period'),'saturn_structure':alternatives('saturn_stress')},('stress_period','saturn_structure'))
    s['reinforced']=s['architecture_active'] and bool(alternatives('stress_reinforcement'))
    s['trigger_active']=s['architecture_active'] and bool(alternatives('stress_trigger'))
    s['state']='stress trigger active' if s['trigger_active'] else 'reinforced stress architecture' if s['reinforced'] else 'stress architecture active' if s['architecture_active'] else 'absent'
    if s['architecture_active']:
        extra=alternatives('stress_reinforcement','stress_trigger')
        if extra:s['evidence_used']=sorted(set(s['evidence_used'])|set().union(*extra))
    # A standalone romance trigger is visible evidence, but does not satisfy its failed period gate.
    r['trigger_active']=bool(alternatives('romance_trigger'))
    if r['trigger_active']:r['evidence_used']=sorted(set(r['evidence_used'])|set().union(*alternatives('romance_trigger')))
    for a in result.values():
        a['evidence_excluded']=sorted(set(book.atoms)-set(a['evidence_used']))
    return result
