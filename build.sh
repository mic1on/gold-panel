#!/bin/bash

# 金价监控应用 PyInstaller 构建脚本

echo "开始构建金价监控应用..."

# 检查是否安装了 pyinstaller
if ! command -v pyinstaller &> /dev/null; then
    echo "错误: 未找到 pyinstaller，请先安装："
    echo "poetry add --group dev pyinstaller"
    exit 1
fi

# 清理之前的构建文件
echo "清理之前的构建文件..."
rm -rf build/
rm -rf dist/

# 使用 PyInstaller 构建应用
echo "使用 PyInstaller 构建应用..."
poetry run pyinstaller gold-panel.spec

# 检查构建是否成功
if [ -d "dist/GoldPanel.app" ]; then
    echo "✅ 构建成功！"
    echo "应用位置: dist/GoldPanel.app"
    echo ""
    echo "可以通过以下方式运行："
    echo "1. 双击 dist/GoldPanel.app"
    echo "2. 或者在终端运行: open dist/GoldPanel.app"
    echo ""
    echo "如需分发，可以将 GoldPanel.app 复制到 /Applications 目录"
else
    echo "❌ 构建失败，请检查错误信息"
    exit 1
fi