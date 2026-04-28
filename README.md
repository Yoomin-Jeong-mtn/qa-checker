# QA Checker — Claude Code 스킬

이벤트 로그 CSV를 YAML 스펙과 대조해 QA를 자동화하는 Claude Code 스킬.

## 설치

### macOS / Linux

#### 1. 레포 클론

```bash
git clone <repo-url> ~/qa-checker
cd ~/qa-checker
pip3 install -r requirements.txt
```

#### 2. 설정 파일 생성

```bash
mkdir -p ~/.qa-checker
cp config.yaml.example ~/.qa-checker/config.yaml
```

`~/.qa-checker/config.yaml`을 열어 `repo_path`와 Slack bot_token, channel을 입력한다.

#### 3. 스킬 설치

```bash
npx skills add <org/repo@qa-checker> -g -y
```

---

### Windows

> Git Bash 또는 WSL 환경을 권장한다. PowerShell에서도 동작하지만 경로 표기에 주의한다.

#### 1. 레포 클론

```bash
git clone <repo-url> C:/Users/<username>/qa-checker
cd C:/Users/<username>/qa-checker
pip install -r requirements.txt   # Windows는 pip3 대신 pip 또는 python -m pip 사용
```

#### 2. 설정 파일 생성

```bash
mkdir -p ~/.qa-checker
cp config.yaml.example ~/.qa-checker/config.yaml
```

`~/.qa-checker/config.yaml`의 `repo_path`는 Windows 경로(`C:/Users/<username>/qa-checker`)로 입력한다.

#### 3. 스킬 설치

```bash
npx skills add <org/repo@qa-checker> -g -y
```

#### Windows 주의사항

| 항목 | 내용 |
|------|------|
| Python 명령어 | `python3` 대신 `python` 사용 (Windows Store stub 문제) |
| `repo_path` | 슬래시(`/`) 또는 백슬래시(`\`) 모두 허용 |
| `install.sh` | Git Bash에서 실행하거나 수동으로 위 단계를 진행 |

## 사용법

Claude Code에서 QA Checker 스킬을 실행 후 CSV 파일 경로를 입력한다.

## 스펙 관리

- `specs/_common.yaml`: 이벤트 간 공통 프로퍼티 그룹 정의
- `specs/<event_name>.yaml`: 이벤트별 스펙 (`extends`로 공통 프로퍼티 상속)
- `specs/business_rules.md`: 자동 검증 불가 항목 메모

새 이벤트 추가 시 `specs/`에 YAML 파일을 추가하고 PR을 올린다.

## CSV 구조

```
NAME,TIME,USER_ID,EVENT_ID,PROPERTIES
pdp_view,1776064118,user_abc,evt_001,{"platform":"PC",...}
```

## 검증 항목

| 항목 | 자동 | 비고 |
|------|------|------|
| 이벤트명 존재 여부 | ✅ | |
| 필수 프로퍼티 누락 | ✅ | |
| 데이터 타입 | ✅ | |
| 빈값 허용 | ✅ | |
| enum / regex 패턴 | ✅ | |
| 미정의 항목 AI 추론 | ✅ | Claude가 타입 추론 |
| 조건부 프로퍼티 관계 | ❌ | business_rules.md 참고 |
