"""
설정 파일 관리 모듈
%APPDATA%/P4V-AI-Assistant/config.json에 설정 저장
"""
import json
import os
from pathlib import Path
from typing import Optional


class ConfigManager:
    DEFAULT_CONFIG = {
        "webhook_url": "",
        "timeout": 60,
        "language": "ko",
        "expert_profile": "generic",
        "custom_prompts": {
            "description": "",
            "review": ""
        }
    }

    def __init__(self):
        self.config_dir = Path(os.environ.get("APPDATA", "")) / "P4V-AI-Assistant"
        self.config_file = self.config_dir / "config.json"
        self._config: dict = {}
        self._load()

    def _load(self) -> None:
        """설정 파일 로드"""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    self._config = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._config = self.DEFAULT_CONFIG.copy()
        else:
            self._config = self.DEFAULT_CONFIG.copy()

    def save(self) -> None:
        """설정 파일 저장"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self._config, f, indent=2, ensure_ascii=False)

    @property
    def webhook_url(self) -> str:
        return self._config.get("webhook_url", "")

    @webhook_url.setter
    def webhook_url(self, value: str) -> None:
        self._config["webhook_url"] = value

    @property
    def timeout(self) -> int:
        return self._config.get("timeout", 60)

    @timeout.setter
    def timeout(self, value: int) -> None:
        self._config["timeout"] = value

    @property
    def expert_profile(self) -> str:
        return self._config.get("expert_profile", "generic")

    @expert_profile.setter
    def expert_profile(self, value: str) -> None:
        self._config["expert_profile"] = value

    @property
    def custom_prompts(self) -> dict:
        return self._config.get("custom_prompts", {"description": "", "review": ""})

    @custom_prompts.setter
    def custom_prompts(self, value: dict) -> None:
        self._config["custom_prompts"] = value

    def get(self, key: str, default=None):
        return self._config.get(key, default)

    def set(self, key: str, value) -> None:
        self._config[key] = value

    def is_configured(self) -> bool:
        """필수 설정이 되어 있는지 확인"""
        return bool(self.webhook_url)


# 싱글톤 인스턴스
_config_instance: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """ConfigManager 싱글톤 인스턴스 반환"""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
    return _config_instance
