# P4V AI Assistant 기술 가이드

P4V AI Assistant가 AI를 어떻게 활용하여 커밋 메시지를 생성하고 코드를 리뷰하는지 설명합니다.

---

## 목차

1. [들어가며: AI가 코드를 어떻게 이해할까?](#1-들어가며-ai가-코드를-어떻게-이해할까)
2. [첫 번째 도전: AI에게 얼마나 많은 코드를 보여줄 수 있을까?](#2-첫-번째-도전-ai에게-얼마나-많은-코드를-보여줄-수-있을까)
3. [두 번째 도전: AI도 긴 글을 읽으면 집중력이 떨어진다](#3-두-번째-도전-ai도-긴-글을-읽으면-집중력이-떨어진다)
4. [해결책: 나눠서 보여주고 기억을 이어주기](#4-해결책-나눠서-보여주고-기억을-이어주기)
5. [기억을 이어주는 방법: Redis Memory](#5-기억을-이어주는-방법-redis-memory)
6. [AI의 창의성 조절하기: Temperature 설정](#6-ai의-창의성-조절하기-temperature-설정)
7. [도메인 전문가 프로필](#7-도메인-전문가-프로필)
8. [JSON 규약: 확장 가능한 설계](#8-json-규약-확장-가능한-설계)
9. [마치며](#9-마치며)
10. [참고 자료](#10-참고-자료)

---

## 1. 들어가며: AI가 코드를 어떻게 이해할까?

### LLM(Large Language Model)이란?

LLM은 "대규모 언어 모델"의 약자입니다. 쉽게 말해, **엄청나게 많은 텍스트를 읽고 학습한 AI**입니다.

이 AI는 인터넷의 책, 문서, 코드 등 수십억 개의 문장을 학습했습니다. 그래서 사람처럼 문장을 이해하고, 질문에 답하고, 글을 작성할 수 있습니다.

### 코드도 텍스트다

프로그래밍 코드도 결국 텍스트입니다. AI는 코드를 "특별한 규칙을 가진 언어"로 인식합니다.

```cpp
void Player::TakeDamage(int amount) {
    health -= amount;
    if (health <= 0) {
        Die();
    }
}
```

AI는 이 코드를 읽고 "플레이어가 데미지를 받으면 체력이 감소하고, 0 이하가 되면 사망한다"라고 이해할 수 있습니다.

### 이 시스템이 하는 일

P4V AI Assistant는 다음 두 가지 기능을 제공합니다:

1. **커밋 메시지 자동 생성**: 변경된 코드를 분석해서 적절한 커밋 메시지를 작성
2. **AI 코드 리뷰**: 코드의 버그, 성능 문제, 보안 취약점 등을 찾아서 피드백 제공

---

## 2. 첫 번째 도전: AI에게 얼마나 많은 코드를 보여줄 수 있을까?

### 토큰이란?

AI는 텍스트를 "토큰"이라는 작은 단위로 나누어 처리합니다. 토큰은 단어, 글자, 또는 기호가 될 수 있습니다.

대략적인 토큰 계산:
- 한글 1글자 = 약 1~2 토큰
- 영어 단어 1개 = 약 1 토큰
- 코드 1줄 = 약 3~10 토큰

예를 들어, 1,000줄짜리 코드 파일은 대략 3,000~10,000 토큰 정도입니다.

### Gemini 모델의 토큰 한계

P4V AI Assistant는 Google의 Gemini 모델을 사용합니다.

| 모델 | 읽을 수 있는 양 | 실제 코드로 환산 |
|------|---------------|-----------------|
| Gemini 3 Pro | 100만 토큰 | 약 30,000줄 |
| Gemini 2.5 Pro | 100만 토큰 | 약 30,000줄 |
| Gemini 1.5 Pro | 200만 토큰 | 약 60,000줄 |

"그러면 30,000줄까지는 한 번에 보여줘도 되지 않나요?"

**정답은 "아니오"입니다.**

다음 섹션에서 그 이유를 설명합니다.

---

## 3. 두 번째 도전: AI도 긴 글을 읽으면 집중력이 떨어진다

### Context Rot 현상

사람이 긴 문서를 읽을 때 앞부분 내용을 잊어버리는 것처럼, AI도 입력이 길어지면 비슷한 현상이 발생합니다. 이를 **Context Rot**(컨텍스트 부패)이라고 부릅니다.

Chroma Research의 연구 결과에 따르면:

- 128,000 토큰(약 40,000줄)을 입력해도 AI가 실제로 잘 기억하는 부분은 훨씬 적음
- AI가 최근에 읽은 내용에만 집중하고, 앞부분은 잊어버리는 경향이 있음
- 이로 인해 "할루시네이션"이 증가함

### 할루시네이션이란?

할루시네이션(Hallucination)은 **AI가 없는 내용을 마치 사실처럼 지어내는 현상**입니다.

예를 들어:
- "이 함수는 10번 줄에서 null 체크를 합니다" (실제로는 null 체크가 없음)
- "이 클래스는 Singleton 패턴을 사용합니다" (실제로는 다른 패턴임)

긴 입력에서 AI가 앞부분 내용을 정확히 기억하지 못하면, 없는 내용을 추측해서 답변하게 됩니다.

### 왜 이런 현상이 발생할까요?

1. **위치 학습 부족**: AI가 학습할 때 매우 긴 문서를 많이 보지 못했습니다. 대부분의 학습 데이터는 상대적으로 짧은 문서들입니다.

2. **인코딩 포화**: AI 내부에서 정보를 저장하는 공간이 한정되어 있습니다. 너무 많은 정보를 한 번에 넣으면 정보가 서로 섞이거나 뭉개집니다.

3. **주의력 분산**: AI의 "주의력" 메커니즘(Attention)이 너무 많은 곳에 분산됩니다. 마치 사람이 여러 대화를 동시에 들으면 집중하기 어려운 것과 비슷합니다.

### 100만 토큰이 있어도 배치를 나누는 이유

1. **할루시네이션 증가**: 긴 컨텍스트에서 AI가 "자신감 있게 틀린 답변"을 생성할 확률이 높아집니다.

2. **분석 품질 저하**: 연구에 따르면 "유효 컨텍스트는 명목 길이보다 훨씬 작게 확장된다"고 합니다.

3. **응답 시간 증가**: 토큰이 많을수록 AI가 처리하는 시간이 기하급수적으로 늘어납니다.

4. **비용 증가**: API 요금은 토큰 수에 비례합니다. 불필요하게 긴 입력은 비용 낭비입니다.

---

## 4. 해결책: 나눠서 보여주고 기억을 이어주기

### 배치 처리란?

대용량 Changelist를 작은 단위로 나눠서 AI에게 순차적으로 보여주는 방식입니다.

P4V AI Assistant의 배치 분할 기준:

```python
# src/commands/review.py
MAX_FILES_PER_BATCH = 50      # 파일 50개마다 나눔
MAX_LINES_PER_BATCH = 5000    # 또는 5,000줄마다 나눔
```

### 배치 분할 예시

200개 파일이 변경된 Changelist가 있다고 가정해봅시다:

| 배치 | 파일 범위 | 설명 |
|------|----------|------|
| 배치 1 | 파일 1~50번 | 첫 번째 배치로 AI에게 전송 |
| 배치 2 | 파일 51~100번 | 두 번째 배치로 전송 |
| 배치 3 | 파일 101~150번 | 세 번째 배치로 전송 |
| 배치 4 | 파일 151~200번 | 마지막 배치로 전송 |

이렇게 4번에 나눠서 AI에게 보여주고, 각 배치의 리뷰 결과를 합칩니다.

### 배치 분할 알고리즘

실제 코드에서 배치를 어떻게 분할하는지 간략히 설명합니다:

```python
def _split_into_batches(self, files):
    # 파일 수와 총 라인 수 계산
    total_files = len(files)
    total_lines = sum(파일별 diff 라인 수)

    # 분할이 필요 없으면 전체를 1개 배치로
    if total_files <= 50 and total_lines <= 5000:
        return [files]

    # 파일을 순회하며 배치 구성
    batches = []
    current_batch = []
    current_lines = 0

    for file in files:
        file_lines = len(file.diff.split('\n'))

        # 임계값 초과 시 새 배치 시작
        if len(current_batch) >= 50 or current_lines + file_lines > 5000:
            batches.append(current_batch)
            current_batch = []
            current_lines = 0

        current_batch.append(file)
        current_lines += file_lines

    return batches
```

### 그런데 문제가 있습니다

배치 1에서 본 내용을 배치 2에서 AI가 기억하지 못합니다!

예를 들어:
- 배치 1에서 `GameManager.cpp`의 `Initialize()` 함수를 분석
- 배치 2에서 `Player.cpp`가 `GameManager::Initialize()`를 호출하는 코드가 있음
- AI는 배치 1의 내용을 모르므로, `Initialize()` 함수가 어떤 일을 하는지 알 수 없음

파일 간에 서로 연관이 있을 수 있는데, 이전 배치 내용을 모르면 제대로 된 리뷰가 어렵습니다.

---

## 5. 기억을 이어주는 방법: Redis Memory

### Redis란?

Redis는 **데이터를 메모리에 저장하는 고속 저장소**입니다. 파일에 저장하는 것보다 훨씬 빠르게 데이터를 읽고 쓸 수 있습니다.

P4V AI Assistant는 n8n 워크플로우에서 Redis를 활용하여 AI의 "대화 기억"을 저장합니다.

### 동작 방식

n8n 워크플로우의 Redis Chat Memory 설정:

```json
{
  "sessionKey": "cl_12345",      // Changelist 번호 기반 세션 키
  "sessionTTL": 900,             // 15분(900초) 후 자동 삭제
  "contextWindowLength": 50      // 최근 50개 메시지 저장
}
```

#### 1단계: 배치 1 처리

```
[클라이언트] → "배치 1 (파일 1~50) 리뷰해줘"
[AI] → "배치 1 분석 완료. GameManager 초기화 로직 확인..."
[Redis] → 대화 내용 저장 (키: cl_12345)
```

#### 2단계: 배치 2 처리

```
[클라이언트] → "배치 2 (파일 51~100) 리뷰해줘"
[Redis] → 이전 대화 내용 불러옴
[AI] → "이전에 분석한 GameManager와 연관된 Player 클래스 확인..."
[Redis] → 새 대화 내용 추가 저장
```

#### 3단계: 자동 정리

- 15분(900초) 후 Redis에서 세션 데이터가 자동 삭제됩니다
- 불필요한 메모리 낭비를 방지합니다

### 세션 키의 역할

```python
session_key = f"cl_{changelist_number}"  # 예: "cl_12345"
```

같은 Changelist의 모든 배치는 **동일한 세션 키**를 사용합니다. 이를 통해:

- 배치 1, 2, 3, 4가 모두 같은 "대화"로 연결됩니다
- AI가 이전 배치에서 분석한 내용을 참조할 수 있습니다
- 파일 간 연관성을 파악한 더 정확한 리뷰가 가능합니다

---

## 6. AI의 창의성 조절하기: Temperature 설정

### Temperature란?

Temperature는 **AI가 답변할 때 얼마나 "모험적"으로 답변할지 결정하는 설정**입니다.

쉬운 비유로 설명하면:
- **낮은 Temperature (0.0~0.3)** = 교과서적인 모범생. 항상 가장 확실한 답변만 합니다.
- **높은 Temperature (0.8~1.0)** = 창의적인 예술가. 때로는 예상치 못한 답변을 합니다.

### 기술적 원리

AI는 다음 단어(토큰)를 예측할 때 여러 후보 중에서 선택합니다.

예를 들어, "이 코드는 ___"라는 문장에서 다음 단어 후보가:
- "버그가" (40% 확률)
- "최적화가" (30% 확률)
- "아름답게" (20% 확률)
- "재미있게" (10% 확률)

**Temperature가 낮으면 (0.2)**:
- AI가 가장 확률 높은 "버그가"를 거의 항상 선택합니다

**Temperature가 높으면 (1.0)**:
- AI가 확률이 낮은 단어도 선택할 수 있습니다
- "아름답게"나 "재미있게" 같은 예상치 못한 표현이 나올 수 있습니다

### Temperature 범위별 특성

| 범위 | AI의 성격 | 적합한 작업 |
|------|----------|------------|
| 0.0~0.3 | 신중하고 일관됨 | 코드 리뷰, 버그 분석, 기술 문서 |
| 0.4~0.7 | 균형 잡힌 | 일반적인 대화, 요약 |
| 0.8~1.0 | 창의적 | 아이디어 브레인스토밍, 스토리 작성 |
| 1.0 이상 | 매우 무작위 | 권장하지 않음 (할루시네이션 급증) |

### P4V AI Assistant의 설정

n8n 워크플로우에서 실제로 사용하는 값:

**코드 리뷰: Temperature 0.2**
```json
{
  "modelName": "models/gemini-3-pro-preview",
  "options": {
    "temperature": 0.2
  }
}
```
- 이유: 버그를 찾는 일은 **정확해야** 합니다. 창의적인 해석은 불필요합니다.
- "이 코드에 버그가 있다"라고 말할 때, 정말로 버그가 있어야 합니다.

**커밋 메시지: Temperature 0.3**
```json
{
  "modelName": "models/gemini-3-pro-preview",
  "options": {
    "temperature": 0.3
  }
}
```
- 이유: 커밋 메시지는 **일관되고 예측 가능**해야 합니다.
- 매번 다른 스타일의 메시지가 나오면 히스토리를 읽기 어렵습니다.

### 직접 조절하고 싶다면

n8n 워크플로우에서 Temperature 값을 수정할 수 있습니다:

- 코드 리뷰가 너무 보수적이라면: 0.3~0.4로 올려보세요
- 커밋 메시지가 너무 딱딱하다면: 0.4~0.5로 올려보세요

**주의**: 1.0 이상은 절대 사용하지 마세요. 할루시네이션이 급격히 증가합니다.

---

## 7. 도메인 전문가 프로필

### 역할 부여의 효과

AI에게 "넌 Unity 전문가야" 또는 "넌 Unreal 전문가야"라고 역할을 부여하면 더 정확한 분석이 가능합니다.

이는 AI가 특정 도메인의 지식을 "활성화"하도록 유도하는 기법입니다.

### 지원하는 프로필

**1. Generic (범용)**
- 특별한 컨텍스트 없이 일반적인 코드 분석
- 어떤 프로젝트에도 적용 가능

**2. Unity 2021.3**
- MonoBehaviour 생명주기 (Awake, Start, Update 등)
- 가비지 컬렉션 최적화 (Object Pooling, 메모리 할당 최소화)
- DOTS/ECS 패턴
- C# 코딩 컨벤션

**3. Unreal Engine 5.7**
- UObject 시스템, 가비지 컬렉션, Reflection
- Blueprint/C++ 상호작용
- UPROPERTY, UFUNCTION 매크로
- Nanite, Lumen, Mass Entity

### 프로필 적용 방식

설정에서 선택한 프로필은 n8n 워크플로우의 시스템 메시지에 추가됩니다:

```
기본 시스템 메시지 + 전문가 프로필 컨텍스트
```

예를 들어, Unity 프로필이 선택되면:
- "MonoBehaviour의 Update()에서 매 프레임 new 키워드 사용은 GC 부하를 유발합니다"
- "GetComponent는 Awake에서 캐싱하세요"

같은 Unity 특화된 피드백을 제공할 수 있습니다.

---

## 8. JSON 규약: 확장 가능한 설계

P4V AI Assistant는 표준화된 JSON 형식으로 n8n 워크플로우와 통신합니다. 이 규약을 따르면 새로운 기능을 쉽게 추가할 수 있습니다.

### 요청 형식

```json
{
  "request_type": "description 또는 review",
  "changelist": {
    "number": 12345,
    "user": "사용자명",
    "client": "워크스페이스명",
    "current_description": "기존 설명"
  },
  "files": [
    {
      "depot_path": "//depot/project/src/file.cpp",
      "action": "edit",
      "revision": 5,
      "diff": "--- a/file.cpp\n+++ b/file.cpp\n@@ -10,3 +10,5 @@\n..."
    }
  ],
  "session_key": "cl_12345",
  "batch_info": {
    "current": 1,
    "total": 4
  },
  "expert_context": "전문가 프로필 추가 컨텍스트"
}
```

#### 필드 설명

| 필드 | 설명 |
|------|------|
| `request_type` | 요청 유형. "description"(커밋 메시지) 또는 "review"(코드 리뷰) |
| `changelist` | Perforce Changelist 정보 |
| `files` | 변경된 파일 목록과 diff |
| `session_key` | Redis Memory용 세션 키 (배치 간 컨텍스트 유지) |
| `batch_info` | 현재 배치 번호와 총 배치 수 |
| `expert_context` | 선택한 전문가 프로필의 추가 프롬프트 |

### 응답 형식 (커밋 메시지)

```json
{
  "success": true,
  "description": "[Feature] 플레이어 데미지 시스템 구현\n\n- Player.cpp: TakeDamage 함수 추가\n- GameManager.cpp: 데미지 이벤트 핸들링",
  "summary": "플레이어 데미지 시스템 구현"
}
```

### 응답 형식 (코드 리뷰)

```json
{
  "success": true,
  "summary": "전반적으로 양호하나 null 체크 누락이 있습니다",
  "overall_score": 72,
  "comments": [
    {
      "file_path": "//depot/project/src/Player.cpp",
      "line_number": 125,
      "severity": "warning",
      "category": "bug",
      "message": "health가 음수가 될 수 있습니다",
      "suggestion": "health = max(0, health - amount)로 수정하세요"
    },
    {
      "file_path": "//depot/project/src/GameManager.cpp",
      "line_number": 45,
      "severity": "info",
      "category": "style",
      "message": "매직 넘버 사용",
      "suggestion": "100을 MAX_HEALTH 상수로 정의하세요"
    }
  ],
  "statistics": {
    "critical": 0,
    "warning": 1,
    "info": 1,
    "suggestion": 0
  }
}
```

#### 심각도(severity) 기준

| 심각도 | 설명 | 점수 영향 |
|--------|------|----------|
| critical | 즉시 수정 필요 (크래시, 보안 취약점) | 0~29점 |
| warning | 수정 권장 (버그 가능성, 성능 이슈) | 30~49점 |
| info | 참고 사항 (컨벤션, 스타일) | 50~69점 |
| suggestion | 개선 제안 (더 나은 방법) | 70~100점 |

#### 카테고리(category) 종류

| 카테고리 | 설명 |
|----------|------|
| bug | 버그 또는 논리 오류 |
| security | 보안 취약점 |
| performance | 성능 이슈 |
| style | 코딩 스타일, 컨벤션 |
| maintainability | 가독성, 유지보수성 |

### 확장하려면

새로운 기능을 추가하고 싶다면:

1. **새로운 request_type 정의** (예: "security_scan", "test_generation")

2. **n8n 워크플로우 수정**
   - Switch 노드에 새 분기 추가
   - 새 기능용 프롬프트 작성
   - 응답 형식 정의

3. **Python 클라이언트 수정**
   - `n8n_client.py`에 새 요청 메서드 추가
   - 결과 처리 로직 구현

기존의 배치 처리와 Redis Memory 패턴을 그대로 재사용할 수 있습니다.

---

## 9. 마치며

### 핵심 요약

1. **AI에게 한 번에 너무 많은 코드를 보여주면 품질이 떨어집니다**
   - Context Rot 현상으로 앞부분 내용을 잊어버림
   - 할루시네이션(없는 내용 지어내기) 증가

2. **배치로 나누고, Redis Memory로 기억을 이어줍니다**
   - 50파일 또는 5,000줄마다 배치 분할
   - 세션 키로 배치 간 대화 컨텍스트 유지
   - 15분 TTL로 메모리 자동 정리

3. **Temperature를 낮게 설정해서 정확한 분석을 유도합니다**
   - 코드 리뷰: 0.2 (신중하고 정확하게)
   - 커밋 메시지: 0.3 (일관되게)

4. **표준화된 JSON 규약으로 확장이 용이합니다**
   - 새로운 request_type으로 기능 추가 가능
   - 동일한 배치/컨텍스트 패턴 재사용

### 시스템 아키텍처

```
P4V (사용자)
    |
    v
p4v_ai_assistant.exe (Python CLI)
    |
    v [HTTP POST + JSON]
n8n 워크플로우
    |
    +-- Switch (request_type 분기)
    |
    +-- Redis Chat Memory (컨텍스트 유지)
    |
    v
Google Gemini AI (LLM)
    |
    v [JSON 응답]
p4v_ai_assistant.exe
    |
    v
GUI / HTML 리포트
```

---

## 10. 참고 자료

이 문서를 작성하면서 참고한 연구 및 자료:

- [Context Rot: How Increasing Input Tokens Impacts LLM Performance](https://research.trychroma.com/context-rot) - Chroma Research
- [LLM Hallucinations in 2025](https://www.lakera.ai/blog/guide-to-hallucinations-in-large-language-models) - Lakera
- [What is LLM Temperature?](https://www.ibm.com/think/topics/llm-temperature) - IBM
- [Google Gemini Token Limits](https://ai.google.dev/gemini-api/docs/models) - Google AI for Developers
- [How to Choose the Right LLM Temperature Setting](https://www.promptfoo.dev/docs/guides/evaluate-llm-temperature/) - Promptfoo

---

*이 문서는 P4V AI Assistant v0.4.2 기준으로 작성되었습니다.*
