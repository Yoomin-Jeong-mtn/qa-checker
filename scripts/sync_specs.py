#!/usr/bin/env python3
"""구글 시트 스펙 탭에서 데이터를 가져와 YAML 파일로 동기화하고 git commit합니다.

Usage:
    python3 sync_specs.py <sheet_csv_url> <specs_dir> <repo_path>
"""

import csv
import io
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import requests
import yaml

TYPE_MAP = {
    'string': 'string',
    'boolean': 'boolean',
    'number': 'number',
    'integer': 'integer',
    'time': 'datetime',
    'datetime': 'datetime',
}


def fetch_csv(url: str) -> str:
    resp = requests.get(url, allow_redirects=True, timeout=30)
    resp.raise_for_status()
    resp.encoding = 'utf-8'
    return resp.text


def parse_condition(required_str: str, condition: str) -> dict:
    required_str = required_str.strip().upper()
    condition = (condition or '').strip()

    if required_str == 'CONDITIONAL':
        return {'required': False, 'allow_empty': True}

    required = (required_str == 'Y')
    result = {'required': required, 'allow_empty': not required}

    # enum 파싱: "enum: A, B, C" 또는 "enum:A,B,C"
    enum_match = re.search(r'enum:\s*([^\n(]+)', condition, re.IGNORECASE)
    if enum_match:
        vals = [v.strip() for v in enum_match.group(1).split(',') if v.strip()]
        if vals:
            result['enum'] = vals

    # regex 패턴 파싱: ^ 로 시작하는 것만 (datetime 포맷 문자열 제외)
    pattern_match = re.search(r'regex:\s*(\S+)', condition, re.IGNORECASE)
    if pattern_match:
        pat = pattern_match.group(1)
        if pat.startswith('^'):
            result['pattern'] = pat

    return result


def parse_sheet(csv_text: str) -> dict:
    reader = csv.DictReader(io.StringIO(csv_text))
    events: dict = defaultdict(list)
    seen: set = set()

    for row in reader:
        event_name = (row.get('이벤트 명') or row.get('이벤트명') or '').strip()
        prop_key = (row.get('프로퍼티명') or '').strip()
        if not event_name or not prop_key:
            continue
        if (event_name, prop_key) in seen:
            continue
        seen.add((event_name, prop_key))

        data_type = (row.get('데이터 타입') or 'string').strip().lower()
        required_str = (row.get('필수 여부') or 'N').strip()
        condition = (row.get('내용 조건') or '').strip()

        extras = parse_condition(required_str, condition)
        prop = {'key': prop_key, 'type': TYPE_MAP.get(data_type, 'string')}
        prop.update(extras)
        events[event_name].append(prop)

    return dict(events)


def dump_event_yaml(event_name: str, props: list) -> str:
    return yaml.dump(
        {'event': event_name, 'properties': props},
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )


def sync(sheet_url: str, specs_dir: str, repo_path: str):
    print('📥 시트 데이터 가져오는 중...')
    try:
        csv_text = fetch_csv(sheet_url)
    except requests.RequestException as e:
        print(f'❌ 시트 접근 실패: {e}')
        print('시트가 "링크 있는 사람 누구나 보기" 로 설정되어 있는지 확인하세요.')
        sys.exit(1)

    events = parse_sheet(csv_text)
    if not events:
        print('❌ 파싱된 이벤트가 없습니다. 시트 헤더를 확인하세요.')
        sys.exit(1)
    print(f'✅ {len(events)}개 이벤트 파싱 완료')

    specs_path = Path(specs_dir)
    changed = []

    for event_name, props in sorted(events.items()):
        file_path = specs_path / f'{event_name}.yaml'
        new_content = dump_event_yaml(event_name, props)

        if file_path.exists() and file_path.read_text(encoding='utf-8') == new_content:
            continue

        is_new = not file_path.exists()
        file_path.write_text(new_content, encoding='utf-8')
        changed.append(event_name)
        print(f'  {"➕ 신규" if is_new else "✏️  업데이트"}: {event_name}.yaml')

    if not changed:
        print('변경 사항 없음. 커밋 생략.')
        return

    subprocess.run(['git', 'add', 'specs/'], cwd=repo_path, check=True)
    event_list = '\n'.join(f'- {e}' for e in sorted(changed))
    commit_msg = (
        f'chore: sync specs from spreadsheet\n\n'
        f'{len(changed)}개 이벤트 업데이트:\n{event_list}'
    )
    subprocess.run(['git', 'commit', '-m', commit_msg], cwd=repo_path, check=True)
    print(f'\n✅ {len(changed)}개 이벤트 변경사항 커밋 완료')
    print('git push를 실행하면 팀원들에게 반영됩니다.')


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print('Usage: sync_specs.py <sheet_url> <specs_dir> <repo_path>')
        sys.exit(1)
    sync(sys.argv[1], sys.argv[2], sys.argv[3])
