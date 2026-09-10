"""Opt-in JSON snapshot viewer; no UI integration, scans, or default dates."""
import argparse
import json
from datetime import datetime
from pathlib import Path
from ..chart import NatalChart, PlanetPlacement
from .engine import analyze_v2


def main():
    parser=argparse.ArgumentParser(description='Inspect independent v2 gates and evidence as JSON')
    parser.add_argument('--chart',required=True,help='Exported NatalChart JSON, not an event record')
    parser.add_argument('--at',required=True,help='Timezone-aware ISO timestamp')
    args=parser.parse_args()
    data=json.loads(Path(args.chart).read_text())
    chart=NatalChart(**{**data,'birth_datetime_utc':datetime.fromisoformat(data['birth_datetime_utc']),
                       'planets':{p:PlanetPlacement(**v) for p,v in data['planets'].items()}})
    print(json.dumps(analyze_v2(chart,datetime.fromisoformat(args.at)),default=str,indent=2))


if __name__=='__main__':main()
