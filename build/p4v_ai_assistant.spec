# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec 파일
P4V AI Assistant 빌드 설정
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트 경로
project_root = Path(SPECPATH).parent
src_path = project_root / 'src'

block_cipher = None

a = Analysis(
    [str(project_root / 'run.py')],  # 엔트리포인트
    pathex=[str(project_root)],
    binaries=[],
    datas=[],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.scrolledtext',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'requests',
        'src',
        'src.main',
        'src.config_manager',
        'src.p4_client',
        'src.n8n_client',
        'src.commands',
        'src.commands.description',
        'src.commands.review',
        'src.commands.install',
        'src.ui',
        'src.ui.dialogs',
        'src.ui.report_generator',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'PIL',
        'scipy',
        'cv2',
        'torch',
        'tensorflow',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='p4v_ai_assistant',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # CLI 지원을 위해 콘솔 유지
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon=str(project_root / 'build' / 'icon.ico'),  # 아이콘 (있으면)
)
