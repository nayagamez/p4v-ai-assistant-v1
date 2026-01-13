"""
기본 전문가 프로필 정의
팀별 전문가 컨텍스트를 AI 시스템 메시지에 추가
"""

EXPERT_PROFILES = {
    "generic": {
        "name": "범용 전문가",
        "description_prompt": "",  # 기본 시스템 메시지만 사용
        "review_prompt": ""
    },
    "unity": {
        "name": "Unity 2021.3 전문가",
        "description_prompt": """
## 추가 전문가 컨텍스트
당신은 또한 Unity 2021.3 및 C# 전문가입니다:
- Unity DOTS, ECS 패턴에 익숙합니다
- MonoBehaviour 생명주기를 정확히 이해합니다
- C# 코딩 컨벤션 (Microsoft 스타일)을 따릅니다
- Unity 특화 최적화 (Object pooling, GC 최소화 등)를 고려합니다""",
        "review_prompt": """
## 추가 전문가 컨텍스트
당신은 또한 Unity 2021.3 및 C# 전문가입니다:
- Unity 특유의 버그 패턴 (Coroutine 누수, Null Reference 등)을 잘 압니다
- MonoBehaviour 생명주기 관련 이슈를 식별합니다
- C# 성능 안티패턴 (Boxing, string 연결 등)을 감지합니다
- Unity API 사용법을 정확히 알고 있습니다
- SerializeField, GetComponent 등의 올바른 사용을 검증합니다"""
    },
    "unreal": {
        "name": "Unreal 5.7 전문가",
        "description_prompt": """
## 추가 전문가 컨텍스트
당신은 또한 Unreal Engine 5.7 및 C++ 전문가입니다:
- UObject 시스템, GC, Reflection을 이해합니다
- Blueprint/C++ 상호작용에 익숙합니다
- Unreal C++ 코딩 컨벤션 (Epic 스타일)을 따릅니다
- UE5 특화 기능 (Nanite, Lumen, Mass Entity 등)을 알고 있습니다""",
        "review_prompt": """
## 추가 전문가 컨텍스트
당신은 또한 Unreal Engine 5.7 및 C++ 전문가입니다:
- UE 메모리 관리 (UPROPERTY, TSharedPtr, TWeakObjectPtr 등)를 검증합니다
- 일반적인 UE 버그 패턴 (GC 타이밍, Replicated 변수 동기화 등)을 식별합니다
- C++ 성능 안티패턴 (불필요한 복사, 가상 함수 오버헤드 등)을 감지합니다
- Unreal API 사용법과 베스트 프랙티스를 알고 있습니다
- UFUNCTION, UPROPERTY 매크로의 올바른 사용을 검증합니다"""
    }
}

DEFAULT_PROFILE = "generic"


def get_profile_names() -> dict:
    """프로필 키와 표시 이름 매핑 반환"""
    return {key: profile["name"] for key, profile in EXPERT_PROFILES.items()}


def get_prompt(profile_key: str, prompt_type: str) -> str:
    """특정 프로필의 프롬프트 반환

    Args:
        profile_key: 프로필 키 (generic, unity, unreal)
        prompt_type: 프롬프트 타입 (description, review)

    Returns:
        프롬프트 문자열 (없으면 빈 문자열)
    """
    profile = EXPERT_PROFILES.get(profile_key, EXPERT_PROFILES[DEFAULT_PROFILE])
    return profile.get(f"{prompt_type}_prompt", "")
