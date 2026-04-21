---
name: qa-checker
description: 이벤트 로그 CSV를 YAML 스펙과 대조하여 QA 검증 후 결과를 Slack으로 발송합니다
---

# QA Checker

이벤트 로그 CSV를 YAML 스펙과 비교해 프로퍼티명·타입·필수값·허용값을 검증하고, 결과를 Slack으로 알립니다.

## 실행 절차

### 1. 설정 파일 읽기

아래 명령으로 설정을 읽는다:

```bash
cat ~/.qa-checker/config.yaml
```

`repo_path`와 `slack.webhook_url`을 읽는다. 파일이 없으면 사용자에게 안내한다:
> `~/.qa-checker/config.yaml`이 없습니다. `config.yaml.example`을 참고해 생성해 주세요.

### 2. CSV 파일 경로 확인

사용자에게 CSV 파일 경로를 묻는다. 경로가 제공되지 않은 경우에만 질문한다.

### 3. CSV 파싱

```bash
python3 {repo_path}/scripts/parse_csv.py {csv_path}
```

출력(JSON)을 `rows` 변수에 저장한다.

### 4. 스펙 로드

```bash
python3 {repo_path}/scripts/load_spec.py {repo_path}/specs
```

출력(JSON)을 `spec` 변수에 저장한다.

### 5. 검증 실행

```bash
python3 {repo_path}/scripts/validate.py '{rows}' '{spec}'
```

출력(JSON)에서 `violations`, `unknowns`, `total_rows`를 읽는다.

### 6. 미정의 항목 AI 추론

`unknowns` 목록의 각 항목에 대해 `sample_values`를 분석해 아래를 추론한다:
- `inferred_type`: `string`, `boolean`, `integer`, `number`, `datetime` 중 하나
- `inferred_required`: `true` / `false`

기존 스펙의 유사 프로퍼티 패턴을 참고해 추론한다.
결과를 `inference` 배열로 구성한다:

```json
[
  {
    "event_name": "pdp_view",
    "key": "new_prop",
    "inferred_type": "string",
    "inferred_required": false
  }
]
```

### 7. Slack 발송

```bash
python3 {repo_path}/scripts/slack_notify.py '{results}' '{inference}' '{filename}' '{webhook_url}'
```

여기서 `{filename}`은 CSV 파일명(경로 제외), `{results}`는 Step 5의 출력 JSON이다.
