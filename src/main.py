"""
P4V AI Assistant - CLI 엔트리포인트
P4V의 Custom Tools에서 호출되는 메인 스크립트
"""
import argparse
import sys

import threading

from . import __version__
from .config_manager import get_config
from .commands.description import run_description_command
from .commands.review import run_review_command, ReviewResult
from .commands.install import install_tool, uninstall_tool
from .p4_client import P4Client
from .ui.dialogs import (
    DescriptionDialog,
    ReviewDialog,
    SettingsDialog,
    show_error,
    show_info
)


def cmd_description(args):
    """AI Description 생성 명령"""
    config = get_config()

    # 설정 확인
    webhook_url = args.webhook_url or config.webhook_url
    if not webhook_url:
        show_error(
            "설정 오류",
            "Webhook URL이 설정되지 않았습니다.\n"
            "설정을 먼저 진행해주세요.\n\n"
            "명령어: p4v_ai_tool.exe settings"
        )
        return 1

    port = args.port or ""
    user = args.user or ""
    client = args.client or ""

    # 적용 콜백 함수
    def apply_callback(changelist: int, description: str):
        p4 = P4Client(port=port, user=user, client=client)
        p4.update_changelist_description(changelist, description)

    # 통합 다이얼로그 생성
    dialog = DescriptionDialog(
        title="AI Description 생성",
        changelist=args.changelist,
        on_apply_callback=apply_callback
    )

    # 백그라운드 작업
    def task():
        try:
            result = run_description_command(
                changelist=args.changelist,
                port=port,
                user=user,
                client=client,
                webhook_url=webhook_url,
                auto_apply=False,  # 사용자가 버튼으로 결정
                progress_callback=dialog.update_status
            )

            dialog.show_result(
                success=result["success"],
                description=result.get("description", ""),
                summary=result.get("summary", ""),
                error=result.get("error", "")
            )
        except Exception as e:
            dialog.show_result(
                success=False,
                error=str(e)
            )

    # 스레드에서 작업 실행
    thread = threading.Thread(target=task, daemon=True)
    thread.start()

    # 다이얼로그 실행
    dialog.run()
    return 0


def cmd_review(args):
    """AI 코드 리뷰 명령"""
    config = get_config()

    # 설정 확인
    webhook_url = args.webhook_url or config.webhook_url
    if not webhook_url:
        show_error(
            "설정 오류",
            "Webhook URL이 설정되지 않았습니다.\n"
            "설정을 먼저 진행해주세요.\n\n"
            "명령어: p4v_ai_tool.exe settings"
        )
        return 1

    port = args.port or ""
    user = args.user or ""
    client = args.client or ""

    # 리뷰 다이얼로그 생성
    dialog = ReviewDialog(
        title="AI 코드 리뷰",
        changelist=args.changelist
    )

    # 백그라운드 작업
    def task():
        try:
            result = run_review_command(
                changelist=args.changelist,
                port=port,
                user=user,
                client=client,
                webhook_url=webhook_url,
                progress_callback=dialog.update_status
            )
            dialog.show_result(result)
        except Exception as e:
            error_result = ReviewResult(success=False, error=str(e))
            dialog.show_result(error_result)

    # 스레드에서 작업 실행
    thread = threading.Thread(target=task, daemon=True)
    thread.start()

    # 다이얼로그 실행
    dialog.run()
    return 0


def cmd_settings(args):
    """설정 GUI 열기"""
    config = get_config()
    SettingsDialog(config).run()
    return 0


def cmd_test(args):
    """테스트 명령 (개발용)"""
    config = get_config()
    print(f"Config file: {config.config_file}")
    print(f"Webhook URL: {config.webhook_url}")
    print(f"Timeout: {config.timeout}")
    print(f"Is configured: {config.is_configured()}")
    return 0


def cmd_install(args):
    """P4V Custom Tools에 도구 설치"""
    result = install_tool(exe_path=args.exe_path)

    if result["success"]:
        show_info("설치 완료", result["message"])
        return 0
    else:
        show_error("설치 실패", result["message"])
        return 1


def cmd_uninstall(args):
    """P4V Custom Tools에서 도구 제거"""
    result = uninstall_tool()

    if result["success"]:
        show_info("제거 완료", result["message"])
        return 0
    else:
        show_error("제거 실패", result["message"])
        return 1


def main():
    parser = argparse.ArgumentParser(
        prog="p4v_ai_assistant",
        description="P4V AI Assistant - AI 기반 Description 생성 및 코드 리뷰"
    )
    parser.add_argument(
        "--version", "-V",
        action="version",
        version=f"P4V AI Assistant v{__version__}"
    )
    subparsers = parser.add_subparsers(dest="command", help="사용 가능한 명령")

    # description 명령
    desc_parser = subparsers.add_parser(
        "description",
        help="AI Description 생성",
        aliases=["desc"]
    )
    desc_parser.add_argument(
        "--changelist", "-c",
        type=int,
        required=True,
        help="Changelist 번호"
    )
    desc_parser.add_argument(
        "--port", "-p",
        help="Perforce 서버 주소 (예: ssl:perforce:1666)"
    )
    desc_parser.add_argument(
        "--user", "-u",
        help="Perforce 사용자명"
    )
    desc_parser.add_argument(
        "--client",
        help="Perforce 클라이언트(workspace) 이름"
    )
    desc_parser.add_argument(
        "--webhook-url",
        help="n8n Webhook URL (설정 파일 대신 사용)"
    )
    desc_parser.add_argument(
        "--no-apply",
        action="store_true",
        help="생성된 description을 자동으로 적용하지 않음"
    )
    desc_parser.set_defaults(func=cmd_description)

    # review 명령
    review_parser = subparsers.add_parser(
        "review",
        help="AI 코드 리뷰",
        aliases=["r"]
    )
    review_parser.add_argument(
        "--changelist", "-c",
        type=int,
        required=True,
        help="Changelist 번호"
    )
    review_parser.add_argument(
        "--port", "-p",
        help="Perforce 서버 주소 (예: ssl:perforce:1666)"
    )
    review_parser.add_argument(
        "--user", "-u",
        help="Perforce 사용자명"
    )
    review_parser.add_argument(
        "--client",
        help="Perforce 클라이언트(workspace) 이름"
    )
    review_parser.add_argument(
        "--webhook-url",
        help="n8n Webhook URL (설정 파일 대신 사용)"
    )
    review_parser.set_defaults(func=cmd_review)

    # settings 명령
    settings_parser = subparsers.add_parser(
        "settings",
        help="설정 GUI 열기"
    )
    settings_parser.set_defaults(func=cmd_settings)

    # test 명령 (개발용)
    test_parser = subparsers.add_parser(
        "test",
        help="테스트 명령 (개발용)"
    )
    test_parser.set_defaults(func=cmd_test)

    # install 명령
    install_parser = subparsers.add_parser(
        "install",
        help="P4V Custom Tools에 도구 설치"
    )
    install_parser.add_argument(
        "--exe-path",
        help="실행 파일 경로 (기본값: 자동 감지)"
    )
    install_parser.set_defaults(func=cmd_install)

    # uninstall 명령
    uninstall_parser = subparsers.add_parser(
        "uninstall",
        help="P4V Custom Tools에서 도구 제거"
    )
    uninstall_parser.set_defaults(func=cmd_uninstall)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
