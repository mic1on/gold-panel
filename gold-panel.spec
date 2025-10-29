# -*- mode: python ; coding: utf-8 -*-

import os
import sys

# 获取项目根目录
project_root = os.path.dirname(os.path.abspath(SPEC))

# 添加项目根目录到路径
sys.path.insert(0, project_root)

a = Analysis(
    ['run.py'],
    pathex=[project_root],
    binaries=[],
    datas=[],
    hiddenimports=[
        'rumps',
        'httpx',
        'usepy',
        'setuptools',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='金价监控',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

# macOS 应用程序包配置
app = BUNDLE(
    exe,
    name='金价监控.app',
    icon=None,
    bundle_identifier='com.miclon.goldpanel',
    version='0.1.0',
    info_plist={
        'CFBundleName': '金价监控',
        'CFBundleDisplayName': '金价监控',
        'CFBundleVersion': '0.1.0',
        'CFBundleShortVersionString': '0.1.0',
        'CFBundleIdentifier': 'com.miclon.goldpanel',
        'LSUIElement': True,  # 不在 Dock 中显示图标
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
    },
)
