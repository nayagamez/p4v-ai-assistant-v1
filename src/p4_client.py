"""
Perforce 명령어 래퍼 모듈
p4 CLI를 통해 Changelist 정보 수집
"""
import subprocess
import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class FileChange:
    """변경된 파일 정보"""
    depot_path: str
    action: str
    file_type: str = ""
    revision: int = 0
    diff: str = ""


@dataclass
class ChangelistInfo:
    """Changelist 정보"""
    number: int
    user: str = ""
    client: str = ""
    status: str = ""
    description: str = ""
    files: List[FileChange] = field(default_factory=list)


class P4Client:
    def __init__(self, port: str = "", user: str = "", client: str = ""):
        self.port = port
        self.user = user
        self.client = client

    def _build_cmd(self, *args) -> List[str]:
        """p4 명령어 구성"""
        cmd = ["p4"]
        if self.port:
            cmd.extend(["-p", self.port])
        if self.user:
            cmd.extend(["-u", self.user])
        if self.client:
            cmd.extend(["-c", self.client])
        cmd.extend(args)
        return cmd

    def _run(self, *args) -> str:
        """p4 명령어 실행"""
        cmd = self._build_cmd(*args)
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            if result.returncode != 0 and result.stderr:
                raise P4Error(f"p4 명령 실패: {result.stderr}")
            return result.stdout
        except FileNotFoundError:
            raise P4Error("p4 명령어를 찾을 수 없습니다. Perforce가 설치되어 있는지 확인하세요.")

    def get_changelist_info(self, changelist: int) -> ChangelistInfo:
        """Changelist 기본 정보 조회 (p4 describe)"""
        output = self._run("describe", "-s", str(changelist))
        return self._parse_describe(output, changelist)

    def get_changelist_with_diff(self, changelist: int) -> ChangelistInfo:
        """Changelist 정보와 diff 조회 (p4 describe -du)"""
        output = self._run("describe", "-du", str(changelist))
        return self._parse_describe_with_diff(output, changelist)

    def _parse_describe(self, output: str, changelist: int) -> ChangelistInfo:
        """p4 describe 출력 파싱"""
        info = ChangelistInfo(number=changelist)

        lines = output.split("\n")
        for line in lines:
            if line.startswith("Change"):
                match = re.match(r"Change (\d+) by ([^@]+)@(\S+) on .* \*?(\w+)\*?", line)
                if match:
                    info.number = int(match.group(1))
                    info.user = match.group(2)
                    info.client = match.group(3)
                    info.status = match.group(4) if match.group(4) else "pending"

        # Description 파싱
        desc_start = False
        desc_lines = []
        for line in lines:
            if desc_start:
                if line.startswith("Affected files") or line.startswith("Jobs fixed"):
                    break
                desc_lines.append(line.strip())
            elif line.strip() == "":
                desc_start = True

        info.description = "\n".join(desc_lines).strip()

        # 파일 목록 파싱
        file_section = False
        for line in lines:
            if "Affected files" in line:
                file_section = True
                continue
            if file_section and line.startswith("..."):
                match = re.match(r"\.\.\. (.+)#(\d+) (\w+)", line)
                if match:
                    info.files.append(FileChange(
                        depot_path=match.group(1),
                        revision=int(match.group(2)),
                        action=match.group(3)
                    ))

        return info

    def _parse_describe_with_diff(self, output: str, changelist: int) -> ChangelistInfo:
        """p4 describe -du 출력 파싱 (diff 포함)"""
        info = self._parse_describe(output, changelist)

        # Diff 파싱
        current_file = None
        diff_lines = []
        in_diff = False

        for line in output.split("\n"):
            # 새 파일의 diff 시작
            if line.startswith("==== "):
                # 이전 파일의 diff 저장
                if current_file and diff_lines:
                    for f in info.files:
                        if f.depot_path == current_file:
                            f.diff = "\n".join(diff_lines)
                            break

                # 새 파일 정보 추출
                match = re.match(r"==== (.+)#\d+ .+ ====", line)
                if match:
                    current_file = match.group(1)
                    diff_lines = []
                    in_diff = True
            elif in_diff:
                diff_lines.append(line)

        # 마지막 파일의 diff 저장
        if current_file and diff_lines:
            for f in info.files:
                if f.depot_path == current_file:
                    f.diff = "\n".join(diff_lines)
                    break

        return info

    def update_changelist_description(self, changelist: int, description: str) -> bool:
        """Changelist description 업데이트 (p4 change -i)"""
        # 현재 changelist 정보 가져오기
        output = self._run("change", "-o", str(changelist))

        # Description 교체
        lines = output.split("\n")
        new_lines = []
        in_description = False
        description_done = False

        for line in lines:
            if line.startswith("Description:"):
                new_lines.append(line)
                new_lines.append(f"\t{description.replace(chr(10), chr(10) + chr(9))}")
                in_description = True
                description_done = True
            elif in_description:
                if line.startswith("\t") or line.strip() == "":
                    continue  # 기존 description 스킵
                else:
                    in_description = False
                    new_lines.append(line)
            else:
                new_lines.append(line)

        # p4 change -i로 업데이트
        new_spec = "\n".join(new_lines)
        cmd = self._build_cmd("change", "-i")
        try:
            result = subprocess.run(
                cmd,
                input=new_spec,
                capture_output=True,
                text=True,
                encoding="utf-8"
            )
            if result.returncode != 0:
                raise P4Error(f"Description 업데이트 실패: {result.stderr}")
            return True
        except Exception as e:
            raise P4Error(f"Description 업데이트 실패: {str(e)}")


class P4Error(Exception):
    """Perforce 관련 에러"""
    pass
