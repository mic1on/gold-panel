#!/usr/bin/env python3
"""
金价状态栏应用启动脚本
"""

import sys
import os

# 添加项目根目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
# 同时将 Resources（打包后的当前目录）和项目根目录加入路径，兼容 py2app
sys.path.insert(0, current_dir)
sys.path.insert(0, project_root)


def main_wrapper():
    """主应用包装函数"""
    # 导入并运行主应用（在函数内部导入以避免 E402 错误）
    from main import main

    return main()


if __name__ == "__main__":
    print("正在启动金价状态栏应用...")
    print("请确保您已经安装了所需的依赖包")
    print("如果遇到问题，请检查网络连接和依赖安装")
    print("-" * 50)

    try:
        main_wrapper()
    except KeyboardInterrupt:
        print("\n应用已停止")
    except Exception as e:
        print(f"启动失败: {e}")
        print("请检查依赖是否正确安装")
        sys.exit(1)
