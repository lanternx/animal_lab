# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None


# 添加应用依赖
hiddenimports = [
    'werkzeug.serving',
    'sqlalchemy',
    'flask_sqlalchemy',
    'flask_cors',
    'pandas',
    'openpyxl',  # pandas Excel 导出依赖
    'engineio.async_drivers.threading',
    'webview',   # 桌面窗口库
    'threading',
    'app',       # 导入app模块
    'models'     # 导入models模块
]

# 包含数据文件
datas = [
    # 包含前端静态文件
    ('dist', 'dist'),

    # 包含app.py和models.py
    ('app.py', '.'),
    ('models.py', '.'),
]

# 主分析配置 - 使用main.py作为入口点
a = Analysis(
    ['main.py'],  # 主入口文件
    pathex=[os.getcwd()],   # 额外的搜索路径
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 创建PYZ存档
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# 可执行文件配置
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='动物房管理 V1.1',  # 输出可执行文件名称
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # 使用UPX压缩可执行文件
    runtime_tmpdir=None,
    console=False,  
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='1.ico',  # 可选的应用程序图标
)

# 收集所有文件到一个目录
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MouseManager',  # 输出目录名称
)
