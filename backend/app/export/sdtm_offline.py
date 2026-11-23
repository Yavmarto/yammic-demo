"""Offline, fictional-only SDTM-style VS weight slice. See SDTM_OFFLINE.md."""
import argparse
import csv
import hashlib
import io
import json
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

COLUMNS = ('STUDYID', 'DOMAIN', 'USUBJID', 'VSSEQ', 'VSTESTCD', 'VSTEST',
           'VSORRES', 'VSORRESU', 'VSSTRESC', 'VSSTRESN', 'VSSTRESU', 'VSDTC')
IDENT = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_-]{0,39}$')


def _id(value, name):
    if not isinstance(value, str) or not IDENT.fullmatch(value):
        raise ValueError(f'invalid {name}')
    return value


def export(data):
    if not isinstance(data, dict) or data.get('fictional') is not True or not isinstance(data.get('rows'), list):
        raise ValueError('input must declare fictional: true and contain rows')
    study = _id(data.get('study_id'), 'study_id')
    selected = []
    seen = set()
    for row in data['rows']:
        if not isinstance(row, dict) or type(row.get('checked')) is not bool:
            raise ValueError('each row requires a boolean checked')
        if not row['checked'] or row.get('value') is None or row.get('value') == '':
            continue
        if row.get('field') != 'WEIGHT' or row.get('unit') != 'kg':
            raise ValueError('checked values must be WEIGHT in kg')
        subject = _id(row.get('subject_id'), 'subject_id')
        source = _id(row.get('source_id'), 'source_id')
        reviewer = _id(row.get('verified_by'), 'verified_by')
        raw = row['value']
        if not isinstance(raw, str) or not re.fullmatch(r'(?:0|[1-9][0-9]{0,2})(?:\.[0-9]{1,3})?', raw):
            raise ValueError('weight must be a decimal string')
        try:
            weight = Decimal(raw)
        except InvalidOperation as exc:
            raise ValueError('invalid weight') from exc
        if not 0 < weight <= 500:
            raise ValueError('weight outside local range')
        dt = row.get('date')
        try:
            if not isinstance(dt, str) or date.fromisoformat(dt).isoformat() != dt:
                raise ValueError()
        except ValueError as exc:
            raise ValueError('date must be YYYY-MM-DD') from exc
        key = (subject, dt)
        if key in seen:
            raise ValueError('duplicate subject and date')
        seen.add(key)
        normalized = format(weight.normalize(), 'f')
        selected.append((subject, dt, source, reviewer, raw, normalized))
    selected.sort()
    output = io.StringIO(newline='')
    writer = csv.writer(output, lineterminator='\n')
    writer.writerow(COLUMNS)
    provenance = []
    previous = None
    seq = 0
    for subject, dt, source, reviewer, raw, normalized in selected:
        seq = seq + 1 if subject == previous else 1
        previous = subject
        usubjid = f'{study}-{subject}'
        writer.writerow((study, 'VS', usubjid, seq, 'WEIGHT', 'Weight', raw, 'kg', normalized, normalized, 'kg', dt))
        provenance.append({'USUBJID': usubjid, 'VSSEQ': seq, 'source_id': source, 'verified_by': reviewer})
    csv_bytes = output.getvalue().encode('utf-8')
    sidecar = {'format': 'fictional-vs-provenance-v1', 'csv_sha256': hashlib.sha256(csv_bytes).hexdigest(), 'records': provenance}
    return csv_bytes, (json.dumps(sidecar, sort_keys=True, ensure_ascii=True, indent=2) + '\n').encode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('fixture', type=Path)
    parser.add_argument('output_dir', type=Path)
    args = parser.parse_args()
    csv_bytes, sidecar = export(json.loads(args.fixture.read_text(encoding='utf-8')))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / 'vs.csv').write_bytes(csv_bytes)
    (args.output_dir / 'vs.provenance.json').write_bytes(sidecar)
    print(hashlib.sha256(csv_bytes).hexdigest())


if __name__ == '__main__':
    main()
