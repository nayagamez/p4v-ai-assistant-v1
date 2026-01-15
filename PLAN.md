# P4V AI Assistant - 개발 계획

## 현재 상태 (v0.4.0)

### 완료된 기능
- [x] 프로젝트 기본 구조 설정
- [x] CLI 엔트리포인트 (main.py)
- [x] 설정 관리 (config_manager.py)
- [x] Perforce 명령어 래퍼 (p4_client.py)
- [x] n8n HTTP 클라이언트 (n8n_client.py)
- [x] AI Description 생성 기능 (commands/description.py)
- [x] P4V Custom Tools 설치/제거 (commands/install.py)
- [x] GUI 다이얼로그 - tkinter (ui/dialogs.py)
- [x] n8n 워크플로우 구성 (Gemini 연동)
- [x] **AI 코드 리뷰 기능** (commands/review.py)
- [x] **HTML 리포트 생성** (ui/report_generator.py)
- [x] **배치 처리 + Redis Memory 컨텍스트 유지**
- [x] **PyInstaller 빌드** (dist/p4v_ai_assistant.exe)
- [x] **커스텀 전문가 프롬프트** (Unity, Unreal, 범용)
- [x] **NSIS 인스톨러** (dist/P4V-AI-Assistant-Setup.exe)
- [x] **버전 관리 시스템** (src/__init__.py → installer.nsi 동기화)
- [x] **CLI --version 옵션**
- [x] **Submitted, History 뷰 컨텍스트 메뉴 지원** (%p → %c)

---

## Phase 1: AI 코드 리뷰 기능 ✅ 완료

### 목표
Changelist의 코드 변경 사항을 AI가 분석하여 잠재적 문제점을 리포트

### 완료된 작업
- [x] `commands/review.py` - 코드 리뷰 로직 구현
- [x] `ui/report_generator.py` - HTML 리포트 템플릿
- [x] n8n 리뷰 워크플로우 구성 (Switch 노드로 분기)
- [x] P4V 컨텍스트 메뉴에 "AI 코드 리뷰" 추가
- [x] main.py에 `review` 서브커맨드 추가
- [x] 배치 분할 처리 (MAX_FILES: 50, MAX_LINES: 5000)
- [x] Redis Chat Memory로 배치 간 컨텍스트 유지

### API 응답 형식
```json
{
  "success": true,
  "summary": "전반적으로 양호한 코드입니다.",
  "overall_score": 78,
  "comments": [
    {
      "file_path": "//depot/.../file.cpp",
      "line_number": 125,
      "severity": "warning",
      "category": "best_practice",
      "message": "문제 설명",
      "suggestion": "수정 제안"
    }
  ],
  "statistics": {
    "critical": 0,
    "warning": 1,
    "info": 1,
    "suggestion": 1
  }
}
```

---

## Phase 2: PyInstaller 빌드 ✅ 완료

### 목표
Python 스크립트를 단일 exe 파일로 패키징

### 완료된 작업
- [x] `build/build.py` - PyInstaller 빌드 스크립트
- [x] `build/p4v_ai_assistant.spec` - PyInstaller 설정 파일
- [x] `run.py` - 엔트리포인트
- [x] `build.bat` - 원클릭 빌드 배치 파일
- [x] 빌드 테스트 및 검증

### 빌드 명령
```bash
build.bat
# 출력: dist/p4v_ai_assistant.exe (~15MB)
```

---

## Phase 2.5: 커스텀 전문가 프롬프트 ✅ 완료

### 목표
팀별로 다른 전문가 컨텍스트를 AI에게 제공

### 완료된 작업
- [x] `src/expert_profiles.py` - 기본 프로필 정의
- [x] 설정 다이얼로그 확장 (프로필 선택, 프롬프트 편집)
- [x] n8n payload에 expert_context 추가
- [x] n8n 시스템 메시지에 동적 컨텍스트 추가

### 지원 프로필
| 프로필 | 대상 |
|--------|------|
| 범용 전문가 | 기본값, 추가 컨텍스트 없음 |
| Unity 2021.3 전문가 | C#, MonoBehaviour, DOTS 등 |
| Unreal 5.7 전문가 | C++, UObject, Blueprint 등 |

---

## Phase 3: NSIS 인스톨러 ✅ 완료

### 목표
사용자가 원클릭으로 설치할 수 있는 Windows 인스톨러 생성

### 완료된 작업
- [x] `installer/installer.nsi` - NSIS 스크립트
- [x] `installer/license.txt` - 라이선스 파일
- [x] `installer/build_installer.bat` - 인스톨러 빌드 스크립트
- [x] 설치 시 Webhook URL 입력 다이얼로그 (기본값 포함)
- [x] 자동 P4V Custom Tools 등록
- [x] 시작 메뉴 바로가기 생성
- [x] 언인스톨러 구현
- [x] 프로그램 추가/제거에 등록

### 인스톨러 빌드
```bash
cd installer && build_installer.bat
# 출력: dist/P4V-AI-Assistant-Setup.exe (~15MB)
```

---

## Phase 3.5: 버전 관리 시스템 ✅ 완료

### 목표
버전을 단일 소스에서 관리하고, 빌드 시 자동으로 인스톨러에 반영

### 완료된 작업
- [x] `src/__init__.py`에 `__version__` 정의 (단일 소스)
- [x] `build/sync_version.py` - 버전 동기화 스크립트
- [x] `build_all.bat` - 버전 동기화 단계 추가
- [x] CLI `--version` 옵션 추가
- [x] 설정 다이얼로그 하단에 버전 표시
- [x] 인스톨러 타이틀에 버전 표시
- [x] `%p` → `%c` 변경 (Submitted, History 뷰 컨텍스트 메뉴 지원)

---

## Phase 4: 추가 개선사항

### 기능 개선 (우선순위 높음)
- [x] **Add 파일 전체 내용 리뷰** - 새로 추가된 파일은 diff 대신 전체 내용을 전송하여 리뷰
- [x] **Description 생성 후 미리보기 → 적용 확인** - DescriptionDialog에서 미리보기 후 적용 버튼
- [ ] 코드 리뷰 결과 P4V 주석으로 추가 옵션
- [ ] 여러 Changelist 일괄 처리

### UI/UX 개선
- [ ] 진행률 표시 개선 (퍼센트 표시)
- [ ] 설정 GUI 개선 (더 많은 옵션)
- [ ] 다크 모드 지원

### 안정성
- [ ] 로깅 시스템 추가
- [ ] 에러 리포팅 기능
- [ ] 자동 업데이트 체크

---

## 기술 부채

- [ ] 단위 테스트 추가
- [ ] 타입 힌트 보완
- [ ] docstring 보완
- [ ] 코드 리팩토링 (필요시)

---

## 참고 자료

- [Perforce P4 명령어 레퍼런스](https://www.perforce.com/manuals/cmdref/Content/CmdRef/Home-cmdref.html)
- [P4V Custom Tools 설정](https://help.perforce.com/helix-core/server-apps/p4v/current/Content/P4V/advanced_options.custom.html)
- [PyInstaller 문서](https://pyinstaller.org/)
- [NSIS 문서](https://nsis.sourceforge.io/Docs/)
- [n8n 문서](https://docs.n8n.io/)
