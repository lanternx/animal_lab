import os
import shutil
import subprocess
import sys
import argparse

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='打包 macOS 应用')
    parser.add_argument('--disable-console', action='store_true', 
                        help='禁用控制台窗口（用于发布版本）')
    parser.add_argument('--create-dmg', action='store_true',
                        help='打包完成后创建 DMG 安装镜像')
    parser.add_argument('--app-name', default='MyApp',
                        help='应用名称（将用于 DMG 和 App 包命名）')
    return parser.parse_args()

def build_app(disable_console=False, app_name="MyApp"):
    """使用 Nuitka 打包应用"""
    build_dist = "build"  # 构建输出目录
    
    # 检查图标文件
    app_icon = "AppIcon.icns"
    if not os.path.exists(app_icon):
        print(f"警告: 未找到 {app_icon} 文件！应用将使用默认图标。")
    
    # 清理旧构建
    if os.path.exists(build_dist):
        print("清理旧构建文件...")
        shutil.rmtree(build_dist)
    
    # 配置隐藏导入
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

    # Nuitka 打包配置 (macOS 专用)
    command = [
        sys.executable,
        "-m", 
        "nuitka",
        "--standalone",
        "--macos-create-app-bundle",
        f"--macos-app-icon={app_icon}",
        "--enable-plugin=pywebview",
        "--include-package=flask",
        "--include-package=flask_sqlalchemy",
        "--include-package=flask_cors",
        "--include-package=webview",
        "--include-package=sqlalchemy",
        "--include-package=pandas",
        "--include-package=openpyxl",
        "--include-data-dir=dist=dist",  # 包含前端资源
        f"--output-dir={build_dist}",
        "main.py"  # 入口文件
    ]
    
    # 可选: 禁用控制台
    if disable_console:
        command.append("--disable-console")
        print("已禁用控制台窗口（发布模式）")
    else:
        print("控制台窗口已启用（调试模式）")

    non_macos_platforms = [
        "winforms", "win32", "qt", "android", "cef", "gtk",
        "edgechromium", "cocoa_webkit", "ios", "linux", "x11", "wayland", "mshtml"
    ]

    for platform in non_macos_platforms:
        command.append(f"--nofollow-import-to=webview.platforms.{platform}")

    # 添加隐藏导入
    for imp in hidden_imports:
        command.append(f"--include-module={imp}")
    
    # macOS 特定的排除项
    command.append("--nofollow-import-to=webview.platforms.winforms")
    command.append("--nofollow-import-to=webview.platforms.win32")
    command.append("--nofollow-import-to=webview.platforms.qt")
    # 保留 Cocoa (macOS 原生) 支持
    
    # 执行命令
    print("执行打包命令: " + " ".join(command))
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"\n打包命令执行失败，返回码: {e.returncode}")
        print("\n标准输出:")
        print(e.stdout)
        print("\n错误输出:")
        print(e.stderr)
        return False
    
    # 打印输出
    print("\n标准输出:")
    print(result.stdout)
    
    if result.stderr:
        print("\n错误输出:")
        print(result.stderr)
    
    if result.returncode == 0:
        print("\nNuitka 打包完成!")
        
        # 重命名应用包
        original_app_bundle = os.path.join(build_dist, "main.app")
        final_app_bundle = os.path.join(build_dist, f"{app_name}.app")
        
        if os.path.exists(original_app_bundle):
            if os.path.exists(final_app_bundle):
                shutil.rmtree(final_app_bundle)
            os.rename(original_app_bundle, final_app_bundle)
            print(f"应用包已重命名为: {final_app_bundle}")
        
        # 设置执行权限
        app_bundle = final_app_bundle
        if os.path.exists(app_bundle):
            macos_dir = os.path.join(app_bundle, "Contents", "MacOS")
            # 确保可执行文件有执行权限
            if os.path.exists(macos_dir):
                for filename in os.listdir(macos_dir):
                    file_path = os.path.join(macos_dir, filename)
                    if os.path.isfile(file_path):
                        os.chmod(file_path, 0o755)
                        print(f"已设置执行权限: {file_path}")
            
            # 重命名主可执行文件以匹配应用名
            main_executable = os.path.join(macos_dir, "main")
            new_executable = os.path.join(macos_dir, app_name)
            if os.path.exists(main_executable):
                os.rename(main_executable, new_executable)
                print(f"主可执行文件已重命名为: {new_executable}")
                
                # 更新 Info.plist 中的可执行文件名称
                info_plist_path = os.path.join(app_bundle, "Contents", "Info.plist")
                if os.path.exists(info_plist_path):
                    with open(info_plist_path, 'r') as f:
                        content = f.read()
                    content = content.replace('<string>main</string>', f'<string>{app_name}</string>')
                    with open(info_plist_path, 'w') as f:
                        f.write(content)
                    print("已更新 Info.plist 中的可执行文件名称")
        
        return True
    else:
        print("\n打包失败，返回码: " + str(result.returncode))
        return False

def create_dmg(app_name="MyApp"):
    """创建 DMG 安装镜像"""
    build_dist = "build"
    app_bundle = os.path.join(build_dist, f"{app_name}.app")
    dmg_name = f"{app_name}_Installer.dmg"
    temp_dmg_dir = "temp_dmg"
    
    if not os.path.exists(app_bundle):
        print(f"错误: 未找到应用包 {app_bundle}")
        return False
    
    print(f"\n开始创建 DMG 安装包: {dmg_name}")
    
    # 清理旧文件
    if os.path.exists(dmg_name):
        os.remove(dmg_name)
    if os.path.exists(temp_dmg_dir):
        shutil.rmtree(temp_dmg_dir)
    
    # 创建临时目录结构
    os.makedirs(temp_dmg_dir)
    
    # 将应用复制到临时目录
    shutil.copytree(app_bundle, os.path.join(temp_dmg_dir, f"{app_name}.app"))
    
    # 创建到"应用程序"文件夹的快捷方式
    os.symlink("/Applications", os.path.join(temp_dmg_dir, "Applications"))
    
    # 使用 hdiutil 创建 DMG
    try:
        # 第一步：创建可读写的 DMG
        cmd_create = [
            "hdiutil", "create",
            "-volname", app_name,
            "-srcfolder", temp_dmg_dir,
            "-ov",
            "-format", "UDRW",
            dmg_name + ".temp"
        ]
        subprocess.run(cmd_create, check=True)
        
        # 第二步：转换为压缩的只读 DMG
        cmd_convert = [
            "hdiutil", "convert",
            dmg_name + ".temp",
            "-ov",
            "-format", "UDZO",
            "-imagekey", "zlib-level=9",
            "-o", dmg_name
        ]
        subprocess.run(cmd_convert, check=True)
        
        # 清理临时文件
        os.remove(dmg_name + ".temp")
        shutil.rmtree(temp_dmg_dir)
        
        print(f"DMG 创建成功! 位于: {os.path.abspath(dmg_name)}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"创建 DMG 失败: {e}")
        # 清理临时文件
        if os.path.exists(dmg_name + ".temp"):
            os.remove(dmg_name + ".temp")
        if os.path.exists(temp_dmg_dir):
            shutil.rmtree(temp_dmg_dir)
        return False

def main():
    """主函数"""
    args = parse_arguments()
    
    print("=" * 50)
    print("开始打包 macOS 应用")
    print("=" * 50)
    
    # 打包应用
    success = build_app(
        disable_console=args.disable_console,
        app_name=args.app_name
    )
    
    # 如果打包成功且要求创建 DMG
    if success and args.create_dmg:
        print("\n" + "=" * 50)
        print("开始创建 DMG 安装镜像")
        print("=" * 50)
        create_dmg(app_name=args.app_name)
    
    print("\n" + "=" * 50)
    if success:
        print("打包流程完成!")
        build_path = os.path.abspath("build")
        print(f"应用位置: {build_path}")
        if args.create_dmg:
            dmg_path = os.path.abspath(f"{args.app_name}_Installer.dmg")
            print(f"DMG 位置: {dmg_path}")
        print("\n启动应用方法:")
        print(f"1. 双击打开: build/{args.app_name}.app")
        print(f"2. 命令行调试: ./build/{args.app_name}.app/Contents/MacOS/{args.app_name}")
    else:
        print("打包流程失败!")
    print("=" * 50)

if __name__ == "__main__":
    main()