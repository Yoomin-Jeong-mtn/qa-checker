import json
import sys
from datetime import datetime

import requests

SLACK_MAX_CHARS = 3000
SLACK_API = 'https://slack.com/api'


def format_summary(results: dict, filename: str) -> str:
    violations = results['violations']
    total = results['total_rows']
    violated_ids = {v['event_id'] for v in violations}
    passed = total - len(violated_ids)

    today = datetime.now().strftime('%-m.%-d')
    status = '❌ 불일치 있음' if violations else '✅ 이상 없음'
    return (
        f"[{today} QA 결과] {status}\n"
        f"📋 {filename}  |  총 {total}행  |  정상 {passed}건  |  위반 {len(violations)}건"
    )


def format_detail_chunks(results: dict, inference: list) -> list[str]:
    violations = results['violations']

    lines = []
    if violations:
        lines.append(f"❌ 스펙 불일치 ({len(violations)}건)")
        for v in violations:
            lines.append(f"  • [event_id: {v['event_id']}] {v['key']}: {v['error_detail']}")
    else:
        lines.append("❌ 스펙 불일치: 없음")

    lines.append("")

    if inference:
        lines.append(f"🔍 미정의 프로퍼티 — AI 추론 ({len(inference)}건)")
        for item in inference:
            lines.append(f"  • [{item['event_name']}] {item['key']}")
            lines.append(f"    → 추론: {item['inferred_type']}, required: {item['inferred_required']}")
            lines.append(f"    → 스펙 추가 검토 필요")
    else:
        lines.append("🔍 미정의 프로퍼티: 없음")

    lines.append("")
    lines.append("📌 비즈니스 규칙 참고: specs/business_rules.md")

    full_text = "\n".join(lines)
    chunks = []
    while len(full_text) > SLACK_MAX_CHARS:
        split_at = full_text.rfind('\n', 0, SLACK_MAX_CHARS)
        if split_at == -1:
            split_at = SLACK_MAX_CHARS
        chunks.append(full_text[:split_at])
        full_text = full_text[split_at:]
    chunks.append(full_text)
    return chunks


def post_message(token: str, channel: str, text: str, thread_ts: str = None) -> str:
    payload = {'channel': channel, 'text': text}
    if thread_ts:
        payload['thread_ts'] = thread_ts
    resp = requests.post(
        f'{SLACK_API}/chat.postMessage',
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json; charset=utf-8'},
        json=payload,
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    if not data.get('ok'):
        raise RuntimeError(f"Slack error: {data.get('error')}")
    return data['ts']


def send_to_slack(token: str, channel: str, results: dict, inference: list, filename: str) -> None:
    # 1. 스레드 부모 메시지 (요약)
    summary = format_summary(results, filename)
    thread_ts = post_message(token, channel, summary)

    # 2. 상세 내용을 스레드 댓글로
    chunks = format_detail_chunks(results, inference)
    for chunk in chunks:
        post_message(token, channel, chunk, thread_ts=thread_ts)

    print(f"Slack 알림 발송 완료 (스레드 댓글 {len(chunks)}개)")


if __name__ == '__main__':
    results = json.loads(sys.argv[1])
    inference = json.loads(sys.argv[2])
    filename = sys.argv[3]
    token = sys.argv[4]
    channel = sys.argv[5]
    send_to_slack(token, channel, results, inference, filename)
