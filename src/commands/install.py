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
TOOLS = [
    {
        "name": "AI Description 생성",
        "arguments": "description --changelist %c",
        "context_menu": True,  # Changelist 컨텍스트 메뉴에 추가 (%c: 모든 CL 뷰에서 동작)
    },
    {
        "name": "AI 코드 리뷰",
        "arguments": "review --changelist %c",
        "context_menu": True,  # Changelist 컨텍스트 메뉴에 추가 (%c: 모든 CL 뷰에서 동작)
    },
    {
        "name": "AI Assistant 설정",
        "arguments": "settings",
        "context_menu": False,  # Tools 메뉴에만 추가
    },
]


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


def get_command_and_args(exe_path: str, tool_arguments: str) -> Tuple[str, str, str]:
    """
    실행 명령, 인자, 작업 디렉토리 반환

    PyInstaller exe: (exe_path, "description --changelist %c", "")
    Python script: (python.exe, "-m src.main description --changelist %c", project_root)
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller로 빌드된 exe인 경우
        return exe_path, tool_arguments, ""
    else:
        # Python 스크립트로 실행 중인 경우
        project_root = get_project_root()
        return exe_path, f"-m src.main {tool_arguments}", project_root


def create_new_customtools_xml(exe_path: str) -> ET.Element:
    """새 customtools.xml 루트 요소 생성"""
    root = ET.Element("CustomToolDefList")
    root.set("varName", "customtooldeflist")
    add_all_tools_to_root(root, exe_path)
    return root


def add_tool_to_root(root: ET.Element, exe_path: str, tool: dict) -> None:
    """루트 요소에 단일 도구 추가"""
    command, arguments, init_dir = get_command_and_args(exe_path, tool["arguments"])

    tool_def = ET.SubElement(root, "CustomToolDef")

    definition = ET.SubElement(tool_def, "Definition")
    ET.SubElement(definition, "Name").text = tool["name"]
    ET.SubElement(definition, "Command").text = command
    ET.SubElement(definition, "Arguments").text = arguments
    ET.SubElement(definition, "InitDir").text = init_dir
    ET.SubElement(definition, "Shortcut")

    # Console 요소 제거: 터미널 창 없이 실행
    # (Run tool in terminal window 옵션 비활성화)

    if tool.get("context_menu", False):
        ET.SubElement(tool_def, "AddToContext").text = "true"


def add_all_tools_to_root(root: ET.Element, exe_path: str) -> None:
    """루트 요소에 모든 도구 추가"""
    for tool in TOOLS:
        add_tool_to_root(root, exe_path, tool)


def find_tool_element(root: ET.Element, tool_name: str) -> Optional[ET.Element]:
    """기존 도구 요소 찾기"""
    for tool_def in root.findall("CustomToolDef"):
        definition = tool_def.find("Definition")
        if definition is not None:
            name_elem = definition.find("Name")
            if name_elem is not None and name_elem.text == tool_name:
                return tool_def
    return None


def find_all_tool_elements(root: ET.Element) -> list:
    """모든 AI Assistant 도구 요소 찾기"""
    tool_names = [tool["name"] for tool in TOOLS]
    found = []
    for tool_def in root.findall("CustomToolDef"):
        definition = tool_def.find("Definition")
        if definition is not None:
            name_elem = definition.find("Name")
            if name_elem is not None and name_elem.text in tool_names:
                found.append(tool_def)
    return found


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

                # 기존 도구들 제거
                existing_tools = find_all_tool_elements(root)
                for existing_tool in existing_tools:
                    root.remove(existing_tool)

                # 모든 도구 추가
                add_all_tools_to_root(root, resolved_exe_path)

                if existing_tools:
                    result["message"] = "AI Assistant 도구가 업데이트되었습니다."
                else:
                    result["message"] = "AI Assistant 도구가 추가되었습니다."
            except ET.ParseError:
                # 파일이 비어있거나 유효하지 않은 XML인 경우 새로 생성
                root = create_new_customtools_xml(resolved_exe_path)
                result["message"] = "customtools.xml이 재생성되고 AI Assistant 도구가 추가되었습니다."
        else:
            # 새 파일 생성
            root = create_new_customtools_xml(resolved_exe_path)
            result["message"] = "customtools.xml이 생성되고 AI Assistant 도구가 추가되었습니다."

        # XML 저장
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")

        with open(customtools_path, "wb") as f:
            f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write(b'<!--perforce-xml-version=1.0-->\n')
            tree.write(f, encoding="UTF-8", xml_declaration=False)

        tool_names = ", ".join([f"'{t['name']}'" for t in TOOLS])
        result["success"] = True
        result["message"] += f"\n\n등록된 도구: {tool_names}"
        result["message"] += f"\n파일 위치: {customtools_path}"
        result["message"] += f"\n실행 파일: {resolved_exe_path}"
        result["message"] += "\n\nP4V를 재시작하면 메뉴에서 사용할 수 있습니다."

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

        existing_tools = find_all_tool_elements(root)
        if not existing_tools:
            result["message"] = "AI Assistant 도구가 설치되어 있지 않습니다."
            result["success"] = True
            return result

        for existing_tool in existing_tools:
            root.remove(existing_tool)

        # XML 저장
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")

        with open(customtools_path, "wb") as f:
            f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write(b'<!--perforce-xml-version=1.0-->\n')
            tree.write(f, encoding="UTF-8", xml_declaration=False)

        result["success"] = True
        result["message"] = "AI Assistant 도구가 제거되었습니다.\n\nP4V를 재시작하면 변경사항이 적용됩니다."

    except Exception as e:
        result["message"] = f"제거 중 오류 발생: {e}"

    return result


class InstallError(Exception):
    """설치 관련 에러"""
    pass
