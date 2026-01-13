"""
P4V Custom Tools 설치/제거 모듈
customtools.xml에 AI Description 생성 도구 등록
"""
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, Tuple

# 도구 정의
TOOL_NAME = "AI Description 생성"
TOOL_ARGUMENTS = "description --changelist %p"


def get_customtools_path() -> Path:
    """customtools.xml 경로 반환"""
    user_profile = os.environ.get("USERPROFILE", "")
    if not user_profile:
        raise InstallError("USERPROFILE 환경변수를 찾을 수 없습니다.")
    return Path(user_profile) / ".p4qt" / "customtools.xml"


def get_exe_path(explicit_path: Optional[str] = None) -> str:
    """
    실행 파일 경로 반환

    Args:
        explicit_path: 명시적으로 지정된 경로 (NSIS에서 사용)

    Returns:
        실행 파일의 절대 경로
    """
    if explicit_path:
        return os.path.abspath(explicit_path)

    # PyInstaller로 빌드된 exe인 경우
    if getattr(sys, 'frozen', False):
        return sys.executable

    # Python 스크립트로 실행 중인 경우
    # python.exe -m src.main 형태로 실행해야 함
    return sys.executable


def get_project_root() -> str:
    """프로젝트 루트 디렉토리 반환"""
    if getattr(sys, 'frozen', False):
        # PyInstaller exe인 경우 - exe가 있는 디렉토리
        return os.path.dirname(sys.executable)
    else:
        # Python 스크립트인 경우 - src의 상위 디렉토리
        current_file = os.path.abspath(__file__)
        # __file__ = .../src/commands/install.py
        # project root = .../
        return os.path.dirname(os.path.dirname(os.path.dirname(current_file)))


def get_command_and_args(exe_path: str) -> Tuple[str, str, str]:
    """
    실행 명령, 인자, 작업 디렉토리 반환

    PyInstaller exe: (exe_path, "description --changelist %p", "")
    Python script: (python.exe, "-m src.main description --changelist %p", project_root)
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller로 빌드된 exe인 경우
        return exe_path, TOOL_ARGUMENTS, ""
    else:
        # Python 스크립트로 실행 중인 경우
        project_root = get_project_root()
        return exe_path, f"-m src.main {TOOL_ARGUMENTS}", project_root


def create_new_customtools_xml(exe_path: str) -> ET.Element:
    """새 customtools.xml 루트 요소 생성"""
    root = ET.Element("CustomToolDefList")
    root.set("varName", "customtooldeflist")
    add_tool_to_root(root, exe_path)
    return root


def add_tool_to_root(root: ET.Element, exe_path: str) -> None:
    """루트 요소에 도구 추가"""
    command, arguments, init_dir = get_command_and_args(exe_path)

    tool_def = ET.SubElement(root, "CustomToolDef")

    definition = ET.SubElement(tool_def, "Definition")
    ET.SubElement(definition, "Name").text = TOOL_NAME
    ET.SubElement(definition, "Command").text = command
    ET.SubElement(definition, "Arguments").text = arguments
    ET.SubElement(definition, "InitDir").text = init_dir
    ET.SubElement(definition, "Shortcut")

    # Console 요소 제거: 터미널 창 없이 실행
    # (Run tool in terminal window 옵션 비활성화)

    ET.SubElement(tool_def, "AddToContext").text = "true"


def find_tool_element(root: ET.Element) -> Optional[ET.Element]:
    """기존 도구 요소 찾기"""
    for tool_def in root.findall("CustomToolDef"):
        definition = tool_def.find("Definition")
        if definition is not None:
            name_elem = definition.find("Name")
            if name_elem is not None and name_elem.text == TOOL_NAME:
                return tool_def
    return None


def install_tool(exe_path: Optional[str] = None) -> dict:
    """
    P4V Custom Tools에 도구 설치

    Args:
        exe_path: 실행 파일 경로 (없으면 자동 감지)

    Returns:
        dict: {"success": bool, "message": str, "path": str}
    """
    result = {
        "success": False,
        "message": "",
        "path": ""
    }

    try:
        customtools_path = get_customtools_path()
        result["path"] = str(customtools_path)

        resolved_exe_path = get_exe_path(exe_path)

        # .p4qt 디렉토리 생성
        customtools_path.parent.mkdir(parents=True, exist_ok=True)

        if customtools_path.exists():
            # 기존 파일 파싱
            try:
                tree = ET.parse(customtools_path)
                root = tree.getroot()
            except ET.ParseError as e:
                result["message"] = f"기존 customtools.xml 파싱 실패: {e}"
                return result

            # 이미 설치되어 있는지 확인
            existing_tool = find_tool_element(root)
            if existing_tool is not None:
                # 기존 도구 업데이트
                root.remove(existing_tool)
                add_tool_to_root(root, resolved_exe_path)
                result["message"] = f"'{TOOL_NAME}' 도구가 업데이트되었습니다."
            else:
                # 새 도구 추가
                add_tool_to_root(root, resolved_exe_path)
                result["message"] = f"'{TOOL_NAME}' 도구가 추가되었습니다."
        else:
            # 새 파일 생성
            root = create_new_customtools_xml(resolved_exe_path)
            result["message"] = f"customtools.xml이 생성되고 '{TOOL_NAME}' 도구가 추가되었습니다."

        # XML 저장
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")

        with open(customtools_path, "wb") as f:
            f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write(b'<!--perforce-xml-version=1.0-->\n')
            tree.write(f, encoding="UTF-8", xml_declaration=False)

        result["success"] = True
        result["message"] += f"\n\n파일 위치: {customtools_path}\n실행 파일: {resolved_exe_path}\n\nP4V를 재시작하면 컨텍스트 메뉴에서 사용할 수 있습니다."

    except InstallError as e:
        result["message"] = str(e)
    except Exception as e:
        result["message"] = f"설치 중 오류 발생: {e}"

    return result


def uninstall_tool() -> dict:
    """
    P4V Custom Tools에서 도구 제거

    Returns:
        dict: {"success": bool, "message": str}
    """
    result = {
        "success": False,
        "message": ""
    }

    try:
        customtools_path = get_customtools_path()

        if not customtools_path.exists():
            result["message"] = "customtools.xml 파일이 존재하지 않습니다."
            return result

        try:
            tree = ET.parse(customtools_path)
            root = tree.getroot()
        except ET.ParseError as e:
            result["message"] = f"customtools.xml 파싱 실패: {e}"
            return result

        existing_tool = find_tool_element(root)
        if existing_tool is None:
            result["message"] = f"'{TOOL_NAME}' 도구가 설치되어 있지 않습니다."
            result["success"] = True
            return result

        root.remove(existing_tool)

        # XML 저장
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")

        with open(customtools_path, "wb") as f:
            f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write(b'<!--perforce-xml-version=1.0-->\n')
            tree.write(f, encoding="UTF-8", xml_declaration=False)

        result["success"] = True
        result["message"] = f"'{TOOL_NAME}' 도구가 제거되었습니다.\n\nP4V를 재시작하면 변경사항이 적용됩니다."

    except Exception as e:
        result["message"] = f"제거 중 오류 발생: {e}"

    return result


class InstallError(Exception):
    """설치 관련 에러"""
    pass
