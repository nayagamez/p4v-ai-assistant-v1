# P4V AI Assistant

P4V(Perforce Visual Client)의 Changelist 컨텍스트 메뉴에서 AI 기능을 사용할 수 있는 도구입니다.

## 기능

### 현재 구현된 기능
- **AI Description 생성**: 코드 변경 내용을 분석하여 커밋 메시지 자동 생성

### 예정된 기능
- AI 코드 리뷰: 변경된 코드의 잠재적 문제점 분석 및 리포트 생성

## 시스템 구성

```
┌─────────────────────────────────────────────────────────────┐
│                         사용자 PC                            │
│  ┌─────────┐    우클릭     ┌──────────────────┐             │
│  │   P4V   │ ──────────▶  │  p4v_ai_tool.exe │             │
│  │ Context │              │  1. p4 명령어로   │             │
│  │  Menu   │              │     정보 수집     │             │
│  └─────────┘              │  2. n8n 호출      │             │
│                           │  3. 결과 처리     │             │
│                           └────────┬─────────┘             │
└────────────────────────────────────┼────────────────────────┘
                                     │ HTTP POST
                                     ▼
┌─────────────────────────────────────────────────────────────┐
│                         사내 서버                            │
│  ┌─────────────────┐         ┌─────────────────┐           │
│  │      n8n        │────────▶│    사내 LLM     │           │
│  │  Webhook 수신   │         │    (Gemini)     │           │
│  │  프롬프트 구성  │◀────────│  코드 분석      │           │
│  └─────────────────┘         └─────────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

## 프로젝트 구조

```
p4v-ai-assistant-v1/
├── src/
│   ├── __init__.py
│   ├── main.py              # CLI 엔트리포인트
│   ├── config_manager.py    # 설정 파일 관리
│   ├── p4_client.py         # Perforce 명령어 래퍼
│   ├── n8n_client.py        # n8n HTTP 클라이언트
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── description.py   # AI Description 생성 로직
│   │   └── install.py       # P4V Custom Tools 등록
│   └── ui/
│       ├── __init__.py
│       └── dialogs.py       # GUI 다이얼로그 (tkinter)
├── build/                   # PyInstaller 빌드 (예정)
├── installer/               # NSIS 인스톨러 (예정)
├── venv/                    # Python 가상환경
├── requirements.txt         # Python 의존성
├── test_webhook.py          # n8n 웹훅 테스트 스크립트
└── README.md
```

## 설치 및 설정

### 1. 환경 설정

```bash
# 가상환경 생성
python -m venv venv

# 의존성 설치
venv\Scripts\pip install -r requirements.txt
```

### 2. Webhook URL 설정

```bash
# 설정 GUI 열기
venv\Scripts\python -m src.main settings
```

또는 직접 설정 파일 편집:
- 위치: `%APPDATA%\P4V-AI-Assistant\config.json`
```json
{
  "webhook_url": "https://your-n8n-server/webhook/...",
  "timeout": 60
}
```

### 3. P4V Custom Tools 등록

```bash
# P4V 컨텍스트 메뉴에 도구 등록
venv\Scripts\python -m src.main install

# 도구 제거
venv\Scripts\python -m src.main uninstall
```

등록 후 **P4V를 재시작**하면 Pending Changelist 우클릭 시 "AI Description 생성" 메뉴가 나타납니다.

## 사용법

### CLI 명령어

```bash
# AI Description 생성
venv\Scripts\python -m src.main description --changelist <CL번호>

# 전체 옵션
venv\Scripts\python -m src.main description -c <CL번호> -p <서버:포트> -u <사용자> --client <워크스페이스>

# 설정 GUI
venv\Scripts\python -m src.main settings

# P4V 도구 설치/제거
venv\Scripts\python -m src.main install
venv\Scripts\python -m src.main uninstall

# 도움말
venv\Scripts\python -m src.main --help
```

### P4V에서 사용

1. P4V에서 Pending Changelist 우클릭
2. "AI Description 생성" 메뉴 클릭
3. AI가 코드 변경 내용을 분석하여 Description 자동 생성 및 적용

## n8n 워크플로우

### 워크플로우 구조

```
Webhook → Code (프롬프트 준비) → AI Agent (Gemini) → Code (응답 포맷) → Respond to Webhook
                                       ↓ (에러 시)
                                 Error Response → Respond to Webhook
```

### API 요청 형식

```json
{
  "request_type": "description",
  "changelist": {
    "number": 12345,
    "user": "username",
    "client": "workspace",
    "current_description": "현재 설명"
  },
  "files": [
    {
      "depot_path": "//depot/path/to/file.cpp",
      "action": "edit",
      "revision": 15,
      "diff": "--- a/file.cpp\n+++ b/file.cpp\n..."
    }
  ]
}
```

### API 응답 형식

```json
{
  "success": true,
  "description": "[Feature] 기능 설명\n\n상세 내용...",
  "summary": "기능 요약"
}
```

## 기술 스택

| 구성 요소 | 기술 |
|-----------|------|
| 클라이언트 | Python 3.x + tkinter |
| 워크플로우 | n8n |
| AI | Google Gemini (사내 LLM) |
| 배포 예정 | PyInstaller + NSIS |

## 의존성

- Python 3.8+
- requests >= 2.28.0
- tkinter (Python 기본 포함)

## 라이선스

Internal Use Only
