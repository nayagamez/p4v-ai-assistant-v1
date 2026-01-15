"""
n8n Webhook HTTP 클라이언트
AI Description 생성 및 코드 리뷰 요청
"""
import requests
from typing import Dict, Any, Optional
from dataclasses import asdict

from .p4_client import ChangelistInfo
from .config_manager import get_config


class N8NClient:
    def __init__(self, webhook_url: Optional[str] = None, timeout: Optional[int] = None):
        config = get_config()
        self.webhook_url = webhook_url or config.webhook_url
        self.timeout = timeout if timeout is not None else config.timeout

    def _prepare_payload(
        self,
        changelist_info: ChangelistInfo,
        request_type: str,
        batch_info: Optional[Dict[str, int]] = None
    ) -> Dict[str, Any]:
        """API 요청 페이로드 생성"""
        files_data = []
        for f in changelist_info.files:
            files_data.append({
                "depot_path": f.depot_path,
                "action": f.action,
                "file_type": f.file_type,
                "revision": f.revision,
                "diff": f.diff,
                "content": ""
            })

        # 전문가 컨텍스트 가져오기
        expert_context = self._get_expert_context(request_type)

        return {
            "request_type": request_type,
            "changelist": {
                "number": changelist_info.number,
                "user": changelist_info.user,
                "client": changelist_info.client,
                "current_description": changelist_info.description
            },
            "files": files_data,
            # 배치 컨텍스트 유지를 위한 세션 정보
            "session_key": f"cl_{changelist_info.number}",
            "batch_info": batch_info or {"current": 1, "total": 1},
            # 전문가 프로필 컨텍스트
            "expert_context": expert_context
        }

    def _get_expert_context(self, request_type: str) -> str:
        """설정된 전문가 프로필의 컨텍스트 반환

        Args:
            request_type: 요청 타입 (description, review)

        Returns:
            전문가 컨텍스트 문자열 (없으면 빈 문자열)
        """
        from .expert_profiles import EXPERT_PROFILES
        config = get_config()

        # 커스텀 프롬프트가 있으면 우선 사용
        custom = config.custom_prompts.get(request_type, "")
        if custom:
            return custom

        # 프로필 기본 프롬프트 사용
        profile = EXPERT_PROFILES.get(config.expert_profile, EXPERT_PROFILES["generic"])
        return profile.get(f"{request_type}_prompt", "")

    def request_description(self, changelist_info: ChangelistInfo) -> Dict[str, Any]:
        """AI Description 생성 요청"""
        payload = self._prepare_payload(changelist_info, "description")
        return self._send_request(payload)

    def request_review(
        self,
        changelist_info: ChangelistInfo,
        batch_info: Optional[Dict[str, int]] = None
    ) -> Dict[str, Any]:
        """AI 코드 리뷰 요청"""
        payload = self._prepare_payload(changelist_info, "review", batch_info)
        return self._send_request(payload)

    def _send_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """HTTP POST 요청 전송"""
        if not self.webhook_url:
            raise N8NError("Webhook URL이 설정되지 않았습니다.")

        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()

            result = response.json()

            # 응답 형식 검증
            if not isinstance(result, dict):
                raise N8NError("잘못된 응답 형식입니다.")

            if not result.get("success", False):
                error_msg = result.get("error", "알 수 없는 오류가 발생했습니다.")
                raise N8NError(error_msg)

            return result

        except requests.exceptions.Timeout:
            raise N8NError(f"요청 시간 초과 ({self.timeout}초)")
        except requests.exceptions.ConnectionError:
            raise N8NError("서버에 연결할 수 없습니다.")
        except requests.exceptions.HTTPError as e:
            raise N8NError(f"HTTP 오류: {e.response.status_code}")
        except requests.exceptions.JSONDecodeError:
            raise N8NError("응답을 JSON으로 파싱할 수 없습니다.")
        except Exception as e:
            if isinstance(e, N8NError):
                raise
            raise N8NError(f"요청 실패: {str(e)}")


class N8NError(Exception):
    """n8n 관련 에러"""
    pass
