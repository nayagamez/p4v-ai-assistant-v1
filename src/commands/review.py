"""
AI 코드 리뷰 명령
Changelist의 diff를 분석하여 코드 리뷰 수행
"""
from dataclasses import dataclass, field
from typing import Callable, Optional, List, Dict, Any

from ..p4_client import P4Client, P4Error, ChangelistInfo, FileChange
from ..n8n_client import N8NClient, N8NError


# 배치 분할 임계값
MAX_FILES_PER_BATCH = 10
MAX_LINES_PER_BATCH = 1000


@dataclass
class ReviewComment:
    """코드 리뷰 코멘트"""
    file_path: str
    line_number: int
    severity: str  # critical, warning, info, suggestion
    category: str  # bug, security, performance, style, maintainability
    message: str
    suggestion: str = ""


@dataclass
class ReviewResult:
    """코드 리뷰 결과"""
    success: bool = False
    summary: str = ""
    overall_score: int = 0
    comments: List[ReviewComment] = field(default_factory=list)
    statistics: Dict[str, int] = field(default_factory=lambda: {
        "critical": 0,
        "warning": 0,
        "info": 0,
        "suggestion": 0
    })
    error: str = ""


class ReviewGenerator:
    """AI 코드 리뷰 생성기"""

    def __init__(
        self,
        port: str = "",
        user: str = "",
        client: str = "",
        webhook_url: str = ""
    ):
        self.p4 = P4Client(port=port, user=user, client=client)
        self.n8n = N8NClient(webhook_url=webhook_url) if webhook_url else N8NClient()

    def generate(
        self,
        changelist: int,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> ReviewResult:
        """
        AI 코드 리뷰 수행

        대용량 changelist는 배치로 분할하여 처리

        Args:
            changelist: Changelist 번호
            progress_callback: 진행 상황 콜백 함수

        Returns:
            ReviewResult: 리뷰 결과
        """
        result = ReviewResult()

        try:
            # Step 1: Changelist 정보 수집
            if progress_callback:
                progress_callback("Changelist 정보 수집 중...")

            changelist_info = self.p4.get_changelist_with_diff(changelist)

            if not changelist_info.files:
                result.error = "변경된 파일이 없습니다."
                return result

            # Step 2: 배치 분할
            batches = self._split_into_batches(changelist_info.files)
            total_batches = len(batches)

            if progress_callback:
                if total_batches > 1:
                    progress_callback(f"총 {total_batches}개 배치로 리뷰 진행...")
                else:
                    progress_callback("AI 코드 리뷰 중...")

            # Step 3: 배치별 리뷰 요청
            batch_results = []
            for i, batch_files in enumerate(batches, 1):
                if progress_callback and total_batches > 1:
                    progress_callback(f"배치 {i}/{total_batches} 리뷰 중...")

                batch_result = self._review_batch(batch_files, changelist_info)
                batch_results.append(batch_result)

            # Step 4: 결과 병합
            if progress_callback:
                progress_callback("리뷰 결과 처리 중...")

            result = self._merge_results(batch_results)
            result.success = True

        except P4Error as e:
            result.error = f"Perforce 오류: {str(e)}"
        except N8NError as e:
            result.error = f"AI 서비스 오류: {str(e)}"
        except Exception as e:
            result.error = f"예상치 못한 오류: {str(e)}"

        return result

    def _split_into_batches(self, files: List[FileChange]) -> List[List[FileChange]]:
        """
        파일 목록을 배치로 분할

        Args:
            files: 파일 목록

        Returns:
            배치로 분할된 파일 목록
        """
        total_files = len(files)
        total_lines = sum(len(f.diff.split('\n')) if f.diff else 0 for f in files)

        # 분할이 필요 없는 경우
        if total_files <= MAX_FILES_PER_BATCH and total_lines <= MAX_LINES_PER_BATCH:
            return [files]

        batches = []
        current_batch: List[FileChange] = []
        current_lines = 0

        for file in files:
            file_lines = len(file.diff.split('\n')) if file.diff else 0

            # 현재 배치에 추가하면 임계값 초과하는지 확인
            would_exceed_files = len(current_batch) >= MAX_FILES_PER_BATCH
            would_exceed_lines = current_lines + file_lines > MAX_LINES_PER_BATCH

            if current_batch and (would_exceed_files or would_exceed_lines):
                batches.append(current_batch)
                current_batch = []
                current_lines = 0

            current_batch.append(file)
            current_lines += file_lines

        if current_batch:
            batches.append(current_batch)

        return batches

    def _review_batch(
        self,
        files: List[FileChange],
        original_info: ChangelistInfo
    ) -> Dict[str, Any]:
        """
        단일 배치 리뷰 요청

        Args:
            files: 배치에 포함된 파일 목록
            original_info: 원본 Changelist 정보

        Returns:
            n8n 응답 딕셔너리
        """
        # 배치용 ChangelistInfo 생성
        batch_info = ChangelistInfo(
            number=original_info.number,
            user=original_info.user,
            client=original_info.client,
            status=original_info.status,
            description=original_info.description,
            files=files
        )

        return self.n8n.request_review(batch_info)

    def _merge_results(self, batch_results: List[Dict[str, Any]]) -> ReviewResult:
        """
        여러 배치의 결과를 병합

        Args:
            batch_results: 배치별 결과 리스트

        Returns:
            병합된 ReviewResult
        """
        merged = ReviewResult()
        all_comments: List[ReviewComment] = []
        total_score = 0
        valid_batches = 0
        summaries: List[str] = []

        for result in batch_results:
            if not result.get("success", False):
                continue

            valid_batches += 1

            # 코멘트 병합
            for comment_data in result.get("comments", []):
                comment = ReviewComment(
                    file_path=comment_data.get("file_path", ""),
                    line_number=comment_data.get("line_number", 0),
                    severity=comment_data.get("severity", "info"),
                    category=comment_data.get("category", ""),
                    message=comment_data.get("message", ""),
                    suggestion=comment_data.get("suggestion", "")
                )
                all_comments.append(comment)

            # 점수 누적 (평균용)
            total_score += result.get("overall_score", 0)

            # 요약 수집
            if result.get("summary"):
                summaries.append(result["summary"])

            # 통계 합산
            stats = result.get("statistics", {})
            for severity in ["critical", "warning", "info", "suggestion"]:
                merged.statistics[severity] += stats.get(severity, 0)

        merged.comments = all_comments
        merged.overall_score = total_score // valid_batches if valid_batches > 0 else 0
        merged.summary = " ".join(summaries) if summaries else "리뷰 완료"

        return merged


def run_review_command(
    changelist: int,
    port: str = "",
    user: str = "",
    client: str = "",
    webhook_url: str = "",
    progress_callback: Optional[Callable[[str], None]] = None
) -> ReviewResult:
    """코드 리뷰 명령 실행 헬퍼 함수"""
    generator = ReviewGenerator(
        port=port,
        user=user,
        client=client,
        webhook_url=webhook_url
    )
    return generator.generate(
        changelist=changelist,
        progress_callback=progress_callback
    )
