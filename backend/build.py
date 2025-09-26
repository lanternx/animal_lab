# build.py
import os
import shutil
import subprocess
import sys

def build_app():
    build_dist = "AM_V2" #路径不能有中文
    # 清理旧构建
    if os.path.exists(build_dist):
        shutil.rmtree(build_dist)
    
    # Niutka 打包配置
    command = [
        sys.executable,  # 使用当前Python解释器
        "-m", 
        "nuitka",
        "--standalone",
        "--windows-console-mode=disable",  # 禁用控制台窗口
        "--windows-icon-from-ico=1.ico",      # 应用图标
        "--enable-plugin=tk-inter",
        "--enable-plugin=pywebview",
        "--include-package=flask",
        "--include-package=flask_sqlalchemy",
        "--include-package=flask_cors",
        "--include-package=webview",
        "--include-package=sqlalchemy",
        "--include-package=pandas",
        "--include-package=openpyxl",
        "--include-data-dir=dist=dist",  # 包含前端资源
        "--output-dir="+build_dist,
        "main.py"              # 入口文件
    ]
    
    # 添加隐藏导入
    hidden_imports = [
        'sqlalchemy.ext.baked',
        'sqlalchemy.dialects.sqlite',
        'pandas._libs',
        'flask.json',
        'flask.wrappers',
        'werkzeug.wrappers',
        'werkzeug.wsgi',
        'webview'
    ]

    for imp in hidden_imports:
        command.append(f"--include-module={imp}")
    
    # 添加pywebview排除项
    command.append("--nofollow-import-to=webview.platforms.android")
    command.append("--nofollow-import-to=webview.platforms.cocoa")
    command.append("--nofollow-import-to=webview.platforms.gtk")
    command.append("--nofollow-import-to=webview.platforms.qt")

    # 执行命令
    print("执行打包命令: " + " ".join(command))
    result = subprocess.run(command, capture_output=True, text=True)
    
    # 打印输出
    print("\n标准输出:")
    print(result.stdout)
    
    if result.stderr:
        print("\n错误输出:")
        print(result.stderr)
    
    if result.returncode == 0:
        print("\n打包完成! 应用位于: " + build_dist)
    else:
        print("\n打包失败，返回码: " + str(result.returncode))

if __name__ == "__main__":
    build_app()