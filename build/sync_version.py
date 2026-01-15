"""
버전 동기화 스크립트
src/__init__.py의 __version__을 읽어서 installer/installer.nsi에 반영
"""
import re
import sys
from pathlib import Path


def get_version_from_init() -> str:
    """src/__init__.py에서 버전 읽기"""
    init_path = Path(__file__).parent.parent / "src" / "__init__.py"

    if not init_path.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {init_path}")

    content = init_path.read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)

    if not match:
        raise ValueError("src/__init__.py에서 __version__을 찾을 수 없습니다")

    return match.group(1)


def update_nsi_version(version: str) -> bool:
    """installer/installer.nsi의 VERSION 업데이트"""
    nsi_path = Path(__file__).parent.parent / "installer" / "installer.nsi"

    if not nsi_path.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {nsi_path}")

    content = nsi_path.read_text(encoding="utf-8")

    # !define VERSION "x.x.x" 패턴 찾아서 교체
    new_content, count = re.subn(
        r'(!define VERSION ")[^"]+(")',
        rf'\g<1>{version}\g<2>',
        content
    )

    if count == 0:
        raise ValueError("installer.nsi에서 VERSION 정의를 찾을 수 없습니다")

    nsi_path.write_text(new_content, encoding="utf-8")
    return True


def main():
    """메인 함수"""
    try:
        version = get_version_from_init()
        print(f"[sync_version] 버전 확인: {version}")

        update_nsi_version(version)
        print(f"[sync_version] installer.nsi 업데이트 완료")

        return 0
    except Exception as e:
        print(f"[sync_version] 오류: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
