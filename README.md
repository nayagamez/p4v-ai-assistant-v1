# P4V AI Assistant

P4V(Perforce Visual Client)의 Changelist 컨텍스트 메뉴에서 AI 기능을 사용할 수 있는 도구입니다.

**현재 버전: v0.4.2**

## 기능

- **AI Description 생성**: 코드 변경 내용을 분석하여 커밋 메시지 자동 생성
- **AI 코드 리뷰**: 변경된 코드의 잠재적 문제점 분석 및 리포트 생성
  - 점수 및 심각도별 통계
  - 파일별 상세 코멘트
  - HTML 리포트 내보내기 (Side-by-side diff 뷰)
  - 대용량 Changelist 배치 처리 (Redis Memory로 컨텍스트 유지)
- **전문가 프로필**: Unity, Unreal, 범용 전문가 컨텍스트 지원
- **다양한 뷰 지원**: Pending, Submitted, History 모든 뷰에서 컨텍스트 메뉴 사용 가능

## 시스템 구성

```
┌─────────────────────────────────────────────────────────────┐
│                         사용자 PC                            │
│  ┌─────────┐    우클릭     ┌───────────────────────┐        │
│  │   P4V   │ ──────────▶  │ p4v_ai_assistant.exe  │        │
│  │ Context │              │  1. p4 명령어로        │        │
│  │  Menu   │              │     정보 수집          │        │
│  └─────────┘              │  2. n8n 호출           │        │
│                           │  3. 결과 GUI 표시      │        │
│                           └──────────┬────────────┘        │
└──────────────────────────────────────┼─────────────────────┘
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
│   ├── __init__.py          # 버전 정의 (__version__)
│   ├── main.py              # CLI 엔트리포인트
│   ├── config_manager.py    # 설정 파일 관리
│   ├── p4_client.py         # Perforce 명령어 래퍼
│   ├── n8n_client.py        # n8n HTTP 클라이언트
│   ├── expert_profiles.py   # 전문가 프로필 정의
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── description.py   # AI Description 생성 로직
│   │   ├── review.py        # AI 코드 리뷰 로직
│   │   └── install.py       # P4V Custom Tools 등록
│   └── ui/
│       ├── __init__.py
│       ├── dialogs.py       # GUI 다이얼로그 (tkinter)
│       └── report_generator.py  # HTML 리포트 생성
├── build/
│   ├── p4v_ai_assistant.spec  # PyInstaller 설정
│   └── sync_version.py      # 버전 동기화 스크립트
├── installer/
│   ├── installer.nsi        # NSIS 인스톨러 스크립트
│   └── license.txt          # 라이선스 파일
├── docs/
│   └── USER_MANUAL.md       # 사용자 매뉴얼
├── n8n/                     # n8n 워크플로우 JSON
├── dist/                    # 빌드 결과물
│   ├── p4v_ai_assistant.exe
│   └── P4V-AI-Assistant-Setup.exe
├── venv/                    # Python 가상환경
├── requirements.txt         # Python 의존성
├── build_all.bat            # 전체 빌드 스크립트
├── PLAN.md                  # 개발 계획
└── README.md
```

## 설치

### 인스톨러 사용 (권장)

1. `P4V-AI-Assistant-Setup.exe` 실행
2. Webhook URL 입력 (기본값 제공, 업그레이드 시 기존 설정 유지)
3. 설치 완료 후 **P4V 재시작**

> **참고**: 업그레이드 설치 시 기존 config.json이 있으면 Webhook URL 설정을 건너뛰고 모든 사용자 설정(커스텀 프롬프트 등)이 보존됩니다.

### 개발 환경 설정

#### 필수 요구사항

| 도구 | 버전 | 용도 | 설치 방법 |
|------|------|------|----------|
| Python | 3.8+ | 런타임 | [python.org](https://www.python.org/downloads/) |
| NSIS | 3.x | 인스톨러 빌드 | [nsis.sourceforge.io](https://nsis.sourceforge.io/Download) |
| Perforce CLI | - | p4 명령어 | P4V 설치 시 포함 |

> **NSIS 설치 참고**: NSIS 설치 후 `makensis.exe`가 PATH에 포함되어야 합니다. 기본 설치 경로는 `C:\Program Files (x86)\NSIS\`입니다.

#### 환경 구성

```bash
# 1. 저장소 클론
git clone <repository-url>
cd p4v-ai-assistant-v1

# 2. 가상환경 생성
python -m venv venv

# 3. 의존성 설치
venv\Scripts\pip install -r requirements.txt

# 4. (선택) P4V 컨텍스트 메뉴에 개발 버전 등록
venv\Scripts\python -m src.main install
```

#### 개발 모드 실행

```bash
# 가상환경 활성화
venv\Scripts\activate

# CLI 직접 실행
python -m src.main --version
python -m src.main description -c <CL번호>
python -m src.main review -c <CL번호>
```

### 설정 파일

위치: `%APPDATA%\P4V-AI-Assistant\config.json`
```json
{
  "webhook_url": "https://your-n8n-server/webhook/...",
  "timeout": 60,
  "language": "ko",
  "expert_profile": "generic",
  "custom_prompts": { "description": "", "review": "" }
}
```

## 사용법

### CLI 명령어

```bash
# 버전 확인
p4v_ai_assistant.exe --version

# AI Description 생성
p4v_ai_assistant.exe description --changelist <CL번호>

# AI 코드 리뷰
p4v_ai_assistant.exe review --changelist <CL번호>

# 설정 GUI
p4v_ai_assistant.exe settings

# P4V 도구 설치/제거
p4v_ai_assistant.exe install
p4v_ai_assistant.exe uninstall
```

### P4V에서 사용

1. P4V에서 Changelist 우클릭 (Pending, Submitted, History 모두 지원)
2. **"AI Description 생성"**: 코드 변경 분석 후 커밋 메시지 자동 생성
3. **"AI 코드 리뷰"**: 코드 리뷰 결과 GUI로 표시, HTML 내보내기 가능

## n8n 워크플로우

### 워크플로우 구조

```
Webhook → Switch (request_type) → description → AI Agent → Format → Respond
                                → review → AI Agent (+ Redis Memory) → Format → Respond
```

### API 요청 형식

```json
{
  "request_type": "description | review",
  "changelist": {
    "number": 12345,
    "user": "username",
    "client": "workspace",
    "current_description": "현재 설명"
  },
  "files": [...],
  "session_key": "cl_12345",      // 리뷰 배치 컨텍스트용
  "batch_info": { "current": 1, "total": 3 }
}
```

### API 응답 형식 (Description)

```json
{
  "success": true,
  "description": "[Feature] 기능 설명\n\n상세 내용...",
  "summary": "기능 요약"
}
```

### API 응답 형식 (Review)

```json
{
  "success": true,
  "summary": "전반적으로 양호한 코드입니다.",
  "overall_score": 78,
  "comments": [
    {
      "file_path": "//depot/.../file.cpp",
      "line_number": 125,
      "severity": "critical | warning | info | suggestion",
      "category": "bug | security | performance | style | maintainability",
      "message": "문제 설명",
      "suggestion": "수정 제안"
    }
  ],
  "statistics": { "critical": 0, "warning": 1, "info": 1, "suggestion": 1 }
}
```

## 기술 스택

| 구성 요소 | 기술 |
|-----------|------|
| 클라이언트 | Python 3.x + tkinter |
| 워크플로우 | n8n |
| AI | Google Gemini (사내 LLM) |
| 빌드 | PyInstaller (단일 exe) |
| 인스톨러 | NSIS |

## 빌드

### 전체 빌드

```bash
# 전체 빌드 (버전 동기화 → exe → 인스톨러)
build_all.bat
```

빌드 과정:
1. `build/sync_version.py` - `src/__init__.py`의 버전을 `installer.nsi`에 동기화
2. PyInstaller - `run.py`를 단일 exe로 패키징
3. NSIS - 인스톨러 생성 (`makensis.exe` 필요)

출력:
- `dist/p4v_ai_assistant.exe` (~15MB)
- `dist/P4V-AI-Assistant-Setup.exe` (~15MB)

### 개별 빌드

```bash
# exe만 빌드 (인스톨러 없이)
venv\Scripts\pyinstaller build/p4v_ai_assistant.spec --distpath dist --workpath build/temp --noconfirm

# 인스톨러만 빌드 (exe가 이미 있을 때)
makensis installer/installer.nsi
```

> **주의**: 인스톨러 빌드 시 NSIS가 설치되어 있어야 합니다. [NSIS 다운로드](https://nsis.sourceforge.io/Download)

## 의존성

- Python 3.8+
- requests >= 2.28.0
- tkinter (Python 기본 포함)

## 변경 이력

### v0.4.2
- 업그레이드 시 사용자 설정 보존 (커스텀 프롬프트 등)

### v0.4.1
- 타임아웃 설정값 미적용 버그 수정

### v0.4.0
- Submitted, History 뷰 컨텍스트 메뉴 지원 (%p → %c)
- CLI --version 옵션 추가
- 설정 다이얼로그에 버전 표시
- 버전 관리 시스템 구현 (단일 소스)

### v0.3.0
- 전문가 프로필 기능 (Unity, Unreal, 범용)
- NSIS 인스톨러

### v0.2.0
- AI 코드 리뷰 기능
- HTML 리포트 생성
- 배치 처리 + Redis Memory 컨텍스트 유지

### v0.1.0
- AI Description 생성 기능
- P4V Custom Tools 연동
- PyInstaller 빌드

## 라이선스

Copyright (c) 2026 Netmarble Neo
Created by Naya
