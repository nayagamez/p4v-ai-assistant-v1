"""
PyInstaller 빌드 스크립트
P4V AI Assistant를 단일 exe 파일로 패키징
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path


def get_project_root() -> Path:
    """프로젝트 루트 디렉토리 반환"""
    return Path(__file__).parent.parent


def clean_build_artifacts():
    """이전 빌드 산출물 정리"""
    project_root = get_project_root()

    dirs_to_clean = [
        project_root / "build" / "pyinstaller",
        project_root / "dist",
    ]

    for dir_path in dirs_to_clean:
        if dir_path.exists():
            print(f"정리 중: {dir_path}")
            shutil.rmtree(dir_path)


def run_pyinstaller():
    """PyInstaller 실행"""
    project_root = get_project_root()
    spec_file = project_root / "build" / "p4v_ai_assistant.spec"

    if not spec_file.exists():
        print(f"오류: spec 파일이 없습니다: {spec_file}")
        sys.exit(1)

    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        str(spec_file)
    ]

    print(f"빌드 명령: {' '.join(cmd)}")
    print("-" * 50)

    result = subprocess.run(cmd, cwd=project_root)

    if result.returncode != 0:
        print("빌드 실패!")
        sys.exit(1)

    print("-" * 50)
    print("빌드 성공!")

    # 결과 파일 확인
    exe_path = project_root / "dist" / "p4v_ai_assistant.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"출력 파일: {exe_path}")
        print(f"파일 크기: {size_mb:.2f} MB")
    else:
        print("경고: exe 파일을 찾을 수 없습니다.")


def main():
    """메인 함수"""
    print("=" * 50)
    print("P4V AI Assistant 빌드")
    print("=" * 50)

    # PyInstaller 설치 확인
    try:
        import PyInstaller
        print(f"PyInstaller 버전: {PyInstaller.__version__}")
    except ImportError:
        print("PyInstaller가 설치되어 있지 않습니다.")
        print("설치: pip install pyinstaller")
        sys.exit(1)

    # 빌드 실행
    clean_build_artifacts()
    run_pyinstaller()

    print("=" * 50)
    print("완료!")
    print("=" * 50)


if __name__ == "__main__":
    main()
