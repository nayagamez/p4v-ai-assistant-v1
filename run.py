#!/usr/bin/env python
"""
P4V AI Assistant - 엔트리포인트
PyInstaller 빌드용 래퍼 스크립트
"""
import sys
import os

# PyInstaller 빌드 시 경로 설정
if getattr(sys, 'frozen', False):
    # PyInstaller로 빌드된 경우
    application_path = os.path.dirname(sys.executable)
else:
    # 일반 Python 실행
    application_path = os.path.dirname(os.path.abspath(__file__))

# src 모듈 경로 추가
sys.path.insert(0, application_path)

from src.main import main

if __name__ == '__main__':
    main()
