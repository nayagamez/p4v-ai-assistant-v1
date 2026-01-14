"""
HTML 리포트 생성 모듈
코드 리뷰 결과를 Side-by-side diff 뷰와 함께 HTML 형식으로 내보내기
"""
import html
import json
import re
from typing import TYPE_CHECKING, List, Dict, Set
from urllib.parse import unquote

if TYPE_CHECKING:
    from ..commands.review import ReviewResult, ReviewComment
    from ..p4_client import FileChange

from .diff2html_bundle import DIFF2HTML_CSS, DIFF2HTML_JS


def count_diff_changes(diff_text: str) -> int:
    """diff에서 변경된 라인 수 카운트 (네비게이션 표시용)"""
    if not diff_text:
        return 0
    count = 0
    for line in diff_text.split('\n'):
        if line.startswith('+') and not line.startswith('+++'):
            count += 1
    return count


def normalize_path(path: str) -> str:
    """
    경로 정규화 (URL 인코딩 해제)

    Perforce depot 경로에서 @가 %40으로 인코딩되는 문제 해결
    예: com.unity.addressables%401.21.2 → com.unity.addressables@1.21.2
    """
    return unquote(path)


def normalize_unified_diff(depot_path: str, diff_text: str, action: str) -> str:
    """
    diff2html 호환 unified diff 형식으로 변환

    Args:
        depot_path: depot 경로
        diff_text: 원본 diff 텍스트
        action: add, edit, delete 등

    Returns:
        표준 unified diff 형식 문자열
    """
    if not diff_text:
        return ""

    file_name = depot_path.split("/")[-1]
    lines = diff_text.strip().split("\n")

    # 이미 --- / +++ 헤더가 있는지 확인
    has_header = any(line.startswith("---") for line in lines[:5])

    if has_header:
        return diff_text

    # 헤더 생성
    if action in ("add", "branch", "move/add"):
        header = f"--- /dev/null\n+++ b/{file_name}\n"
    elif action in ("delete", "move/delete"):
        header = f"--- a/{file_name}\n+++ /dev/null\n"
    else:  # edit, integrate 등
        header = f"--- a/{file_name}\n+++ b/{file_name}\n"

    return header + diff_text


# HTML 템플릿 - 탭 UI, diff2html 통합, AI 코멘트 인라인 표시
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>코드 리뷰 - Changelist #{changelist}</title>
    <style>
        /* diff2html 스타일 */
        {diff2html_css}

        /* 커스텀 스타일 */
        * {{ box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', 'Malgun Gothic', Arial, sans-serif;
            margin: 0;
            padding: 0;
            background: #f0f2f5;
            color: #333;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}

        /* 헤더 */
        .review-header {{
            background: white;
            padding: 20px 30px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 20px;
            flex-wrap: wrap;
        }}
        .review-header h1 {{
            margin: 0;
            color: #1a1a2e;
            font-size: 24px;
        }}
        .changelist-badge {{
            background: #e3f2fd;
            color: #1565c0;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 600;
        }}
        .score-badge {{
            font-size: 28px;
            font-weight: bold;
            padding: 5px 15px;
            border-radius: 8px;
        }}
        .score-badge.high {{ background: #e8f5e9; color: #2e7d32; }}
        .score-badge.medium {{ background: #fff3e0; color: #ef6c00; }}
        .score-badge.low {{ background: #ffebee; color: #c62828; }}

        /* 통계 바 */
        .stats-bar {{
            display: flex;
            gap: 10px;
            margin-left: auto;
        }}
        .stat-item {{
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 600;
        }}
        .stat-item.critical {{ background: #ffebee; color: #c62828; }}
        .stat-item.warning {{ background: #fff3e0; color: #ef6c00; }}
        .stat-item.info {{ background: #e3f2fd; color: #1565c0; }}
        .stat-item.suggestion {{ background: #e8f5e9; color: #2e7d32; }}

        /* 탭 네비게이션 */
        .tab-nav {{
            display: flex;
            gap: 5px;
            background: white;
            padding: 10px;
            border-radius: 12px 12px 0 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .tab-btn {{
            padding: 12px 24px;
            border: none;
            background: transparent;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            color: #666;
            border-radius: 8px;
            transition: all 0.2s;
        }}
        .tab-btn:hover {{ background: #f5f5f5; }}
        .tab-btn.active {{
            background: #4a90d9;
            color: white;
        }}
        .tab-btn .badge {{
            background: rgba(0,0,0,0.1);
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 12px;
            margin-left: 5px;
        }}
        .tab-btn.active .badge {{ background: rgba(255,255,255,0.3); }}

        /* 탭 컨텐츠 */
        .tab-content {{
            background: white;
            padding: 25px;
            border-radius: 0 0 12px 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            display: none;
        }}
        .tab-content.active {{ display: block; }}

        /* 요약 탭 */
        .summary-box {{
            background: #e8f4fd;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #4a90d9;
            line-height: 1.6;
            margin-bottom: 20px;
        }}

        /* Diff 탭 - 파일 서브탭 */
        .file-tabs {{
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
            padding: 10px;
            background: #f5f5f5;
            border-bottom: 1px solid #ddd;
            margin-bottom: 0;
        }}
        .file-tab {{
            padding: 8px 16px;
            border: 1px solid #ddd;
            background: white;
            cursor: pointer;
            border-radius: 6px;
            font-size: 13px;
            font-family: 'Consolas', 'Courier New', monospace;
            transition: all 0.2s;
        }}
        .file-tab:hover {{ background: #e3f2fd; }}
        .file-tab.active {{
            background: #4a90d9;
            color: white;
            border-color: #4a90d9;
        }}
        .file-tab .action-badge {{
            font-size: 10px;
            padding: 2px 5px;
            border-radius: 3px;
            margin-left: 5px;
            text-transform: uppercase;
        }}
        .file-tab .action-badge.add {{ background: #c8e6c9; color: #2e7d32; }}
        .file-tab .action-badge.edit {{ background: #bbdefb; color: #1565c0; }}
        .file-tab .action-badge.delete {{ background: #ffcdd2; color: #c62828; }}
        .file-tab.active .action-badge {{ background: rgba(255,255,255,0.3); color: white; }}
        .file-tab .comment-badge {{
            background: #ff5722;
            color: white;
            padding: 2px 6px;
            border-radius: 10px;
            font-size: 11px;
            margin-left: 5px;
        }}
        .file-tab .comment-badge.zero {{ background: #9e9e9e; }}
        .file-tab.active .comment-badge {{ background: rgba(255,255,255,0.4); }}

        /* Diff 컨테이너 - flex 레이아웃으로 헤더 고정 */
        .file-diff {{
            display: none;
            border: 1px solid #ddd;
            border-top: none;
            border-radius: 0 0 8px 8px;
            overflow: hidden;
            flex-direction: column;
            height: calc(100vh - 280px);
            min-height: 400px;
        }}
        .file-diff.active {{ display: flex; }}
        .file-header {{
            background: #f7f7f7;
            padding: 12px 15px;
            display: flex;
            align-items: center;
            gap: 10px;
            border-bottom: 1px solid #ddd;
            flex-shrink: 0;
        }}

        /* diff2html sticky 비활성화 (스크롤 컨테이너 충돌 방지) */
        .d2h-code-side-linenumber,
        .d2h-code-linenumber {{
            position: static !important;
        }}
        .file-name {{
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 13px;
            font-weight: 600;
        }}
        .file-action {{
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }}
        .file-action.add {{ background: #e8f5e9; color: #2e7d32; }}
        .file-action.edit {{ background: #e3f2fd; color: #1565c0; }}
        .file-action.delete {{ background: #ffebee; color: #c62828; }}
        .file-action.integrate {{ background: #fff3e0; color: #ef6c00; }}
        .comment-count {{
            margin-left: auto;
            font-size: 12px;
            color: #666;
        }}
        /* 스크롤 영역 - 이 부분만 스크롤됨 */
        .diff-scroll-container {{
            flex: 1;
            overflow-y: auto;
            overflow-x: auto;
        }}
        .diff-content {{
            min-height: 100%;
        }}
        .no-diff {{
            padding: 30px;
            text-align: center;
            color: #999;
        }}

        /* AI 코멘트 인라인 */
        .ai-comment-row {{
            border-left: 4px solid;
            background: #fafafa;
        }}
        .ai-comment-row.severity-critical {{ border-left-color: #dc3545; background: #fff5f5; }}
        .ai-comment-row.severity-warning {{ border-left-color: #ff9800; background: #fffaf0; }}
        .ai-comment-row.severity-info {{ border-left-color: #2196f3; background: #f0f7ff; }}
        .ai-comment-row.severity-suggestion {{ border-left-color: #4caf50; background: #f0fff4; }}

        .ai-comment-cell {{
            padding: 12px 16px !important;
        }}
        .ai-comment {{
            font-family: 'Segoe UI', sans-serif;
        }}
        .severity-badge {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            margin-right: 8px;
        }}
        .severity-badge.critical {{ background: #ffebee; color: #c62828; }}
        .severity-badge.warning {{ background: #fff3e0; color: #ef6c00; }}
        .severity-badge.info {{ background: #e3f2fd; color: #1565c0; }}
        .severity-badge.suggestion {{ background: #e8f5e9; color: #2e7d32; }}

        .category-tag {{
            display: inline-block;
            background: #f0f0f0;
            color: #666;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 11px;
            margin-right: 8px;
        }}
        .comment-message {{
            margin-top: 8px;
            line-height: 1.5;
        }}
        .comment-suggestion {{
            background: #f5f5f5;
            padding: 10px 12px;
            margin-top: 10px;
            border-radius: 4px;
            font-size: 13px;
            border-left: 3px solid #4caf50;
        }}
        .comment-suggestion strong {{ color: #2e7d32; }}

        /* 코멘트 목록 탭 */
        .comment-list {{
            list-style: none;
            padding: 0;
            margin: 0;
        }}
        .comment-item {{
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            margin-bottom: 15px;
            overflow: hidden;
            transition: box-shadow 0.2s;
        }}
        .comment-item:hover {{ box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .comment-item-header {{
            padding: 12px 15px;
            background: #f8f9fa;
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
        }}
        .comment-item-body {{
            padding: 15px;
        }}
        .file-info {{
            font-family: 'Consolas', monospace;
            font-size: 13px;
            color: #555;
        }}

        /* 푸터 */
        .footer {{
            text-align: center;
            padding: 20px;
            color: #999;
            font-size: 12px;
        }}

        /* diff2html 오버라이드 */
        .d2h-wrapper {{ margin: 0; }}
        .d2h-file-wrapper {{ border: none; margin: 0; }}
        .d2h-file-header {{ display: none; }}

        /* 뷰 토글 및 네비게이션 */
        .view-controls {{
            display: flex;
            align-items: center;
            gap: 15px;
            margin-left: auto;
        }}
        .view-toggle {{
            display: flex;
            gap: 2px;
            background: #e0e0e0;
            border-radius: 6px;
            padding: 2px;
        }}
        .toggle-btn {{
            padding: 6px 12px;
            border: none;
            background: transparent;
            cursor: pointer;
            font-size: 12px;
            border-radius: 4px;
            transition: all 0.2s;
        }}
        .toggle-btn:hover {{ background: rgba(255,255,255,0.5); }}
        .toggle-btn.active {{
            background: #4a90d9;
            color: white;
        }}
        .nav-controls {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        .nav-btn {{
            padding: 4px 8px;
            border: 1px solid #ddd;
            background: white;
            cursor: pointer;
            border-radius: 4px;
            font-size: 12px;
        }}
        .nav-btn:hover {{ background: #f5f5f5; }}
        .nav-btn:disabled {{ opacity: 0.5; cursor: not-allowed; }}
        .position-indicator {{
            font-size: 12px;
            color: #666;
            min-width: 40px;
            text-align: center;
        }}

        /* 키보드 단축키 도움말 */
        .keyboard-help {{
            font-size: 11px;
            color: #999;
            margin-left: 10px;
        }}
        .keyboard-help kbd {{
            background: #f0f0f0;
            padding: 2px 5px;
            border-radius: 3px;
            border: 1px solid #ddd;
            font-family: monospace;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- 헤더 -->
        <header class="review-header">
            <h1>코드 리뷰 결과</h1>
            <span class="changelist-badge">CL #{changelist}</span>
            <span class="score-badge {score_class}">{score}/100</span>
            <div class="stats-bar">
                <span class="stat-item critical">Critical: {critical}</span>
                <span class="stat-item warning">Warning: {warning}</span>
                <span class="stat-item info">Info: {info}</span>
                <span class="stat-item suggestion">Suggestion: {suggestion_count}</span>
            </div>
        </header>

        <!-- 탭 네비게이션 -->
        <nav class="tab-nav">
            <button class="tab-btn active" data-tab="summary">요약<span class="badge">{comment_count}</span></button>
            <button class="tab-btn" data-tab="diff">Diff 뷰<span class="badge">{file_count}</span></button>
        </nav>

        <!-- 요약 + 코멘트 탭 -->
        <div class="tab-content active" id="summary">
            <div class="summary-box">{summary}</div>
            <h3 style="margin: 25px 0 15px 0; color: #333;">코멘트 ({comment_count})</h3>
            {comments_html}
        </div>

        <!-- Diff 탭 -->
        <div class="tab-content" id="diff">
            {file_tabs_html}
            {files_diff_html}
        </div>

        <div class="footer">Generated by P4V AI Assistant</div>
    </div>

    <script>
        {diff2html_js}
    </script>
    <script>
        // 메인 탭 전환
        document.querySelectorAll('.tab-btn').forEach(function(btn) {{
            btn.addEventListener('click', function() {{
                var targetTab = this.getAttribute('data-tab');

                document.querySelectorAll('.tab-btn').forEach(function(b) {{
                    b.classList.remove('active');
                }});
                this.classList.add('active');

                document.querySelectorAll('.tab-content').forEach(function(content) {{
                    content.classList.remove('active');
                }});
                document.getElementById(targetTab).classList.add('active');

                // diff 탭 첫 진입 시 첫 번째 파일 렌더링
                if (targetTab === 'diff' && !window.diffInitialized) {{
                    initFileTabs();
                    window.diffInitialized = true;
                }}
            }});
        }});

        // 파일 탭 초기화
        function initFileTabs() {{
            // 파일 탭 클릭 이벤트
            document.querySelectorAll('.file-tab').forEach(function(tab) {{
                tab.addEventListener('click', function() {{
                    var fileIndex = this.getAttribute('data-file-index');

                    // 탭 활성화
                    document.querySelectorAll('.file-tab').forEach(function(t) {{
                        t.classList.remove('active');
                    }});
                    this.classList.add('active');

                    // diff 컨테이너 전환
                    document.querySelectorAll('.file-diff').forEach(function(d) {{
                        d.classList.remove('active');
                    }});
                    var targetDiff = document.querySelector('.file-diff[data-file-index="' + fileIndex + '"]');
                    if (targetDiff) {{
                        targetDiff.classList.add('active');

                        // 해당 파일 diff 렌더링 (lazy)
                        if (!targetDiff.getAttribute('data-rendered')) {{
                            renderSingleDiff(targetDiff);
                            targetDiff.setAttribute('data-rendered', 'true');
                            initViewToggle(targetDiff);
                            initNavigation(targetDiff);
                        }}

                        // 네비게이션 상태 초기화
                        resetNavState();
                    }}
                }});
            }});

            // 첫 번째 파일 렌더링
            var firstDiff = document.querySelector('.file-diff.active');
            if (firstDiff && !firstDiff.getAttribute('data-rendered')) {{
                renderSingleDiff(firstDiff);
                firstDiff.setAttribute('data-rendered', 'true');
                initViewToggle(firstDiff);
                initNavigation(firstDiff);
            }}
        }}

        // 단일 파일 diff 렌더링 (mode: 'diff' 또는 'full')
        function renderSingleDiff(container, mode) {{
            mode = mode || 'diff';
            var diffText = mode === 'full'
                ? container.getAttribute('data-diff-full')
                : container.getAttribute('data-diff');

            // full 모드에서 diff-full이 없으면 일반 diff로 fallback
            if (mode === 'full' && !diffText) {{
                diffText = container.getAttribute('data-diff');
            }}

            if (!diffText || diffText === '(바이너리 파일)' || diffText.startsWith('(')) {{
                container.querySelector('.diff-content').innerHTML =
                    '<div class="no-diff">' + (diffText || 'diff 데이터 없음') + '</div>';
                return;
            }}

            try {{
                var diffHtml = Diff2Html.html(diffText, {{
                    drawFileList: false,
                    matching: 'lines',
                    outputFormat: 'side-by-side'
                }});
                container.querySelector('.diff-content').innerHTML = diffHtml;

                // 코멘트 삽입
                var commentsData = container.getAttribute('data-comments');
                if (commentsData) {{
                    insertComments(container, JSON.parse(commentsData));
                }}

                // 현재 모드 저장
                container.setAttribute('data-current-mode', mode);
            }} catch (e) {{
                container.querySelector('.diff-content').innerHTML =
                    '<div class="no-diff">diff 렌더링 실패: ' + e.message + '</div>';
            }}
        }}

        // 코멘트 삽입 (오른쪽 패널 - 변경된 코드에만)
        function insertComments(container, comments) {{
            if (!comments || comments.length === 0) return;

            // side-by-side 모드: 오른쪽 패널(변경된 코드)만 선택
            var sidePanels = container.querySelectorAll('.d2h-file-side-diff');
            var rightPanel = sidePanels.length > 1 ? sidePanels[1] : container;

            comments.forEach(function(comment) {{
                var lineRow = null;

                // 오른쪽 패널에서 라인 번호 검색
                var lineNumberCells = rightPanel.querySelectorAll('.d2h-code-side-linenumber');
                lineNumberCells.forEach(function(cell) {{
                    if (parseInt(cell.textContent.trim()) === comment.line_number) {{
                        lineRow = cell.closest('tr');
                    }}
                }});

                // line-by-line 모드 fallback
                if (!lineRow) {{
                    var allLineCells = container.querySelectorAll('.d2h-code-linenumber .line-num2');
                    allLineCells.forEach(function(cell) {{
                        if (parseInt(cell.textContent.trim()) === comment.line_number) {{
                            lineRow = cell.closest('tr');
                        }}
                    }});
                }}

                if (lineRow) {{
                    var commentRow = document.createElement('tr');
                    commentRow.className = 'ai-comment-row severity-' + comment.severity;
                    commentRow.innerHTML = createCommentHTML(comment);
                    lineRow.parentNode.insertBefore(commentRow, lineRow.nextSibling);
                }}
            }});
        }}

        function createCommentHTML(comment) {{
            var suggestionHtml = '';
            if (comment.suggestion) {{
                suggestionHtml = '<div class="comment-suggestion"><strong>제안:</strong> ' +
                    escapeHtml(comment.suggestion) + '</div>';
            }}

            return '<td colspan="4" class="ai-comment-cell">' +
                '<div class="ai-comment">' +
                    '<span class="severity-badge ' + comment.severity + '">' +
                        comment.severity.toUpperCase() + '</span>' +
                    '<span class="category-tag">' + (comment.category || 'general') + '</span>' +
                    '<div class="comment-message">' + escapeHtml(comment.message) + '</div>' +
                    suggestionHtml +
                '</div>' +
            '</td>';
        }}

        function escapeHtml(text) {{
            var div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }}

        // 뷰 모드 토글 (diff2html 재렌더링 방식)
        function initViewToggle(container) {{
            container.querySelectorAll('.toggle-btn').forEach(function(btn) {{
                btn.addEventListener('click', function() {{
                    if (this.disabled) return;

                    var mode = this.getAttribute('data-mode');
                    var currentMode = container.getAttribute('data-current-mode') || 'diff';

                    // 같은 모드면 무시
                    if (mode === currentMode) return;

                    // 버튼 상태 업데이트
                    container.querySelectorAll('.toggle-btn').forEach(function(b) {{
                        b.classList.remove('active');
                    }});
                    this.classList.add('active');

                    // diff2html 재렌더링 (새 모드로)
                    renderSingleDiff(container, mode);

                    // 네비게이션 상태 초기화
                    resetNavState();
                }});
            }});
        }}

        // 네비게이션 상태
        var navState = {{
            changeIndex: -1,
            commentIndex: -1
        }};

        // 변경점 네비게이션
        function navigateChange(container, direction) {{
            var diffContent = container.querySelector('.diff-content');
            if (!diffContent) return;

            var changes = diffContent.querySelectorAll('.d2h-ins, .d2h-del');
            if (changes.length === 0) return;

            if (direction === 'next') {{
                navState.changeIndex = Math.min(navState.changeIndex + 1, changes.length - 1);
            }} else {{
                navState.changeIndex = Math.max(navState.changeIndex - 1, 0);
            }}

            // 스크롤 컨테이너 내에서만 스크롤 (페이지 전체 스크롤 방지)
            scrollToElement(container, changes[navState.changeIndex]);
            updatePositionIndicator(container, 'change', navState.changeIndex + 1, changes.length);
        }}

        // 코멘트 네비게이션
        function navigateComment(container, direction) {{
            var comments = container.querySelectorAll('.ai-comment-row');
            if (comments.length === 0) return;

            if (direction === 'next') {{
                navState.commentIndex = Math.min(navState.commentIndex + 1, comments.length - 1);
            }} else {{
                navState.commentIndex = Math.max(navState.commentIndex - 1, 0);
            }}

            // 스크롤 컨테이너 내에서만 스크롤 (페이지 전체 스크롤 방지)
            scrollToElement(container, comments[navState.commentIndex]);
            updatePositionIndicator(container, 'comment', navState.commentIndex + 1, comments.length);
        }}

        // 스크롤 컨테이너 내에서만 요소로 스크롤 (페이지 전체 스크롤 방지)
        function scrollToElement(container, element) {{
            var scrollContainer = container.querySelector('.diff-scroll-container');
            if (!scrollContainer || !element) return;

            var elementRect = element.getBoundingClientRect();
            var containerRect = scrollContainer.getBoundingClientRect();
            var offsetTop = elementRect.top - containerRect.top + scrollContainer.scrollTop;

            scrollContainer.scrollTo({{
                top: offsetTop - (scrollContainer.clientHeight / 2),
                behavior: 'smooth'
            }});
        }}

        function updatePositionIndicator(container, type, current, total) {{
            var indicator = container.querySelector('.' + type + '-pos');
            if (indicator) {{
                indicator.textContent = current + '/' + total;
            }}
        }}

        // 네비게이션 버튼 초기화
        function initNavigation(container) {{
            container.querySelectorAll('.nav-btn').forEach(function(btn) {{
                btn.addEventListener('click', function() {{
                    var action = this.getAttribute('data-action');
                    if (action === 'prev-change') {{
                        navigateChange(container, 'prev');
                    }} else if (action === 'next-change') {{
                        navigateChange(container, 'next');
                    }} else if (action === 'prev-comment') {{
                        navigateComment(container, 'prev');
                    }} else if (action === 'next-comment') {{
                        navigateComment(container, 'next');
                    }}
                }});
            }});
        }}

        // 키보드 단축키
        document.addEventListener('keydown', function(e) {{
            // 입력 필드에서는 무시
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

            var activeFile = document.querySelector('.file-diff.active');
            if (!activeFile) return;

            var key = e.key.toLowerCase();
            if (key === 'j') {{
                e.preventDefault();
                navigateChange(activeFile, 'next');
            }} else if (key === 'k') {{
                e.preventDefault();
                navigateChange(activeFile, 'prev');
            }} else if (key === 'n') {{
                e.preventDefault();
                navigateComment(activeFile, 'next');
            }} else if (key === 'p') {{
                e.preventDefault();
                navigateComment(activeFile, 'prev');
            }}
        }});

        // 파일 탭 전환 시 상태 초기화
        function resetNavState() {{
            navState.changeIndex = -1;
            navState.commentIndex = -1;
        }}
    </script>
</body>
</html>"""


COMMENT_TEMPLATE = """<li class="comment-item">
    <div class="comment-item-header">
        <span class="severity-badge {severity}">{severity_upper}</span>
        <span class="file-info">{file_path} : {line_number}</span>
    </div>
    <div class="comment-item-body">
        <span class="category-tag">{category}</span>
        <div class="comment-message">{message}</div>
        {suggestion_html}
    </div>
</li>"""


NO_COMMENTS_HTML = """<div style="text-align:center; padding:40px; color:#666;">
    <p>발견된 이슈가 없습니다.</p>
</div>"""


def _generate_file_tabs_html(files: List['FileChange'], comments: List['ReviewComment']) -> str:
    """파일 서브탭 HTML 생성"""
    if not files:
        return ''

    tab_parts = ['<div class="file-tabs">']

    for i, file in enumerate(files):
        file_name = file.depot_path.split("/")[-1]
        # URL 인코딩 정규화하여 비교 (예: %40 vs @)
        normalized_depot = normalize_path(file.depot_path)
        file_comments = [c for c in comments if normalize_path(c.file_path) == normalized_depot]
        comment_count = len(file_comments)
        action_class = file.action.replace("/", "-")

        # 첫 번째 파일은 active
        active_class = "active" if i == 0 else ""
        comment_badge_class = "zero" if comment_count == 0 else ""

        tab_parts.append(f'''
            <button class="file-tab {active_class}" data-file-index="{i}">
                {html.escape(file_name)}
                <span class="action-badge {action_class}">{html.escape(file.action)}</span>
                <span class="comment-badge {comment_badge_class}">{comment_count}</span>
            </button>
        ''')

    tab_parts.append('</div>')
    return "\n".join(tab_parts)


def _generate_files_diff_html(files: List['FileChange'], comments: List['ReviewComment']) -> str:
    """파일별 diff 컨테이너 HTML 생성"""
    if not files:
        return '<div class="no-diff">변경된 파일이 없습니다.</div>'

    html_parts = []

    for i, file in enumerate(files):
        # diff 정규화 (변경사항만)
        normalized_diff = normalize_unified_diff(
            file.depot_path,
            file.diff,
            file.action
        )

        # diff_full 정규화 (전체 소스)
        normalized_diff_full = normalize_unified_diff(
            file.depot_path,
            file.diff_full,
            file.action
        ) if file.diff_full else ""

        # 이 파일의 코멘트 (URL 인코딩 정규화하여 비교)
        normalized_depot = normalize_path(file.depot_path)
        file_comments = [c for c in comments if normalize_path(c.file_path) == normalized_depot]

        # HTML 이스케이프 (data 속성용)
        escaped_diff = html.escape(normalized_diff) if normalized_diff else ""
        escaped_diff_full = html.escape(normalized_diff_full) if normalized_diff_full else ""

        # 코멘트 JSON (dict 변환)
        comments_list = [{
            "file_path": c.file_path,
            "line_number": c.line_number,
            "severity": c.severity,
            "category": c.category,
            "message": c.message,
            "suggestion": c.suggestion
        } for c in file_comments]
        comments_json = json.dumps(comments_list, ensure_ascii=False)

        # action에 따른 CSS 클래스
        action_class = file.action.replace("/", "-")  # move/add -> move-add

        # 첫 번째 파일은 active
        active_class = "active" if i == 0 else ""

        # 전체 소스 diff 데이터 존재 여부
        has_full_diff = bool(escaped_diff_full)

        # 변경된 라인 수 계산 (네비게이션용)
        change_count = count_diff_changes(file.diff)

        html_parts.append(f'''
        <div class="file-diff {active_class}"
             data-file-index="{i}"
             data-file="{html.escape(file.depot_path)}"
             data-diff="{escaped_diff}"
             data-diff-full="{escaped_diff_full}"
             data-comments='{html.escape(comments_json)}'
             data-change-count="{change_count}">
            <div class="file-header">
                <span class="file-name">{html.escape(file.depot_path)}</span>
                <span class="file-action {action_class}">{html.escape(file.action)}</span>
                <div class="view-controls">
                    <div class="view-toggle">
                        <button class="toggle-btn active" data-mode="diff">변경사항만</button>
                        <button class="toggle-btn" data-mode="full" {"disabled" if not has_full_diff else ""}>전체 소스</button>
                    </div>
                    <div class="nav-controls">
                        <button class="nav-btn" data-action="prev-change" title="이전 변경 (K)">◀</button>
                        <span class="position-indicator change-pos">-/{change_count}</span>
                        <button class="nav-btn" data-action="next-change" title="다음 변경 (J)">▶</button>
                    </div>
                    <div class="nav-controls">
                        <button class="nav-btn" data-action="prev-comment" title="이전 코멘트 (P)">◀</button>
                        <span class="position-indicator comment-pos">-/{len(file_comments)}</span>
                        <button class="nav-btn" data-action="next-comment" title="다음 코멘트 (N)">▶</button>
                    </div>
                    <span class="keyboard-help"><kbd>J</kbd>/<kbd>K</kbd> 변경 <kbd>N</kbd>/<kbd>P</kbd> 코멘트</span>
                </div>
            </div>
            <div class="diff-scroll-container">
                <div class="diff-content">
                    <div class="no-diff">파일을 선택하면 diff가 표시됩니다.</div>
                </div>
            </div>
        </div>
        ''')

    return "\n".join(html_parts)


def _generate_comments_html(comments: List['ReviewComment']) -> str:
    """코멘트 목록 HTML 생성"""
    if not comments:
        return NO_COMMENTS_HTML

    html_parts = ['<ul class="comment-list">']

    for comment in comments:
        suggestion_html = ""
        if comment.suggestion:
            suggestion_html = f'<div class="comment-suggestion"><strong>제안:</strong> {html.escape(comment.suggestion)}</div>'

        comment_html = COMMENT_TEMPLATE.format(
            severity=comment.severity,
            severity_upper=comment.severity.upper(),
            file_path=html.escape(comment.file_path),
            line_number=comment.line_number,
            category=comment.category or "general",
            message=html.escape(comment.message),
            suggestion_html=suggestion_html
        )
        html_parts.append(comment_html)

    html_parts.append('</ul>')
    return "\n".join(html_parts)


def generate_html_report(
    result: 'ReviewResult',
    changelist: int,
    output_path: str
) -> None:
    """
    HTML 리포트 생성 (Side-by-side diff + AI 코멘트 인라인)

    Args:
        result: 리뷰 결과 (ReviewResult)
        changelist: Changelist 번호
        output_path: 출력 파일 경로
    """
    score = result.overall_score
    if score >= 70:
        score_class = "high"
    elif score >= 50:
        score_class = "medium"
    else:
        score_class = "low"

    # 파일 탭 HTML 생성
    file_tabs_html = _generate_file_tabs_html(result.files, result.comments)

    # 파일 diff HTML 생성
    files_diff_html = _generate_files_diff_html(result.files, result.comments)

    # 코멘트 목록 HTML 생성
    comments_html = _generate_comments_html(result.comments)

    # 전체 HTML 생성
    final_html = HTML_TEMPLATE.format(
        changelist=changelist,
        score=score,
        score_class=score_class,
        summary=html.escape(result.summary or "리뷰가 완료되었습니다."),
        critical=result.statistics.get("critical", 0),
        warning=result.statistics.get("warning", 0),
        info=result.statistics.get("info", 0),
        suggestion_count=result.statistics.get("suggestion", 0),
        file_count=len(result.files),
        comment_count=len(result.comments),
        file_tabs_html=file_tabs_html,
        files_diff_html=files_diff_html,
        comments_html=comments_html,
        diff2html_css=DIFF2HTML_CSS,
        diff2html_js=DIFF2HTML_JS
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_html)
