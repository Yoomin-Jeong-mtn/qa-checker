---
name: qa-checker
description: 이벤트 로그 CSV를 YAML 스펙과 대조해 QA 검증 후 Slack 발송. 스펙 동기화(구글 시트 → YAML git commit)도 지원합니다.
---

# QA Checker

이벤트 로그 CSV를 YAML 스펙과 비교해 프로퍼티명·타입·필수값·허용값을 검증하고, 결과를 Slack으로 알립니다.
스펙 동기화 요청 시 구글 시트 → YAML 파일 갱신 → git commit을 자동 처리합니다.

---

## 스펙 동기화 모드

사용자가 "스펙 동기화", "sync", "시트 반영" 등을 요청하면 **QA 검증 대신** 아래 절차를 실행한다.

### S1. 설정 읽기

```bash
cat ~/.qa-checker/config.yaml
```

`repo_path`와 `sheet.specs_url`을 읽는다.
`sheet.specs_url`이 없으면:
> `config.yaml`에 `sheet.specs_url`이 없습니다. `config.yaml.example`을 참고해 추가해 주세요.

### S2. 동기화 실행

```bash
python3 {repo_path}/scripts/sync_specs.py "{specs_url}" {repo_path}/specs {repo_path}
```

### S3. 결과 보고

- 변경된 이벤트 목록을 보여준다.
- 변경사항이 있으면 팀원 반영을 위해 `git push` 여부를 묻는다.
- 사용자가 동의하면: `git push origin main` (cwd: repo_path)

---

## QA 검증 모드

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

`bot_token`과 `channel`을 config에서 읽어 실행한다:

```bash
python3 {repo_path}/scripts/slack_notify.py '{results}' '{inference}' '{filename}' '{bot_token}' '{channel}'
```

여기서 `{filename}`은 CSV 파일명(경로 제외), `{results}`는 Step 5의 출력 JSON이다.
첫 메시지로 `[날짜 QA 결과]` 요약을 보내고, 상세 내용은 스레드 댓글로 달린다.
