import json
import re
import sys
from datetime import datetime


def _is_datetime(value) -> bool:
    if not isinstance(value, str):
        return False
    try:
        datetime.fromisoformat(value.replace('Z', '+00:00'))
        return True
    except ValueError:
        return False


TYPE_CHECKERS = {
    'string': lambda v: isinstance(v, str),
    'boolean': lambda v: isinstance(v, bool),
    'integer': lambda v: isinstance(v, int) and not isinstance(v, bool),
    'number': lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    'datetime': _is_datetime,
}


def validate(rows: list, spec: dict) -> dict:
    violations = []
    unknowns: dict = {}

    for row in rows:
        event_name = row['name']
        event_id = row['event_id']
        properties = row['properties']

        if event_name not in spec:
            key = (event_name, None)
            if key not in unknowns:
                unknowns[key] = {'event_name': event_name, 'key': None, 'sample_values': []}
            continue

        event_spec = spec[event_name]

        for prop_key, prop_def in event_spec.items():
            if prop_def.get('required') and prop_key not in properties:
                violations.append({
                    'event_id': event_id,
                    'event_name': event_name,
                    'key': prop_key,
                    'value': None,
                    'error_type': 'missing_required',
                    'error_detail': '필수 프로퍼티 누락',
                })

        for prop_key, value in properties.items():
            if prop_key not in event_spec:
                ukey = (event_name, prop_key)
                if ukey not in unknowns:
                    unknowns[ukey] = {'event_name': event_name, 'key': prop_key, 'sample_values': []}
                if len(unknowns[ukey]['sample_values']) < 3:
                    unknowns[ukey]['sample_values'].append(value)
                continue

            prop_def = event_spec[prop_key]
            expected_type = prop_def['type']
            allow_empty = prop_def.get('allow_empty', False)

            if value == '':
                if not allow_empty:
                    violations.append({
                        'event_id': event_id, 'event_name': event_name,
                        'key': prop_key, 'value': value,
                        'error_type': 'empty_not_allowed', 'error_detail': '빈값 허용 안 됨',
                    })
                continue  # 빈값은 type/enum/pattern 검사 생략

            if value != '':
                checker = TYPE_CHECKERS.get(expected_type)
                if checker and not checker(value):
                    violations.append({
                        'event_id': event_id, 'event_name': event_name,
                        'key': prop_key, 'value': value,
                        'error_type': 'type_mismatch',
                        'error_detail': f'타입 오류 (expected: {expected_type}, got: {type(value).__name__})',
                    })
                    continue

            enum_vals = prop_def.get('enum')
            if enum_vals and value not in enum_vals:
                violations.append({
                    'event_id': event_id, 'event_name': event_name,
                    'key': prop_key, 'value': value,
                    'error_type': 'enum_mismatch',
                    'error_detail': f'허용값 아님 (enum: {"|".join(str(e) for e in enum_vals)})',
                })
                continue

            pattern = prop_def.get('pattern')
            if pattern and isinstance(value, str) and not re.match(pattern, value):
                violations.append({
                    'event_id': event_id, 'event_name': event_name,
                    'key': prop_key, 'value': value,
                    'error_type': 'pattern_mismatch',
                    'error_detail': f'패턴 불일치 (pattern: {pattern})',
                })

    return {
        'violations': violations,
        'unknowns': list(unknowns.values()),
        'total_rows': len(rows),
    }


if __name__ == '__main__':
    rows = json.loads(sys.argv[1])
    spec = json.loads(sys.argv[2])
    print(json.dumps(validate(rows, spec), ensure_ascii=False))
