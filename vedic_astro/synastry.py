"""Natal chart comparison, kept separate from event timing and scoring."""
from dataclasses import asdict
from datetime import date, time, timedelta

from .chart import compute_natal_chart
from .ephemeris import get_planet_positions
from .relationship_records import local_instant
from .relationships import contact_rows, indicators
from .util import rashi_name, nakshatra_name, house_from_sign, angular_separation


def profile_chart(profile, ayanamsa):
    if not profile.reliable_time:
        raise ValueError('Lagna, houses, D9 and UL require a reliable birth time')
    return compute_natal_chart(profile.instant(),profile.latitude,profile.longitude,ayanamsa)


def compare_profiles(natal, profile, orb=3.0):
    at=profile.instant()
    if profile.reliable_time:
        partner=profile_chart(profile,natal.ayanamsa)
        placements={p:asdict(v) for p,v in partner.planets.items()}
        source={p:v.longitude for p,v in partner.planets.items()}
        my_targets={p:v.longitude for p,v in natal.planets.items()}
        my_targets['Lagna']=natal.ascendant_longitude
        partner_targets=dict(source, Lagna=partner.ascendant_longitude)
        forward=contact_rows(source,my_targets,orb)
        backward=contact_rows({p:v.longitude for p,v in natal.planets.items()},partner_targets,orb)
        for row in forward: row['direction']='Partner → you'
        for row in backward: row['direction']='You → partner'
        my_d9=indicators(natal)['d9_placements']
        their_meta=indicators(partner)
        d9_contacts=[{'your_planet':a,'partner_planet':b,'shared_d9_sign':pa['rashi'],
                      'rule':'Natal D9 sign co-occupation; no physical degree contact implied'}
                     for a,pa in my_d9.items() for b,pb in their_meta['d9_placements'].items()
                     if pa['rashi']==pb['rashi']]
        return {'reliable_time':True,'at_utc':at.isoformat(),'timezone':profile.timezone,
                'ayanamsa':natal.ayanamsa,'partner_d1':placements,
                'lagna_separation_degrees':angular_separation(natal.ascendant_longitude,partner.ascendant_longitude),
                'partner_lagna':partner.ascendant_rashi,'partner_lagna_longitude':partner.ascendant_longitude,
                'partner_moon_nakshatra':partner.moon_nakshatra,'partner_moon_pada':partner.moon_pada,
                'partner_indicators':their_meta,'your_indicators':indicators(natal),
                'contacts':forward+backward,'d9_contacts':d9_contacts,
                'house_overlays':[{'planet':p,'partner_in_your_house':house_from_sign(v.longitude,natal.ascendant_longitude),
                                   'you_in_partner_house':house_from_sign(natal.planets[p].longitude,partner.ascendant_longitude)}
                                  for p,v in partner.planets.items()]}
    # No Ascendant or house calculation is performed for an unreliable/unknown time.
    positions=get_planet_positions(at,natal.ayanamsa)
    day=date.fromisoformat(profile.day)
    start=local_instant(day,time(0),profile.timezone,0)
    end=local_instant(day+timedelta(days=1),time(0),profile.timezone,0)
    samples=[]
    cursor=start
    while cursor<end:
        samples.append(get_planet_positions(cursor,natal.ayanamsa))
        cursor+=timedelta(hours=1)
    rows=[]
    for name,pos in positions.items():
        rows.append({'planet':name,'provisional_longitude':pos.longitude,'provisional_sign':rashi_name(pos.longitude),
                     'sampled_signs':sorted({rashi_name(s[name].longitude) for s in samples}),
                     'sampled_nakshatras':sorted({nakshatra_name(s[name].longitude) for s in samples})})
    contacts=contact_rows({p:v.longitude for p,v in positions.items()},
                          {p:v.longitude for p,v in natal.planets.items()},orb)
    return {'reliable_time':False,'at_utc':at.isoformat(),'timezone':profile.timezone,
            'ayanamsa':natal.ayanamsa,'provisional_planets':rows,'provisional_contacts':contacts,
            'unavailable':['Lagna','houses','D9','Upapada','definitive Darakaraka','definitive Moon/nakshatra'],
            'assumption':'Reference time only (noon when time absent); hourly samples are not guaranteed full-day bounds. Contacts are provisional and not used for event scores.'}
