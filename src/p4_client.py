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
    diff: str = ""              # 변경사항만 (context 3줄, -du)
    diff_full: str = ""         # 전체 소스 (context 10000줄, -du10000)
    # 전체 소스 뷰용 필드 (향후 사용)
    original_content: str = ""  # 이전 버전 전체 내용
    new_content: str = ""       # 변경 후 전체 내용


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
        """Changelist 정보와 diff 조회 (변경사항만 + 전체소스 두 버전)"""
        # 먼저 기본 정보 조회
        output = self._run("describe", "-s", str(changelist))
        info = self._parse_describe(output, changelist)

        # pending CL인 경우 p4 diff로 diff 수집
        if info.status == "pending":
            self._collect_pending_diffs(info, changelist)
        else:
            # submitted CL인 경우 두 가지 버전 diff 수집
            # 1. 변경사항만 (context 3줄)
            output_short = self._run("describe", "-du", str(changelist))
            info = self._parse_describe_with_diff(output_short, changelist)
            # 2. 전체 소스 (context 10000줄)
            output_full = self._run("describe", "-du10000", str(changelist))
            self._parse_describe_with_diff_full(output_full, info)

        return info

    def _collect_pending_diffs(self, info: ChangelistInfo, changelist: int) -> None:
        """Pending changelist의 파일별 diff 수집 (변경사항만 + 전체소스 두 버전)"""
        for file_change in info.files:
            try:
                # action에 따라 다르게 처리
                if file_change.action in ("add", "branch", "move/add"):
                    # 새 파일은 전체 내용을 diff로 표시 (두 버전 동일)
                    diff = self._get_new_file_content(file_change.depot_path, changelist)
                    file_change.diff = diff.strip()
                    file_change.diff_full = diff.strip()
                elif file_change.action in ("delete", "move/delete"):
                    # 삭제 파일은 간단히 표시 (두 버전 동일)
                    diff = f"(파일 삭제됨: {file_change.depot_path})"
                    file_change.diff = diff
                    file_change.diff_full = diff
                else:
                    # edit, integrate 등은 p4 diff 사용
                    # 1. 변경사항만 (context 3줄)
                    diff_short = self._run("diff", "-du", file_change.depot_path)
                    file_change.diff = diff_short.strip()
                    # 2. 전체 소스 (context 10000줄)
                    diff_full = self._run("diff", "-du10000", file_change.depot_path)
                    file_change.diff_full = diff_full.strip()
            except P4Error as e:
                # diff 실패 시 에러 메시지 포함
                error_msg = f"(diff 실패: {str(e)[:100]})"
                file_change.diff = error_msg
                file_change.diff_full = error_msg

    def _get_new_file_content(self, depot_path: str, changelist: int) -> str:
        """새로 추가된 파일의 내용을 diff 형식으로 반환"""
        try:
            # shelved 파일인 경우
            content = self._run("print", "-q", f"{depot_path}@={changelist}")
            if content:
                lines = content.split("\n")
                # unified diff 형식으로 변환
                diff_lines = [f"@@ -0,0 +1,{len(lines)} @@"]
                diff_lines.extend(f"+{line}" for line in lines)
                return "\n".join(diff_lines)
        except P4Error:
            pass

        try:
            # workspace의 로컬 파일인 경우
            # opened 파일 정보에서 로컬 경로 확인
            opened_info = self._run("opened", "-c", str(changelist), depot_path)
            # p4 where로 로컬 경로 확인
            where_output = self._run("where", depot_path)
            if where_output:
                parts = where_output.strip().split(" ")
                if len(parts) >= 3:
                    local_path = parts[-1]
                    try:
                        with open(local_path, "r", encoding="utf-8", errors="replace") as f:
                            content = f.read()
                        lines = content.split("\n")
                        diff_lines = [f"@@ -0,0 +1,{len(lines)} @@"]
                        diff_lines.extend(f"+{line}" for line in lines)
                        return "\n".join(diff_lines)
                    except (IOError, OSError):
                        pass
        except P4Error:
            pass

        return "(새 파일 - 내용을 가져올 수 없음)"

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

    def _parse_describe_with_diff_full(self, output: str, info: ChangelistInfo) -> None:
        """p4 describe -du10000 출력을 파싱하여 diff_full 필드 채우기 (in-place)"""
        current_file = None
        diff_lines = []
        in_diff = False

        for line in output.split("\n"):
            # 새 파일의 diff 시작
            if line.startswith("==== "):
                # 이전 파일의 diff_full 저장
                if current_file and diff_lines:
                    for f in info.files:
                        if f.depot_path == current_file:
                            f.diff_full = "\n".join(diff_lines)
                            break

                # 새 파일 정보 추출
                match = re.match(r"==== (.+)#\d+ .+ ====", line)
                if match:
                    current_file = match.group(1)
                    diff_lines = []
                    in_diff = True
            elif in_diff:
                diff_lines.append(line)

        # 마지막 파일의 diff_full 저장
        if current_file and diff_lines:
            for f in info.files:
                if f.depot_path == current_file:
                    f.diff_full = "\n".join(diff_lines)
                    break

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

    def get_file_content(self, depot_path: str, revision: int = 0) -> str:
        """특정 리비전의 파일 내용 조회

        Args:
            depot_path: depot 경로 (예: //depot/path/file.cpp)
            revision: 리비전 번호 (0이면 head)

        Returns:
            파일 내용 문자열
        """
        try:
            spec = f"{depot_path}#{revision}" if revision else depot_path
            return self._run("print", "-q", spec)
        except P4Error:
            return ""

    def get_shelved_content(self, depot_path: str, changelist: int) -> str:
        """Shelved 파일 내용 조회

        Args:
            depot_path: depot 경로
            changelist: changelist 번호

        Returns:
            파일 내용 문자열
        """
        try:
            return self._run("print", "-q", f"{depot_path}@={changelist}")
        except P4Error:
            return ""

    def get_have_revision(self, depot_path: str) -> int:
        """로컬 workspace의 have 리비전 조회

        Args:
            depot_path: depot 경로

        Returns:
            have 리비전 번호 (없으면 0)
        """
        try:
            output = self._run("have", depot_path)
            # 출력 형식: //depot/file.cpp#5 - /local/path/file.cpp
            match = re.search(r"#(\d+)", output)
            return int(match.group(1)) if match else 0
        except P4Error:
            return 0

    def get_local_file_content(self, depot_path: str) -> str:
        """로컬 workspace 파일 내용 조회

        Args:
            depot_path: depot 경로

        Returns:
            파일 내용 문자열 (없으면 빈 문자열)
        """
        try:
            where_output = self._run("where", depot_path)
            if where_output:
                parts = where_output.strip().split(" ")
                if len(parts) >= 3:
                    local_path = parts[-1]
                    try:
                        with open(local_path, "r", encoding="utf-8", errors="replace") as f:
                            return f.read()
                    except (IOError, OSError):
                        pass
        except P4Error:
            pass
        return ""

    def collect_file_contents(
        self,
        file_change: FileChange,
        changelist: int,
        cl_status: str
    ) -> None:
        """파일의 이전/현재 버전 내용 수집 (in-place 수정)

        Args:
            file_change: FileChange 객체 (original_content, new_content가 채워짐)
            changelist: CL 번호
            cl_status: 'pending' 또는 'submitted'
        """
        depot_path = file_change.depot_path
        action = file_change.action
        revision = file_change.revision

        # 원본 내용 수집 (add가 아닌 경우)
        if action not in ("add", "branch", "move/add"):
            if cl_status == "pending":
                # pending CL: have 리비전에서 원본 가져오기
                have_rev = self.get_have_revision(depot_path)
                if have_rev > 0:
                    file_change.original_content = self.get_file_content(depot_path, have_rev)
            else:
                # submitted CL: 이전 리비전에서 원본 가져오기
                if revision > 1:
                    file_change.original_content = self.get_file_content(depot_path, revision - 1)

        # 새 내용 수집 (delete가 아닌 경우)
        if action not in ("delete", "move/delete"):
            if cl_status == "pending":
                # pending CL: shelved 먼저 시도, 없으면 로컬 파일
                content = self.get_shelved_content(depot_path, changelist)
                if not content:
                    content = self.get_local_file_content(depot_path)
                file_change.new_content = content
            else:
                # submitted CL: 해당 리비전에서 가져오기
                file_change.new_content = self.get_file_content(depot_path, revision)


class P4Error(Exception):
    """Perforce 관련 에러"""
    pass
