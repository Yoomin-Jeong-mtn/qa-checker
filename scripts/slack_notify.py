import json
import sys

import requests

SLACK_MAX_CHARS = 3000


def format_message(results: dict, filename: str, inference: list) -> list[str]:
    violations = results['violations']
    total = results['total_rows']
    violated_ids = {v['event_id'] for v in violations}
    passed = total - len(violated_ids)

    lines = [f"📋 QA 결과 | {filename}  (총 {total}행)\n"]

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
    lines.append(f"✅ 정상: {passed}건")
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


def send_to_slack(webhook_url: str, messages: list[str]) -> None:
    for msg in messages:
        response = requests.post(webhook_url, json={'text': msg}, timeout=10)
        response.raise_for_status()


if __name__ == '__main__':
    results = json.loads(sys.argv[1])
    inference = json.loads(sys.argv[2])
    filename = sys.argv[3]
    webhook_url = sys.argv[4]
    messages = format_message(results, filename, inference)
    send_to_slack(webhook_url, messages)
    print(f"Slack 알림 발송 완료 ({len(messages)}개 메시지)")
