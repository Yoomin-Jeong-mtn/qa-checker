import csv
import json
import sys
from pathlib import Path


def parse_csv(filepath: str) -> list[dict]:
    rows = []
    with open(filepath, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=2):
            rows.append({
                'row': i,
                'name': row['NAME'],
                'time': row['TIME'],
                'user_id': row['USER_ID'],
                'event_id': row['EVENT_ID'],
                'properties': json.loads(row['PROPERTIES']),
            })
    return rows


if __name__ == '__main__':
    result = parse_csv(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False))
