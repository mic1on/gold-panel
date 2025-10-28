from setuptools import setup

APP = ["run.py"]

OPTIONS = {
    "argv_emulation": False,
    "includes": [
        "rumps",
        # 强制包含 PyObjC 相关模块与旧版 stdlib 模块
        "imp",
        "objc",
        "Foundation",
        "Cocoa",
        "CoreFoundation",
        "Quartz",
    ],
    "excludes": [
        "zlib",  # 排除有问题的 zlib 模块
    ],
    "resources": [],
    "packages": [],
    # 使用 alias 模式来避免 Python 运行时问题
    "alias": True,
    "plist": {
        # 作为状态栏应用运行（不显示 Dock 图标）
        "LSUIElement": True,
        "CFBundleName": "金价监控",
        "CFBundleIdentifier": "com.miclon.gold-panel",
        "CFBundleVersion": "1.0.0",
    },
}

setup(
    app=APP,
    options={"py2app": OPTIONS},
)
