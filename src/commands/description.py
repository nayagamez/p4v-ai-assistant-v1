"""
AI Description 생성 명령
Changelist의 diff를 분석하여 커밋 메시지 자동 생성
"""
import re
from typing import Callable, Optional

from ..p4_client import P4Client, P4Error
from ..n8n_client import N8NClient, N8NError


# 접두사 패턴: 대괄호로 감싸진 텍스트가 연속으로 나오는 부분
# 예: [1UD][클라/홍길동] 또는 [클라/홍길동]
PREFIX_PATTERN = r'^(\[[^\]]+\])+\s*'


def extract_prefix(description: str) -> str:
    """
    기존 description에서 접두사 추출

    Args:
        description: 현재 changelist description

    Returns:
        접두사 문자열 (없으면 빈 문자열)

    Examples:
        "[1UD][클라/홍길동] 작업 중" -> "[1UD][클라/홍길동]"
        "[클라/홍길동] 버그 수정" -> "[클라/홍길동]"
        "작업 중..." -> ""
    """
    if not description:
        return ""
    match = re.match(PREFIX_PATTERN, description)
    return match.group(0).rstrip() if match else ""


class DescriptionGenerator:
    def __init__(
        self,
        port: str = "",
        user: str = "",
        client: str = "",
        webhook_url: str = ""
    ):
        self.p4 = P4Client(port=port, user=user, client=client)
        self.n8n = N8NClient(webhook_url=webhook_url) if webhook_url else N8NClient()

    def generate(
        self,
        changelist: int,
        progress_callback: Optional[Callable[[str], None]] = None,
        auto_apply: bool = True
    ) -> dict:
        """
        AI Description 생성

        Args:
            changelist: Changelist 번호
            progress_callback: 진행 상황 콜백 함수
            auto_apply: True면 생성된 description을 자동으로 적용

        Returns:
            dict: {
                "success": bool,
                "description": str,  # 생성된 description
                "summary": str,      # 요약
                "applied": bool,     # 적용 여부
                "error": str         # 에러 메시지 (실패 시)
            }
        """
        result = {
            "success": False,
            "description": "",
            "summary": "",
            "applied": False,
            "error": ""
        }

        try:
            # Step 1: Changelist 정보 수집
            if progress_callback:
                progress_callback("Changelist 정보 수집 중...")

            changelist_info = self.p4.get_changelist_with_diff(changelist)

            if not changelist_info.files:
                result["error"] = "변경된 파일이 없습니다."
                return result

            # Step 2: n8n으로 AI 요청
            if progress_callback:
                progress_callback("AI Description 생성 중...")

            response = self.n8n.request_description(changelist_info)

            ai_description = response.get("description", "")
            summary = response.get("summary", "")

            if not ai_description:
                result["error"] = "AI가 description을 생성하지 못했습니다."
                return result

            # 기존 description에서 접두사 추출 후 적용
            prefix = extract_prefix(changelist_info.description)
            if prefix:
                description = f"{prefix}{ai_description}"
            else:
                description = ai_description

            result["description"] = description
            result["summary"] = summary

            # Step 3: Description 적용 (선택적)
            if auto_apply:
                if progress_callback:
                    progress_callback("Description 적용 중...")

                self.p4.update_changelist_description(changelist, description)
                result["applied"] = True

            result["success"] = True

        except P4Error as e:
            result["error"] = f"Perforce 오류: {str(e)}"
        except N8NError as e:
            result["error"] = f"AI 서비스 오류: {str(e)}"
        except Exception as e:
            result["error"] = f"예상치 못한 오류: {str(e)}"

        return result


def run_description_command(
    changelist: int,
    port: str = "",
    user: str = "",
    client: str = "",
    webhook_url: str = "",
    auto_apply: bool = True,
    progress_callback: Optional[Callable[[str], None]] = None
) -> dict:
    """Description 생성 명령 실행 헬퍼 함수"""
    generator = DescriptionGenerator(
        port=port,
        user=user,
        client=client,
        webhook_url=webhook_url
    )
    return generator.generate(
        changelist=changelist,
        progress_callback=progress_callback,
        auto_apply=auto_apply
    )
