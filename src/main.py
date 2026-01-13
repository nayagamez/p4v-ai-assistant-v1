"""
P4V AI Assistant - CLI 엔트리포인트
P4V의 Custom Tools에서 호출되는 메인 스크립트
"""
import argparse
import sys

from .config_manager import get_config
from .commands.description import run_description_command
from .commands.install import install_tool, uninstall_tool
from .ui.dialogs import (
    run_with_progress,
    ResultDialog,
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

    def task(progress_callback):
        return run_description_command(
            changelist=args.changelist,
            port=args.port or "",
            user=args.user or "",
            client=args.client or "",
            webhook_url=webhook_url,
            auto_apply=not args.no_apply,
            progress_callback=progress_callback
        )

    try:
        result = run_with_progress(
            task,
            title="AI Description 생성",
            message=f"Changelist #{args.changelist} 분석 중..."
        )

        if result["success"]:
            detail = f"생성된 Description:\n\n{result['description']}"
            if result.get("summary"):
                detail += f"\n\n요약: {result['summary']}"

            applied_text = "적용됨" if result.get("applied") else "적용 안됨"

            ResultDialog(
                title="AI Description 생성 완료",
                success=True,
                message=f"Description이 성공적으로 생성되었습니다. ({applied_text})",
                detail=detail
            ).run()
            return 0
        else:
            ResultDialog(
                title="AI Description 생성 실패",
                success=False,
                message="Description 생성에 실패했습니다.",
                detail=result.get("error", "알 수 없는 오류")
            ).run()
            return 1

    except Exception as e:
        show_error("오류", f"예상치 못한 오류가 발생했습니다.\n\n{str(e)}")
        return 1


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
        prog="p4v_ai_tool",
        description="P4V AI Assistant - AI 기반 Description 생성 및 코드 리뷰"
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
