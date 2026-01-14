# P4V AI Assistant - HTML 리포트 확장 기능 명세서

## 1. 프로젝트 개요

### 1.1 현재 시스템
P4V(Perforce Visual Client)의 Changelist 컨텍스트 메뉴에서 AI 코드 리뷰 기능을 제공하는 도구.

```
현재 아키텍처:
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

### 1.2 현재 출력 방식
- **tkinter GUI**: 리뷰 결과 요약 리스트 표시
- **HTML 리포트**: 상세 내용 내보내기 (점수, 통계, 코멘트 목록)

### 1.3 개선 목표
현재는 diff만 제공되어 코드를 다시 열어봐야 하는 불편함이 있음. 다음을 통합한 HTML 리포트로 개선:
- Perforce 스트림에서 두 파일 버전(이전/현재)을 불러와 **Side-by-side diff 뷰** 제공
- diff 위에 **AI 코멘트를 인라인으로 표시**
- 코드 리뷰에 필요한 **네비게이션 및 필터 기능** 제공

---

## 2. 기술 스택 및 의존성

### 2.1 기존 기술 스택
| 구성 요소 | 기술 |
|-----------|------|
| 클라이언트 | Python 3.8+ |
| GUI | tkinter |
| HTTP 클라이언트 | requests |
| 워크플로우 | n8n |
| AI | Google Gemini (사내 LLM) |
| 배포 예정 | PyInstaller + NSIS |

### 2.2 추가 기술 (HTML 리포트용)
| 구성 요소 | 기술 | 비고 |
|-----------|------|------|
| Diff 렌더링 | diff2html | CSS/JS 인라인 번들링 |
| Diff 계산 | Python difflib (백업) | 외부 의존성 없음 |

### 2.3 diff2html 통합 방식
사내망 환경에서 오프라인 동작을 보장하기 위해 **CSS/JS 인라인 번들링** 방식 채택:

```python
# report_generator.py 구조
DIFF2HTML_CSS = """/* diff2html.min.css 내용 (~15KB) */"""
DIFF2HTML_JS = """/* diff2html-ui.min.js 내용 (~80KB) */"""

HTML_TEMPLATE = f"""
<!DOCTYPE html>
<html>
<head>
    <style>{DIFF2HTML_CSS}</style>
</head>
<body>
    ...
    <script>{DIFF2HTML_JS}</script>
</body>
</html>
"""
```

- 장점: HTML 파일 하나로 완결, 어디서든 열람 가능
- 단점: 파일 크기 증가 (100~150KB)

---

## 3. 프로젝트 구조

### 3.1 기존 구조
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
│   │   ├── review.py        # AI 코드 리뷰 로직
│   │   └── install.py       # P4V Custom Tools 등록
│   └── ui/
│       ├── __init__.py
│       ├── dialogs.py       # GUI 다이얼로그 (tkinter)
│       └── report_generator.py  # HTML 리포트 생성
├── requirements.txt
└── README.md
```

### 3.2 확장 후 구조 (예상)
```
p4v-ai-assistant-v1/
├── src/
│   ├── ...
│   ├── p4_client.py         # ← 파일 내용 조회 메서드 추가
│   └── ui/
│       ├── ...
│       ├── report_generator.py  # ← 대폭 확장
│       └── assets/              # ← 새로 추가
│           ├── diff2html.min.css
│           └── diff2html-ui.min.js
```

---

## 4. 데이터 구조

### 4.1 Perforce 데이터 (기존)

```python
@dataclass
class FileChange:
    """변경된 파일 정보"""
    depot_path: str      # //depot/path/to/file.cpp
    action: str          # add, edit, delete, branch, integrate, move/add, move/delete
    file_type: str       # text, binary
    revision: int        # 리비전 번호
    diff: str            # unified diff 형식의 변경 내용

@dataclass
class ChangelistInfo:
    """Changelist 정보"""
    number: int
    user: str
    client: str
    status: str          # pending, submitted
    description: str
    files: List[FileChange]
```

### 4.2 AI 리뷰 응답 형식

```json
{
  "success": true,
  "summary": "전반적으로 양호한 코드입니다.",
  "overall_score": 78,
  "comments": [
    {
      "file_path": "//depot/src/main.cpp",
      "line_number": 125,
      "severity": "critical | warning | info | suggestion",
      "category": "bug | security | performance | style | maintainability",
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

### 4.3 diff2html 입력 형식
diff2html은 **unified diff 형식**을 입력으로 받음:

```diff
--- a/depot/src/main.cpp
+++ b/depot/src/main.cpp
@@ -120,6 +120,8 @@
 context line
-removed line
+added line
 context line
```

**주의**: 현재 `file_change.diff`에 헤더(`--- a/...`, `+++ b/...`)가 없을 수 있음. 없으면 생성 시 추가 필요.

---

## 5. 기존 p4_client.py 분석

### 5.1 현재 구현된 메서드

| 메서드 | 설명 | 사용하는 p4 명령어 |
|--------|------|-------------------|
| `get_changelist_info()` | CL 기본 정보 조회 | `p4 describe -s` |
| `get_changelist_with_diff()` | CL 정보 + diff | `p4 describe -du`, `p4 diff -du` |
| `_collect_pending_diffs()` | pending CL의 파일별 diff 수집 | `p4 diff -du` |
| `_get_new_file_content()` | 새 파일 내용 조회 | `p4 print -q "path@=CL"` |
| `update_changelist_description()` | CL 설명 업데이트 | `p4 change -i` |

### 5.2 추가 필요한 메서드

```python
def get_file_content(self, depot_path: str, revision: int) -> str:
    """특정 리비전의 파일 내용 조회"""
    return self._run("print", "-q", f"{depot_path}#{revision}")

def get_shelved_content(self, depot_path: str, changelist: int) -> str:
    """Shelved 파일 내용 조회"""
    return self._run("print", "-q", f"{depot_path}@={changelist}")

def get_have_revision(self, depot_path: str) -> Optional[int]:
    """로컬 have 리비전 확인"""
    output = self._run("have", depot_path)
    # 파싱 로직...
    return revision
```

### 5.3 파일 버전 조회 시나리오

| CL 상태 | 이전 버전 | 현재 버전 |
|---------|-----------|-----------|
| pending (edit) | `p4 print "path#have"` | 로컬 파일 또는 shelved |
| pending (add) | (없음) | 로컬 파일 또는 shelved |
| pending (delete) | `p4 print "path#have"` | (없음) |
| submitted | `p4 print "path#(rev-1)"` | `p4 print "path#rev"` |

---

## 6. HTML 리포트 UI 설계

### 6.1 전체 레이아웃

```
┌─────────────────────────────────────────────────────────────────┐
│ 🔍 필터: [전체 ▼] [Critical ✓] [Warning ✓] [Info ☐]            │
│ 📍 이동: [◀ 이전 코멘트] [다음 코멘트 ▶] (3/12)                │
│ 👁 보기: [코드 접기 ✓] [코멘트만 보기 ☐]                       │
├─────────────────────────────────────────────────────────────────┤
│ [📊 Summary] [main.cpp 🔴2] [util.h ⚠️1] [config.py ✓]         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                     (탭별 콘텐츠 영역)                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 탭 구조

#### Summary 탭 (기존 내용 유지)
```
┌─────────────────────────────────────────┐
│           점수: 78 / 100                │
├─────────────────────────────────────────┤
│ 📝 요약                                 │
│ 전반적으로 양호한 코드입니다...          │
├─────────────────────────────────────────┤
│ 📊 통계                                 │
│ [Critical: 0] [Warning: 1] [Info: 1]    │
├─────────────────────────────────────────┤
│ 📋 전체 코멘트 목록                      │
│ - main.cpp:125 ⚠️ null 체크...          │
│ - util.h:42 💡 변수명 개선...            │
└─────────────────────────────────────────┘
```

#### 파일 탭 (신규)
```
┌─────────────────────────────────────────────────────────────────┐
│ ▲▼ 변경점 이동    💬 N/P 코멘트 이동                            │
├────────────────────────┬────────────────────────────────────────┤
│      이전 버전         │           현재 버전                    │
│      (have rev)        │        (workspace/shelved)             │
├────────────────────────┴────────────────────────────────────────┤
│ 120 │ int result = 0;        │ 120 │ int result = 0;           │
│ 121 │ if (ptr) {             │ 121 │ if (ptr) {                │
│ 122 │   process(ptr);        │ 122 │   process(ptr);           │
│     │                        │ 123+│   validate(ptr);          │
├─────┴────────────────────────┴─────┴────────────────────────────┤
│ ⚠️ WARNING (Line 123)                                           │
│ validate() 호출 전 ptr null 체크가 필요합니다.                   │
│ 💡 제안: if (ptr && ptr->isValid()) 패턴 적용                   │
└─────────────────────────────────────────────────────────────────┘
```

### 6.3 코멘트만 보기 모드

```
┌─────────────────────────────────────────────────────────────────┐
│ 파일: //depot/src/main.cpp                                      │
├─────────────────────────────────────────────────────────────────┤
│ Line 125 🔴 CRITICAL                                            │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 125 │ delete buffer;                                        │ │
│ └─────────────────────────────────────────────────────────────┘ │
│ double free 가능성이 있습니다.                                   │
│ 💡 제안: buffer = nullptr 추가                                  │
├─────────────────────────────────────────────────────────────────┤
│ Line 340 ⚠️ WARNING                                             │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 340 │ if (ptr == null) {                                    │ │
│ └─────────────────────────────────────────────────────────────┘ │
│ null 체크 후 ptr 사용하는 곳에서 다시 체크 필요                  │
│ 💡 제안: guard clause 패턴 적용                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. 기능 명세

### 7.1 MVP (1차 구현)

| 기능 | 설명 | 구현 방식 |
|------|------|-----------|
| 탭 구조 | Summary + 파일별 탭 | HTML + CSS + 간단한 JS |
| Side-by-side diff | 두 버전 비교 뷰 | diff2html 라이브러리 |
| 코멘트 인라인 표시 | diff 내 해당 라인에 코멘트 삽입 | JS로 DOM 조작 |
| 변경점 이동 (▲▼) | 다음/이전 diff 청크로 이동 | diff2html 기본 기능 활용 |
| 코멘트 이동 (N/P) | 다음/이전 AI 코멘트로 이동 | Custom JS |

### 7.2 2차 구현

| 기능 | 설명 | 구현 방식 |
|------|------|-----------|
| 심각도 필터 | Critical/Warning/Info/Suggestion 토글 | JS 필터링 |
| 코드 접기/펼치기 | 변경 없는 부분 숨기기 | diff2html outputFormat 옵션 |
| 코멘트만 보기 모드 | 코드 숨기고 코멘트만 리스트 | 별도 뷰 모드 |
| 전체 펼치기/접기 | 한 번에 모든 코드 토글 | JS 일괄 처리 |

### 7.3 3차 구현 (Nice to Have)

| 기능 | 설명 | 구현 방식 |
|------|------|-----------|
| 키보드 단축키 | J/K(변경점), N/P(코멘트), E(펼치기), 1-4(필터) | JS 이벤트 리스너 |
| 미니맵 | 스크롤바 옆 코멘트 위치 시각화 | Custom CSS + JS |
| Side-by-side ↔ Unified 토글 | 뷰 모드 전환 | diff2html 옵션 변경 |
| 파일 트리 사이드바 | 파일 많을 때 탐색 편의 | 별도 사이드 패널 |
| 탭에 통계 뱃지 | 파일명 옆에 이슈 개수 표시 | 탭 생성 시 계산 |

---

## 8. 구현 계획

### Phase 1: 기반 작업

```
1. diff2html CSS/JS 파일 다운로드 및 인라인화
2. HTML 템플릿 구조 변경 (탭 UI 추가)
3. p4_client.py에 파일 내용 조회 메서드 추가
```

### Phase 2: diff 렌더링

```
1. 파일별 unified diff 생성 (헤더 포함)
2. diff2html로 Side-by-side 렌더링
3. 탭 전환 로직 구현
```

### Phase 3: AI 코멘트 통합

```
1. line_number 기준 코멘트 매핑 로직
2. diff 렌더링 후 코멘트 DOM 삽입 (JS)
3. 코멘트 스타일링 (severity별 색상)
```

### Phase 4: 네비게이션

```
1. 변경점 이동 기능 (diff2html 활용)
2. 코멘트 이동 기능 (Custom JS)
3. 현재 위치 표시 (3/12)
```

### Phase 5: 필터 및 뷰 옵션

```
1. 심각도 필터 UI 및 로직
2. 코드 접기/펼치기
3. 코멘트만 보기 모드
```

---

## 9. 기술적 고려사항

### 9.1 diff 헤더 생성
현재 `file_change.diff`에 헤더가 없을 수 있으므로 생성 시 추가:

```python
def format_unified_diff(file_change: FileChange) -> str:
    """diff2html 호환 unified diff 형식 생성"""
    header = f"--- a{file_change.depot_path}\n+++ b{file_change.depot_path}\n"
    return header + file_change.diff
```

### 9.2 line_number 매핑
AI 코멘트의 `line_number`가 어느 기준인지 확인 필요:
- **원본 파일 기준**: 이전 버전의 라인 번호
- **새 파일 기준**: 현재 버전의 라인 번호
- **diff 청크 기준**: diff 내의 상대 위치

diff2html 렌더링 후 DOM에서 해당 라인을 찾아 코멘트 삽입.

### 9.3 대용량 파일 처리
- 파일이 수천 줄일 경우 전체 렌더링은 성능 이슈 발생 가능
- **권장**: 변경 부분 ± N줄 컨텍스트만 표시 (diff2html의 `context` 옵션 활용)

### 9.4 바이너리 파일 처리
- 바이너리 파일(이미지, 실행파일 등)은 diff 불가
- "(바이너리 파일)" 표시 처리 필요

### 9.5 인코딩 처리
- UTF-8이 아닌 파일 처리 (예: EUC-KR)
- `p4 print`의 인코딩 옵션 및 Python `errors="replace"` 활용

---

## 10. 예상 결과물

### 10.1 파일 변경사항

| 파일 | 변경 내용 |
|------|-----------|
| `p4_client.py` | `get_file_content()`, `get_shelved_content()`, `get_have_revision()` 추가 |
| `report_generator.py` | 전면 재작성 (탭 UI, diff2html 통합, 코멘트 렌더링) |
| `ui/assets/` | diff2html CSS/JS 파일 추가 (또는 인라인) |

### 10.2 HTML 리포트 사양

| 항목 | 값 |
|------|-----|
| 예상 파일 크기 | 100~150KB (기본) + diff 내용 |
| 외부 의존성 | 없음 (오프라인 동작) |
| 지원 브라우저 | Chrome, Edge, Firefox (최신 버전) |

---

## 11. 체크리스트

### 구현 전 확인사항
- [ ] 현재 `file_change.diff` 형식 확인 (헤더 유무)
- [ ] diff2html 단독 테스트 (간단한 HTML로)
- [ ] AI 코멘트 `line_number`가 어느 기준인지 확인
- [ ] 사내망에서 diff2html CDN 접근 가능 여부 (불가 시 인라인 확정)

### MVP 완료 기준
- [ ] Summary 탭 + 파일별 탭 전환 동작
- [ ] Side-by-side diff 렌더링 정상 표시
- [ ] AI 코멘트가 해당 라인에 인라인 표시
- [ ] 변경점 이동 (▲▼) 동작
- [ ] 코멘트 이동 (N/P) 동작

---

## 12. 참고 자료

### 12.1 diff2html
- 공식 문서: https://diff2html.xyz/
- GitHub: https://github.com/rtfpessoa/diff2html
- CDN: https://cdn.jsdelivr.net/npm/diff2html/

### 12.2 Perforce 명령어
```bash
# 특정 리비전 파일 내용
p4 print -q "//depot/path/file.cpp#3"

# Shelved 파일 내용
p4 print -q "//depot/path/file.cpp@=12345"

# 로컬 have 리비전 확인
p4 have "//depot/path/file.cpp"

# Pending CL diff
p4 diff -du //depot/path/file.cpp

# Submitted CL diff
p4 describe -du 12345
```

### 12.3 키보드 단축키 (구현 시 참고)

| 키 | 동작 |
|----|------|
| `J` | 다음 변경점 |
| `K` | 이전 변경점 |
| `N` | 다음 코멘트 |
| `P` | 이전 코멘트 |
| `E` | 코드 펼치기/접기 토글 |
| `1` | Critical 필터 토글 |
| `2` | Warning 필터 토글 |
| `3` | Info 필터 토글 |
| `4` | Suggestion 필터 토글 |
| `0` | 전체 필터 초기화 |
