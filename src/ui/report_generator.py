"""
HTML 리포트 생성 모듈
코드 리뷰 결과를 HTML 형식으로 내보내기
"""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..commands.review import ReviewResult


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>코드 리뷰 - Changelist #{changelist}</title>
    <style>
        * {{
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', 'Malgun Gothic', Arial, sans-serif;
            margin: 0;
            padding: 40px;
            background: #f0f2f5;
            color: #333;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #1a1a2e;
            border-bottom: 3px solid #4a90d9;
            padding-bottom: 15px;
            margin-bottom: 10px;
        }}
        .changelist-info {{
            color: #666;
            margin-bottom: 20px;
        }}
        .score-section {{
            text-align: center;
            padding: 30px;
            background: #f8f9fa;
            border-radius: 12px;
            margin: 20px 0;
        }}
        .score {{
            font-size: 64px;
            font-weight: bold;
            margin: 0;
        }}
        .score.high {{ color: #28a745; }}
        .score.medium {{ color: #ffc107; }}
        .score.low {{ color: #dc3545; }}
        .score-label {{
            font-size: 18px;
            color: #666;
            margin-top: 5px;
        }}
        .summary {{
            background: #e8f4fd;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid #4a90d9;
            font-size: 15px;
            line-height: 1.6;
        }}
        .stats {{
            display: flex;
            gap: 15px;
            margin: 25px 0;
            flex-wrap: wrap;
        }}
        .stat {{
            flex: 1;
            min-width: 120px;
            text-align: center;
            padding: 20px 15px;
            border-radius: 10px;
        }}
        .stat-count {{
            font-size: 32px;
            font-weight: bold;
            display: block;
        }}
        .stat-label {{
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-top: 5px;
        }}
        .stat.critical {{
            background: #ffebee;
            color: #c62828;
        }}
        .stat.warning {{
            background: #fff3e0;
            color: #ef6c00;
        }}
        .stat.info {{
            background: #e3f2fd;
            color: #1565c0;
        }}
        .stat.suggestion {{
            background: #e8f5e9;
            color: #2e7d32;
        }}
        .comments-section {{
            margin-top: 30px;
        }}
        .comments-section h2 {{
            color: #1a1a2e;
            font-size: 20px;
            margin-bottom: 20px;
        }}
        .comment {{
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            margin: 15px 0;
            overflow: hidden;
            transition: box-shadow 0.2s;
        }}
        .comment:hover {{
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .comment-header {{
            padding: 12px 15px;
            background: #f8f9fa;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .comment-body {{
            padding: 15px;
        }}
        .severity {{
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 12px;
            text-transform: uppercase;
        }}
        .severity.critical {{
            background: #ffebee;
            color: #c62828;
        }}
        .severity.warning {{
            background: #fff3e0;
            color: #ef6c00;
        }}
        .severity.info {{
            background: #e3f2fd;
            color: #1565c0;
        }}
        .severity.suggestion {{
            background: #e8f5e9;
            color: #2e7d32;
        }}
        .file-info {{
            color: #555;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 13px;
        }}
        .category {{
            display: inline-block;
            background: #f0f0f0;
            color: #666;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 12px;
            margin-bottom: 10px;
        }}
        .message {{
            margin: 10px 0;
            line-height: 1.6;
        }}
        .suggestion-box {{
            background: #e8f5e9;
            padding: 12px 15px;
            margin-top: 12px;
            border-radius: 5px;
            border-left: 3px solid #4caf50;
        }}
        .suggestion-box strong {{
            color: #2e7d32;
        }}
        .no-comments {{
            text-align: center;
            padding: 40px;
            color: #666;
        }}
        .footer {{
            margin-top: 40px;
            text-align: center;
            color: #999;
            font-size: 12px;
            padding-top: 20px;
            border-top: 1px solid #eee;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>코드 리뷰 결과</h1>
        <div class="changelist-info">Changelist #{changelist}</div>

        <div class="score-section">
            <div class="score {score_class}">{score}</div>
            <div class="score-label">/ 100점</div>
        </div>

        <div class="summary">{summary}</div>

        <div class="stats">
            <div class="stat critical">
                <span class="stat-count">{critical}</span>
                <span class="stat-label">Critical</span>
            </div>
            <div class="stat warning">
                <span class="stat-count">{warning}</span>
                <span class="stat-label">Warning</span>
            </div>
            <div class="stat info">
                <span class="stat-count">{info}</span>
                <span class="stat-label">Info</span>
            </div>
            <div class="stat suggestion">
                <span class="stat-count">{suggestion_count}</span>
                <span class="stat-label">Suggestion</span>
            </div>
        </div>

        <div class="comments-section">
            <h2>상세 리뷰 ({comment_count}건)</h2>
            {comments_html}
        </div>

        <div class="footer">
            Generated by P4V AI Assistant
        </div>
    </div>
</body>
</html>"""


COMMENT_TEMPLATE = """<div class="comment">
    <div class="comment-header">
        <span class="severity {severity}">{severity_upper}</span>
        <span class="file-info">{file_path} : {line_number}</span>
    </div>
    <div class="comment-body">
        <span class="category">{category}</span>
        <div class="message">{message}</div>
        {suggestion_html}
    </div>
</div>"""


NO_COMMENTS_HTML = """<div class="no-comments">
    <p>발견된 이슈가 없습니다.</p>
</div>"""


def generate_html_report(
    result: 'ReviewResult',
    changelist: int,
    output_path: str
) -> None:
    """
    HTML 리포트 생성

    Args:
        result: 리뷰 결과
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

    # 코멘트 HTML 생성
    if result.comments:
        comments_html_parts = []
        for comment in result.comments:
            suggestion_html = ""
            if comment.suggestion:
                suggestion_html = f'<div class="suggestion-box"><strong>제안:</strong> {comment.suggestion}</div>'

            comment_html = COMMENT_TEMPLATE.format(
                severity=comment.severity,
                severity_upper=comment.severity.upper(),
                file_path=comment.file_path,
                line_number=comment.line_number,
                category=comment.category or "general",
                message=comment.message,
                suggestion_html=suggestion_html
            )
            comments_html_parts.append(comment_html)
        comments_html = "\n".join(comments_html_parts)
    else:
        comments_html = NO_COMMENTS_HTML

    # 전체 HTML 생성
    html = HTML_TEMPLATE.format(
        changelist=changelist,
        score=score,
        score_class=score_class,
        summary=result.summary or "리뷰가 완료되었습니다.",
        critical=result.statistics.get("critical", 0),
        warning=result.statistics.get("warning", 0),
        info=result.statistics.get("info", 0),
        suggestion_count=result.statistics.get("suggestion", 0),
        comment_count=len(result.comments),
        comments_html=comments_html
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
